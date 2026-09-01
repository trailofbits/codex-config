#!/usr/bin/env python
"""Run isolated comparative Codex model and guidance evaluations."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

from grade import Grade, grade_run, parse_trace


ROOT = Path(__file__).resolve().parents[1]
HIGH_RISK_CASES = {"authorized-security-research", "mixed-python-actions"}


@dataclass(frozen=True)
class Configuration:
    """One row in the model, effort, and prompt comparison matrix."""

    id: str
    model: str
    reasoning_effort: str
    source: str
    historical_baseline: bool


@dataclass(frozen=True)
class Task:
    """One isolated configuration, case, and repeat."""

    configuration: Configuration
    case: str
    run: int


@dataclass
class RunRecord:
    """Sanitized result fields retained for one model-backed run."""

    configuration: str
    case: str
    run: int
    status: str
    task_success: bool
    mandatory_pass: bool
    evidence_pass: bool
    unauthorized_writes: bool
    exit_code: int
    latency_seconds: float
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    reasoning_output_tokens: int | None
    loaded_skills: str
    loaded_references: str
    validation: str
    failed_checks: str


def parse_arguments() -> argparse.Namespace:
    """Parse the evaluation command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run the comparative evaluation matrix")
    run.add_argument("--baseline-ref", required=True)
    run.add_argument("--candidate-ref", required=True)
    run.add_argument("--runs", type=int, default=1)
    run.add_argument("--jobs", type=int, default=4)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--output-dir", type=Path, default=ROOT / "evals" / "results")
    return parser.parse_args()


def main() -> int:
    """Run the requested command and return a process exit status."""
    arguments = parse_arguments()
    if arguments.runs < 1 or arguments.jobs < 1:
        raise SystemExit("--runs and --jobs must be positive integers")

    baseline_ref = resolve_ref(arguments.baseline_ref)
    candidate_ref = resolve_ref(arguments.candidate_ref)
    with tempfile.TemporaryDirectory(prefix="codex-config-eval-") as directory:
        temp_root = Path(directory)
        baseline = export_ref(baseline_ref, temp_root / "baseline")
        candidate = export_ref(candidate_ref, temp_root / "candidate")
        configurations, comparisons = load_matrix(ROOT / "evals" / "matrix.toml")
        cases = sorted(path.stem for path in (ROOT / "evals" / "cases").glob("*.md"))
        tasks = build_tasks(configurations, cases, arguments.runs)

        if arguments.dry_run:
            print_plan(tasks, baseline_ref, candidate_ref)
            return 0

        credential_name, credential = read_credential()
        codex = shutil.which("codex")
        if codex is None:
            raise SystemExit("codex executable not found on PATH")

        output_dir = arguments.output_dir.resolve()
        raw_dir = output_dir / "raw" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        raw_dir.mkdir(parents=True, exist_ok=False)
        source_roots = {"baseline": baseline, "candidate": candidate}
        records = run_tasks(
            tasks,
            source_roots=source_roots,
            evaluation_root=ROOT,
            temp_root=temp_root,
            raw_dir=raw_dir,
            codex=codex,
            credential_name=credential_name,
            credential=credential,
            jobs=arguments.jobs,
        )

        retries = retry_tasks(records, configurations)
        if retries:
            print(f"Repeating {len(retries)} failed or borderline runs twice.")
            records.extend(
                run_tasks(
                    retries,
                    source_roots=source_roots,
                    evaluation_root=ROOT,
                    temp_root=temp_root,
                    raw_dir=raw_dir,
                    codex=codex,
                    credential_name=credential_name,
                    credential=credential,
                    jobs=arguments.jobs,
                )
            )

        records.sort(key=lambda item: (item.configuration, item.case, item.run))
        summary = build_summary(
            records,
            configurations,
            comparisons,
            baseline_ref=baseline_ref,
            candidate_ref=candidate_ref,
            codex_version=command_output([codex, "--version"]).strip(),
        )
        write_results(output_dir, records, summary)
        print(
            f"Wrote {len(records)} sanitized run rows and {len(comparisons)} pairwise "
            f"comparisons to {output_dir}"
        )
        print(f"Evaluation gate: {summary['gate']['status']}")
        return 0 if summary["gate"]["status"] == "pass" else 1


