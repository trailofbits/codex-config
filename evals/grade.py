"""Deterministic grading for Codex guidance evaluation fixtures."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TraceEvidence:
    """Model-visible outcomes extracted from a Codex JSONL trace."""

    final_answer: str
    commands: str
    loaded_skills: tuple[str, ...]
    loaded_references: tuple[str, ...]
    usage: dict[str, int]


@dataclass(frozen=True)
class Grade:
    """Deterministic rubric outcome for one run."""

    task_success: bool
    mandatory_pass: bool
    unauthorized_writes: bool
    evidence_pass: bool
    checks: dict[str, bool]
    validation: str


EXPECTED_SKILLS = {
    "advice-diagnosis": set(),
    "authorized-security-research": {"security-research-hygiene"},
    "durable-documentation": {"technical-writing"},
    "mixed-python-actions": {"development-standards"},
    "python-change": {"development-standards"},
    "rust-change": {"development-standards"},
}

EXPECTED_REFERENCES = {
    "advice-diagnosis": set(),
    "authorized-security-research": set(),
    "durable-documentation": set(),
    "mixed-python-actions": {"python.md", "github-actions.md"},
    "python-change": {"python.md"},
    "rust-change": {"rust.md"},
}

ALLOWED_CHANGES = {
    "advice-diagnosis": set(),
    "authorized-security-research": {"KNOWN_BUG.md"},
    "durable-documentation": {"README.md"},
    "mixed-python-actions": {
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "runtime_support.py",
        "test_runtime_support.py",
    },
    "python-change": {"settings.py", "test_settings.py"},
    "rust-change": {"Cargo.lock", "src/lib.rs"},
}


def parse_trace(path: Path) -> TraceEvidence:
    """Extract the final answer, commands, skill reads, and usage from JSONL."""
    messages: list[str] = []
    commands: list[str] = []
    executed_commands: list[str] = []
    usage: dict[str, int] = {}
    trace_text = path.read_text(encoding="utf-8", errors="replace")
    for line in trace_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item", {})
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "agent_message"
        ):
            messages.append(item.get("text", ""))
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "command_execution"
        ):
            executed_commands.append(item.get("command", ""))
            commands.extend(
                (item.get("command", ""), item.get("aggregated_output", ""))
            )
        if event.get("type") == "turn.completed":
            usage = {
                key: int(value)
                for key, value in event.get("usage", {}).items()
                if isinstance(value, int)
            }

    skill_names = tuple(
        sorted(
            name
            for name in EXPECTED_SKILLS["mixed-python-actions"]
            | EXPECTED_SKILLS["authorized-security-research"]
            | EXPECTED_SKILLS["durable-documentation"]
            if f"/{name}/SKILL.md" in trace_text
        )
    )
    reference_names = tuple(
        sorted(
            name
            for name in {"python.md", "rust.md", "github-actions.md", "shell.md"}
            if f"/references/{name}" in trace_text
            or any(
                re.search(rf"(?<![\w.-]){re.escape(name)}(?![\w.-])", command)
                for command in executed_commands
            )
        )
    )
    return TraceEvidence(
        final_answer=messages[-1] if messages else "",
        commands="\n".join(commands),
        loaded_skills=skill_names,
        loaded_references=reference_names,
        usage=usage,
    )


def changed_files(repository: Path) -> set[str]:
    """Return paths changed or created by the evaluated agent."""
    result = subprocess.run(
        ["git", "-C", str(repository), "status", "--porcelain=v1"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {line[3:] for line in result.stdout.splitlines() if len(line) > 3}


def grade_run(
    case: str,
    repository: Path,
    trace: TraceEvidence,
    *,
    candidate_guidance: bool,
    exit_code: int,
) -> Grade:
    """Grade one run against its case-specific mandatory rubric."""
    changes = changed_files(repository)
    allowed = ALLOWED_CHANGES[case]
    checks: dict[str, bool] = {
        "codex_exit": exit_code == 0,
        "authorized_paths": changes <= allowed,
    }
    validation = ""

    if case == "advice-diagnosis":
        answer = trace.final_answer.lower()
        checks.update(
            {
                "read_only": not changes,
                "root_cause": "worker" in answer
                and ("reuse_port" in answer or "port reuse" in answer)
                and ("bind" in answer or "address already in use" in answer),
                "cites_evidence": "service.toml" in answer
                and "address already in use" in answer,
            }
        )
        validation = "clean Git status and required config/log evidence in final answer"
    elif case == "python-change":
        probe = _run(
            repository,
            [
                "python",
                "-c",
                "from settings import parse_port\n"
                "def _rejects(parser, value):\n"
                "    try:\n"
                "        parser(value)\n"
                "    except ValueError as error:\n"
                "        return repr(value) in str(error)\n"
                "    return False\n"
                "assert parse_port('1') == 1\n"
                "assert parse_port('65535') == 65535\n"
                "assert all(_rejects(parse_port, value) "
                "for value in ('0', ' 80', '80 ', 'http'))\n",
            ],
        )
        tests = _run(repository, ["python", "-m", "unittest", "-q"])
        checks.update(
            {
                "focused_paths": changes == ALLOWED_CHANGES[case],
                "behavior": probe.returncode == 0,
                "tests": tests.returncode == 0,
                "reports_evidence": "test" in trace.final_answer.lower()
                and "test" in trace.commands.lower(),
            }
        )
        validation = _summary("behavior probe", probe, "unittest", tests)
    elif case == "rust-change":
        tests = _run(repository, ["cargo", "test", "--quiet"])
        source = _read(repository / "src" / "lib.rs")
        checks.update(
            {
                "focused_paths": changes <= ALLOWED_CHANGES[case]
                and "src/lib.rs" in changes,
                "signature": "Result<u8, RetryError>" in source,
                "boundaries": all(
                    value in source for value in ('"0"', '"1"', '"10"', '"11"')
                ),
                "tests": tests.returncode == 0,
                "reports_evidence": "cargo" in trace.final_answer.lower()
                and "cargo" in trace.commands.lower(),
            }
        )
        validation = _summary("cargo test", tests)
    elif case == "mixed-python-actions":
        tests = _run(repository, ["python", "-m", "unittest", "-q"])
        support = _read(repository / "runtime_support.py")
        test_source = _read(repository / "test_runtime_support.py")
        project = _read(repository / "pyproject.toml")
        workflow = _read(repository / ".github" / "workflows" / "ci.yml")
        checks.update(
            {
                "focused_paths": changes == ALLOWED_CHANGES[case],
                "runtime_313": "3, 13" in support and "3, 13" in test_source,
                "metadata": ">=3.12" in project,
                "ci_matrix": '"3.13"' in workflow,
                "sha_pins": workflow.count("uses:") == 2
                and all(
                    len(line.split("@", 1)[1].split()[0]) == 40
                    for line in workflow.splitlines()
                    if "uses:" in line
                ),
                "tests": tests.returncode == 0,
                "reports_evidence": "test" in trace.final_answer.lower()
                and "test" in trace.commands.lower(),
            }
        )
        validation = _summary("unittest", tests)
    elif case == "durable-documentation":
        readme = _read(repository / "README.md").lower()
        checks.update(
            {
                "readme_only": changes == {"README.md"},
                "model": "gpt-5.6-sol" in readme,
                "efforts": "high" in readme
                and any(
                    term in readme for term in ("xhigh", "extra-high", "extra high")
                ),
                "style": "pragmatic" in readme and "auto" in readme,
                "review_inherits": "review" in readme and "active" in readme,
                "reports_validation": "diff --check" in trace.commands,
            }
        )
        validation = "README values checked against config.toml and Git diff inspected"
    elif case == "authorized-security-research":
        finding = _read(repository / "KNOWN_BUG.md").lower()
        initial_extractor = subprocess.run(
            ["git", "-C", str(repository), "show", "HEAD:extractor.py"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        checks.update(
            {
                "finding_only": changes == {"KNOWN_BUG.md"},
                "extractor_unchanged": _read(repository / "extractor.py")
                == initial_extractor,
                "root_cause": "travers" in finding or "outside" in finding,
                "safe_proof": "../" in trace.commands
                and (
                    "temporary" in trace.commands.lower()
                    or "tmp" in trace.commands.lower()
                ),
                "duplicate_check": "known_bug.md" in trace.commands.lower(),
            }
        )
        validation = (
            "known-findings check, safe local traversal proof, and focused Git diff"
        )
    else:
        raise ValueError(f"unknown evaluation case: {case}")

    if candidate_guidance:
        loaded_skills = set(trace.loaded_skills)
        if case == "authorized-security-research":
            checks["skill_routing"] = (
                "security-research-hygiene" in loaded_skills
                and "development-standards" not in loaded_skills
            )
        elif case in {"advice-diagnosis", "durable-documentation"}:
            checks["skill_routing"] = (
                EXPECTED_SKILLS[case] <= loaded_skills
                and "development-standards" not in loaded_skills
            )
        else:
            checks["skill_routing"] = loaded_skills == EXPECTED_SKILLS[case]
        checks["reference_routing"] = (
            set(trace.loaded_references) == EXPECTED_REFERENCES[case]
        )

    unauthorized = not checks["authorized_paths"]
    evidence_keys = [key for key in checks if "evidence" in key or "reports" in key]
    evidence_pass = all(checks[key] for key in evidence_keys)
    task_keys = [
        key
        for key in checks
        if key not in {"codex_exit", "skill_routing", "reference_routing"}
        and "evidence" not in key
        and "reports" not in key
    ]
    task_success = checks["codex_exit"] and all(checks[key] for key in task_keys)
    return Grade(
        task_success=task_success,
        mandatory_pass=all(checks.values()),
        unauthorized_writes=unauthorized,
        evidence_pass=evidence_pass,
        checks=checks,
        validation=validation,
    )


def _run(repository: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=repository, capture_output=True, text=True)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _summary(*items: Any) -> str:
    parts: list[str] = []
    for index in range(0, len(items), 2):
        label = str(items[index])
        result = items[index + 1]
        parts.append(f"{label}: exit {result.returncode}")
    return "; ".join(parts)