def resolve_ref(reference: str) -> str:
    """Resolve a Git reference to a full commit hash."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", f"{reference}^{{commit}}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def export_ref(reference: str, destination: Path) -> Path:
    """Export a committed repository tree without carrying local state."""
    archive = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=tar", reference],
        check=True,
        capture_output=True,
    ).stdout
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        tar.extractall(destination, filter="data")
    return destination


def load_matrix(path: Path) -> tuple[list[Configuration], list[dict[str, str]]]:
    """Load configurations and explicit pairwise comparisons."""
    matrix = tomllib.loads(path.read_text(encoding="utf-8"))
    configurations = [Configuration(**item) for item in matrix["configuration"]]
    return configurations, matrix["comparison"]


def build_tasks(
    configurations: list[Configuration], cases: list[str], requested_runs: int
) -> list[Task]:
    """Build the 24 base runs plus high-risk repeats."""
    tasks: list[Task] = []
    for configuration in configurations:
        for case in cases:
            total = max(
                requested_runs, 3 if case in HIGH_RISK_CASES else requested_runs
            )
            tasks.extend(Task(configuration, case, run) for run in range(1, total + 1))
    return tasks


def print_plan(tasks: list[Task], baseline_ref: str, candidate_ref: str) -> None:
    """Print a credential-free execution plan."""
    print(f"baseline={baseline_ref}")
    print(f"candidate={candidate_ref}")
    print(f"runs={len(tasks)}")
    for task in tasks:
        print(f"{task.configuration.id},{task.case},{task.run}")


def read_credential() -> tuple[str, str]:
    """Read one supported credential from the environment without logging it."""
    for name in ("OPENAI_API_KEY", "CODEX_ACCESS_TOKEN"):
        value = os.environ.get(name)
        if value:
            return name, value
    raise SystemExit(
        "Set OPENAI_API_KEY or CODEX_ACCESS_TOKEN in the environment before running evals."
    )


def run_tasks(
    tasks: list[Task],
    *,
    source_roots: dict[str, Path],
    evaluation_root: Path,
    temp_root: Path,
    raw_dir: Path,
    codex: str,
    credential_name: str,
    credential: str,
    jobs: int,
) -> list[RunRecord]:
    """Run independent eval tasks concurrently and return sanitized records."""
    records: list[RunRecord] = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(
                run_task,
                task,
                source_root=source_roots[task.configuration.source],
                evaluation_root=evaluation_root,
                temp_root=temp_root,
                raw_dir=raw_dir,
                codex=codex,
                credential_name=credential_name,
                credential=credential,
            ): task
            for task in tasks
        }
        for future in as_completed(futures):
            task = futures[future]
            record = future.result()
            records.append(record)
            print(
                f"{task.configuration.id}/{task.case}/run-{task.run}: "
                f"{record.status}, mandatory={'pass' if record.mandatory_pass else 'fail'}"
            )
    return records


def run_task(
    task: Task,
    *,
    source_root: Path,
    evaluation_root: Path,
    temp_root: Path,
    raw_dir: Path,
    codex: str,
    credential_name: str,
    credential: str,
) -> RunRecord:
    """Prepare, execute, and grade one isolated Codex run."""
    task_name = f"{task.configuration.id}-{task.case}-{task.run}"
    task_root = temp_root / "runs" / task_name
    home = task_root / "home"
    repository = task_root / "repository"
    prepare_home(home, source_root)
    prepare_repository(repository, evaluation_root / "evals" / "fixtures" / task.case)
    authenticate(home, codex, credential_name, credential)

    result_dir = raw_dir / task.configuration.id
    result_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{task.case}-run-{task.run}"
    trace_path = result_dir / f"{stem}.jsonl"
    stderr_path = result_dir / f"{stem}.stderr"
    final_path = result_dir / f"{stem}.final.md"
    prompt = extract_prompt(evaluation_root / "evals" / "cases" / f"{task.case}.md")
    environment = isolated_environment(home, credential_name)
    command = [
        codex,
        "exec",
        "--strict-config",
        "--json",
        "--ephemeral",
        "--dangerously-bypass-hook-trust",
        "--color",
        "never",
        "--model",
        task.configuration.model,
        "--sandbox",
        "workspace-write",
        "--cd",
        str(repository),
        "--output-last-message",
        str(final_path),
        "-c",
        f'model_reasoning_effort="{task.configuration.reasoning_effort}"',
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "-c",
        "features.multi_agent=false",
        "-",
    ]

    started = time.monotonic()
    with (
        trace_path.open("w", encoding="utf-8") as trace_file,
        stderr_path.open("w", encoding="utf-8") as stderr_file,
    ):
        completed = subprocess.run(
            command,
            input=prompt,
            stdout=trace_file,
            stderr=stderr_file,
            text=True,
            env=environment,
        )
    latency = time.monotonic() - started
    assert_secret_absent((trace_path, stderr_path, final_path), credential)
    write_raw_git_evidence(repository, result_dir, stem)
    trace = parse_trace(trace_path)
    status = classify_status(completed.returncode, stderr_path)
    if status == "unavailable":
        grade = unavailable_grade()
    else:
        grade = grade_run(
            task.case,
            repository,
            trace,
            candidate_guidance=task.configuration.source == "candidate",
            exit_code=completed.returncode,
        )
    return record_from_grade(task, status, completed.returncode, latency, trace, grade)


def prepare_home(home: Path, source_root: Path) -> None:
    """Create a synthetic HOME containing only the selected committed config."""
    codex_home = home / ".codex"
    codex_home.mkdir(parents=True)
    config = (source_root / "config.toml").read_text(encoding="utf-8")
    config = config.replace(
        'cli_auth_credentials_store = "keyring"', 'cli_auth_credentials_store = "file"'
    )
    (codex_home / "config.toml").write_text(config, encoding="utf-8")
    shutil.copy2(source_root / "global-agents.md", codex_home / "AGENTS.md")
    for name in ("hooks", "rules"):
        if (source_root / name).is_dir():
            shutil.copytree(source_root / name, codex_home / name)
    skills = source_root / ".agents" / "skills"
    if skills.is_dir():
        shutil.copytree(skills, home / ".agents" / "skills")


def prepare_repository(repository: Path, fixture: Path) -> None:
    """Copy and commit one fixture as an independent Git repository."""
    shutil.copytree(fixture, repository)
    run_checked(["git", "init", "-q", "-b", "main"], cwd=repository)
    run_checked(["git", "add", "."], cwd=repository)
    run_checked(
        [
            "git",
            "-c",
            "user.name=Codex Eval",
            "-c",
            "user.email=codex-eval@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "-m",
            "Seed evaluation fixture",
        ],
        cwd=repository,
    )


def authenticate(home: Path, codex: str, credential_name: str, credential: str) -> None:
    """Authenticate the temporary home from one environment credential."""
    option = (
        "--with-api-key"
        if credential_name == "OPENAI_API_KEY"
        else "--with-access-token"
    )
    environment = isolated_environment(home, keep_credential=credential_name)
    environment[credential_name] = credential
    completed = subprocess.run(
        [codex, "login", option],
        input=credential,
        capture_output=True,
        text=True,
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError("Codex login failed for an isolated evaluation home")


def isolated_environment(home: Path, keep_credential: str) -> dict[str, str]:
    """Build an environment that excludes credentials from model-run commands."""
    environment = dict(os.environ)
    for name in ("OPENAI_API_KEY", "CODEX_ACCESS_TOKEN"):
        environment.pop(name, None)
    environment.update({"HOME": str(home), "CODEX_HOME": str(home / ".codex")})
    if keep_credential not in {"OPENAI_API_KEY", "CODEX_ACCESS_TOKEN"}:
        raise ValueError(f"unsupported credential variable: {keep_credential}")
    return environment


def extract_prompt(path: Path) -> str:
    """Extract the Prompt section from one Markdown case."""
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^## Prompt\n\n(?P<prompt>.*?)(?=\n## Mandatory rubric\n)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if match is None:
        raise ValueError(f"case has no Prompt section: {path}")
    return match.group("prompt").strip() + "\n"


def assert_secret_absent(paths: tuple[Path, ...], credential: str) -> None:
    """Fail and redact if a subprocess unexpectedly logs its credential."""
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if credential in text:
            path.write_text(text.replace(credential, "[REDACTED]"), encoding="utf-8")
            raise RuntimeError(f"credential appeared in evaluation output: {path.name}")


def write_raw_git_evidence(repository: Path, result_dir: Path, stem: str) -> None:
    """Retain ignored diffs and status for manual trace review."""
    (result_dir / f"{stem}.diff").write_text(
        command_output(["git", "-C", str(repository), "diff", "--binary"]),
        encoding="utf-8",
    )
    (result_dir / f"{stem}.status").write_text(
        command_output(["git", "-C", str(repository), "status", "--short"]),
        encoding="utf-8",
    )


def classify_status(exit_code: int, stderr_path: Path) -> str:
    """Distinguish unavailable models from other execution failures."""
    if exit_code == 0:
        return "completed"
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace").lower()
    unavailable_markers = (
        "model_not_found",
        "model is not available",
        "unsupported model",
    )
    return (
        "unavailable"
        if any(marker in stderr for marker in unavailable_markers)
        else "error"
    )


def unavailable_grade() -> Grade:
    """Return a non-passing grade without pretending another model ran."""
    return Grade(
        False, False, False, False, {"model_available": False}, "model unavailable"
    )


def record_from_grade(
    task: Task,
    status: str,
    exit_code: int,
    latency: float,
    trace: Any,
    grade: Grade,
) -> RunRecord:
    """Convert internal evidence to a sanitized checked-in row."""
    usage = trace.usage
    failed = sorted(name for name, passed in grade.checks.items() if not passed)
    return RunRecord(
        configuration=task.configuration.id,
        case=task.case,
        run=task.run,
        status=status,
        task_success=grade.task_success,
        mandatory_pass=grade.mandatory_pass,
        evidence_pass=grade.evidence_pass,
        unauthorized_writes=grade.unauthorized_writes,
        exit_code=exit_code,
        latency_seconds=round(latency, 3),
        input_tokens=usage.get("input_tokens"),
        cached_input_tokens=usage.get("cached_input_tokens"),
        output_tokens=usage.get("output_tokens"),
        reasoning_output_tokens=usage.get("reasoning_output_tokens"),
        loaded_skills=";".join(trace.loaded_skills),
        loaded_references=";".join(trace.loaded_references),
        validation=grade.validation,
        failed_checks=";".join(failed),
    )


def retry_tasks(
    records: list[RunRecord], configurations: list[Configuration]
) -> list[Task]:
    """Repeat non-high-risk failures twice, without retrying unavailable models."""
    by_id = {configuration.id: configuration for configuration in configurations}
    retries: list[Task] = []
    for record in records:
        if (
            record.run == 1
            and record.case not in HIGH_RISK_CASES
            and record.status != "unavailable"
            and not record.mandatory_pass
        ):
            retries.extend(
                Task(by_id[record.configuration], record.case, run) for run in (2, 3)
            )
    return retries


def build_summary(
    records: list[RunRecord],
    configurations: list[Configuration],
    comparisons: list[dict[str, str]],
    *,
    baseline_ref: str,
    candidate_ref: str,
    codex_version: str,
) -> dict[str, Any]:
    """Build sanitized aggregate and pairwise results."""
    aggregate = {
        configuration.id: aggregate_configuration(records, configuration.id)
        for configuration in configurations
    }
    pairwise = [compare(records, item) for item in comparisons]
    candidate_configuration = next(
        item for item in configurations if item.source == "candidate"
    )
    candidate_id = candidate_configuration.id
    candidate_records = [item for item in records if item.configuration == candidate_id]
    gate_reasons: list[str] = []
    if any(item.status != "completed" for item in records):
        gate_reasons.append(
            "one or more requested model runs were unavailable or errored"
        )
    if any(not item.mandatory_pass for item in candidate_records):
        gate_reasons.append("candidate guidance failed a mandatory rubric")
    if any(item.unauthorized_writes for item in records):
        gate_reasons.append("an evaluation made an unauthorized fixture write")
    decision_comparisons = [
        item for item in pairwise if item["dimension"] != "reasoning_effort"
    ]
    if any(item["status"] == "regression" for item in decision_comparisons):
        gate_reasons.append("a pairwise comparison regressed")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "baseline_ref": baseline_ref,
        "candidate_ref": candidate_ref,
        "codex_version": codex_version,
        "run_count": len(records),
        "high_risk_cases": sorted(HIGH_RISK_CASES),
        "aggregate": aggregate,
        "pairwise": pairwise,
        "gate": {
            "status": "pass" if not gate_reasons else "fail",
            "selected_normal_reasoning_effort": candidate_configuration.reasoning_effort,
            "selection_basis": "candidate configuration after comparative evaluation",
            "reasons": gate_reasons,
        },
    }


def aggregate_configuration(
    records: list[RunRecord], configuration: str
) -> dict[str, Any]:
    """Aggregate pass rates and token or latency medians for one configuration."""
    selected = [item for item in records if item.configuration == configuration]
    completed = [item for item in selected if item.status == "completed"]
    return {
        "requested_runs": len(selected),
        "completed_runs": len(completed),
        "task_success_rate": rate(completed, "task_success"),
        "mandatory_pass_rate": rate(completed, "mandatory_pass"),
        "evidence_pass_rate": rate(completed, "evidence_pass"),
        "unauthorized_writes": sum(item.unauthorized_writes for item in selected),
        "median_latency_seconds": median_or_none(
            [item.latency_seconds for item in completed]
        ),
        "median_input_tokens": median_or_none(
            [item.input_tokens for item in completed if item.input_tokens is not None]
        ),
        "median_output_tokens": median_or_none(
            [item.output_tokens for item in completed if item.output_tokens is not None]
        ),
    }


def compare(records: list[RunRecord], comparison: dict[str, str]) -> dict[str, Any]:
    """Compare task, evidence, and rubric pass rates case by case."""
    before = [item for item in records if item.configuration == comparison["baseline"]]
    after = [item for item in records if item.configuration == comparison["candidate"]]
    if any(item.status != "completed" for item in before + after):
        status = "unavailable"
        regressions = ["one or more compared runs did not complete"]
    else:
        regressions = []
        cases = sorted({item.case for item in before + after})
        for case in cases:
            before_case = [item for item in before if item.case == case]
            after_case = [item for item in after if item.case == case]
            for field in ("task_success", "mandatory_pass", "evidence_pass"):
                if rate(after_case, field) < rate(before_case, field):
                    regressions.append(f"{case}:{field}")
            if any(item.unauthorized_writes for item in after_case):
                regressions.append(f"{case}:unauthorized_writes")
        status = "regression" if regressions else "pass"
    return {
        "id": comparison["id"],
        "dimension": comparison["dimension"],
        "baseline": comparison["baseline"],
        "candidate": comparison["candidate"],
        "status": status,
        "regressions": regressions,
    }


def rate(records: list[RunRecord], field: str) -> float:
    """Return the proportion of records with a true Boolean field."""
    return (
        round(sum(bool(getattr(item, field)) for item in records) / len(records), 4)
        if records
        else 0.0
    )


def median_or_none(values: list[float | int]) -> float | None:
    """Return a rounded median when values are available."""
    return round(float(median(values)), 3) if values else None


def write_results(
    output_dir: Path, records: list[RunRecord], summary: dict[str, Any]
) -> None:
    """Write reviewable sanitized CSV and JSON results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(records[0])) if records else list(RunRecord.__annotations__)
    with (output_dir / "runs.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    pairwise_fields = (
        "id",
        "dimension",
        "baseline",
        "candidate",
        "status",
        "regressions",
    )
    with (output_dir / "pairwise.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=pairwise_fields, lineterminator="\n")
        writer.writeheader()
        for item in summary["pairwise"]:
            row = dict(item)
            row["regressions"] = ";".join(row["regressions"])
            writer.writerow(row)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_checked(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def command_output(command: list[str]) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


if __name__ == "__main__":
    raise SystemExit(main())
