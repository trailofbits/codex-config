"""Deterministic checks for the shipped Codex configuration."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills"
BASELINE_GLOBAL_BYTES = 10_177
MAX_SKILL_ENTRYPOINT_BYTES = 8_000


def read_text(path: Path) -> str:
    """Read a repository text file as UTF-8."""
    return path.read_text(encoding="utf-8")


def skill_files() -> list[Path]:
    """Return every checked-in direct skill entrypoint."""
    return sorted(SKILL_ROOT.glob("*/SKILL.md"))


class ConfigTests(unittest.TestCase):
    """Check public model and reasoning defaults."""

    def test_model_defaults(self) -> None:
        config = tomllib.loads(read_text(ROOT / "config.toml"))
        self.assertEqual(config["model"], "gpt-5.6-sol")
        self.assertNotIn("review_model", config)
        self.assertEqual(config["model_reasoning_effort"], "xhigh")
        self.assertEqual(config["plan_mode_reasoning_effort"], "xhigh")
        self.assertEqual(config["personality"], "pragmatic")
        self.assertEqual(config["model_reasoning_summary"], "auto")
        self.assertNotIn("model_verbosity", config)

    def test_profile_example_uses_current_cyber_alias(self) -> None:
        profile = read_text(ROOT / "profile-template.toml")
        self.assertIn('# model = "gpt-5.6-cyber"', profile)


class GlobalGuidanceTests(unittest.TestCase):
    """Keep the always-loaded prompt compact and cross-task."""

    def test_size_budget_and_reduction(self) -> None:
        size = (ROOT / "global-agents.md").stat().st_size
        self.assertLessEqual(size, 7_000)
        self.assertLessEqual(size, int(BASELINE_GLOBAL_BYTES * 0.70))

        normal_python_payload = sum(
            path.stat().st_size
            for path in (
                ROOT / "global-agents.md",
                SKILL_ROOT / "development-standards" / "SKILL.md",
                SKILL_ROOT / "development-standards" / "references" / "python.md",
            )
        )
        self.assertLessEqual(normal_python_payload, BASELINE_GLOBAL_BYTES)

    def test_language_markers_are_not_global(self) -> None:
        guidance = read_text(ROOT / "global-agents.md").lower()
        markers = (
            "pytest",
            "ruff",
            "cargo ",
            "pnpm",
            "golangci",
            "shellcheck",
            "shfmt",
            "actionlint",
            "zizmor",
            "cyclomatic",
            "100 lines",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, guidance)


class SkillTests(unittest.TestCase):
    """Check skill packaging and progressive routing."""

    def test_skill_entrypoints_and_references(self) -> None:
        self.assertGreaterEqual(len(skill_files()), 7)
        for skill_file in skill_files():
            with self.subTest(skill=skill_file.parent.name):
                text = read_text(skill_file)
                frontmatter = re.match(r"\A---\n(?P<meta>.*?)\n---\n", text, re.DOTALL)
                self.assertIsNotNone(frontmatter)
                assert frontmatter is not None
                metadata = yaml.safe_load(frontmatter["meta"])
                self.assertIsInstance(metadata, dict)
                self.assertEqual(metadata["name"], skill_file.parent.name)
                self.assertIsInstance(metadata.get("description"), str)
                self.assertLessEqual(
                    skill_file.stat().st_size, MAX_SKILL_ENTRYPOINT_BYTES
                )
                self._assert_references_are_routed(skill_file, text)

    def _assert_references_are_routed(self, skill_file: Path, text: str) -> None:
        reference_dir = skill_file.parent / "references"
        actual = set(reference_dir.glob("*.md")) if reference_dir.is_dir() else set()
        linked = {
            skill_file.parent / match
            for match in re.findall(r"\]\((references/[^)#]+\.md)\)", text)
        }
        self.assertEqual(linked, actual)
        for reference in linked:
            self.assertTrue(reference.is_file(), reference)

    def test_only_conditional_guidance_uses_references(self) -> None:
        expected = {
            "development-standards": {
                "python.md",
                "node-typescript.md",
                "rust.md",
                "go.md",
                "shell.md",
                "github-actions.md",
            },
            "fix-github-issue": set(),
            "install-codex-config": set(),
            "merge-dependabot-prs": {
                "library-evaluation.md",
                "actions-evaluation.md",
                "merge.md",
            },
            "review-and-fix-pr": set(),
            "security-research-hygiene": set(),
            "technical-writing": set(),
        }
        for skill_name, references in expected.items():
            with self.subTest(skill=skill_name):
                skill_dir = SKILL_ROOT / skill_name
                actual = {path.name for path in (skill_dir / "references").glob("*.md")}
                self.assertEqual(actual, references)
                self.assertNotIn("workflow.md", actual)

    def test_skill_interface_metadata(self) -> None:
        for skill_file in skill_files():
            with self.subTest(skill=skill_file.parent.name):
                metadata = read_text(skill_file.parent / "agents" / "openai.yaml")
                short_match = re.search(
                    r'^  short_description: "([^"]+)"$', metadata, re.MULTILINE
                )
                prompt_match = re.search(
                    r'^  default_prompt: "([^"]+)"$', metadata, re.MULTILINE
                )
                self.assertIsNotNone(short_match)
                self.assertIsNotNone(prompt_match)
                assert short_match is not None
                assert prompt_match is not None
                self.assertGreaterEqual(len(short_match.group(1)), 25)
                self.assertLessEqual(len(short_match.group(1)), 64)
                self.assertIn(f"${skill_file.parent.name}", prompt_match.group(1))

    def test_workflows_do_not_embed_language_fallback_tables(self) -> None:
        workflow_names = (
            "fix-github-issue",
            "review-and-fix-pr",
            "merge-dependabot-prs",
        )
        text = "\n".join(
            read_text(path)
            for name in workflow_names
            for path in (
                SKILL_ROOT / name / "SKILL.md",
                *(SKILL_ROOT / name / "references").glob("*.md"),
            )
        )
        forbidden = (
            "Fallback defaults",
            "full test suite",
            "| `Cargo.toml`",
            "| `pyproject.toml`",
            "| `package.json`",
            "| `go.mod`",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)


class InstallerTests(unittest.TestCase):
    """Check that installer inventory is derived from tracked source files."""

    def test_new_tracked_skill_is_discovered_without_inventory_edit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            for name in ("existing-skill", "new-skill"):
                skill_dir = source_root / ".agents" / "skills" / name
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")

            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=source_root,
                check=True,
            )
            subprocess.run(
                ["git", "add", ".agents/skills"],
                cwd=source_root,
                check=True,
            )

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--frozen",
                    "python",
                    str(ROOT / "scripts" / "list_skills.py"),
                    str(source_root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                [Path(line).parent.name for line in result.stdout.splitlines()],
                ["existing-skill", "new-skill"],
            )

    def test_installer_has_no_fixed_skill_inventory(self) -> None:
        installer = read_text(SKILL_ROOT / "install-codex-config" / "SKILL.md")
        self.assertIn("scripts/list_skills.py", installer)
        for skill_name in (
            "fix-github-issue",
            "merge-dependabot-prs",
            "technical-writing",
        ):
            self.assertNotIn(f"~/.agents/skills/{skill_name}/SKILL.md", installer)

    def test_checked_in_inventory_and_preservation_contract(self) -> None:
        result = subprocess.run(
            [
                "uv",
                "run",
                "--frozen",
                "python",
                str(ROOT / "scripts" / "list_skills.py"),
                str(ROOT),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        discovered = {Path(line).parent.name for line in result.stdout.splitlines()}
        self.assertEqual(discovered, {path.parent.name for path in skill_files()})

        installer = read_text(SKILL_ROOT / "install-codex-config" / "SKILL.md")
        self.assertIn(
            "authentication, trust, and local provider/model overrides", installer
        )
        self.assertIn("Do not delete or change target", installer)


class PythonInvocationTests(unittest.TestCase):
    """Keep repository Python execution within the uv-managed environment."""

    def test_python_helpers_use_uv_script_shebangs(self) -> None:
        for script in sorted((ROOT / "scripts").glob("*.py")):
            with self.subTest(script=script.name):
                self.assertTrue(
                    read_text(script).startswith("#!/usr/bin/env -S uv run --script\n")
                )

    def test_python_commands_use_frozen_uv_environment(self) -> None:
        paths = [ROOT / "scripts" / "check.sh", ROOT / "tests" / "test_repository.py"]
        paths.extend(SKILL_ROOT.glob("**/*.md"))
        combined = "\n".join(read_text(path) for path in paths)
        self.assertNotIn("python" + "3", combined)
        self.assertNotRegex(combined, r"(?<!uv run --frozen )\bpython\s")

    def test_pyyaml_is_locked_and_rejects_malformed_frontmatter(self) -> None:
        self.assertEqual(yaml.__version__, "6.0.3")
        with self.assertRaises(yaml.YAMLError):
            yaml.safe_load("description: 'unterminated")


class WhitespaceTests(unittest.TestCase):
    """Check unstaged, staged, and committed branch whitespace."""

    def test_all_git_states_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            self._git(repository, "init", "-q", "-b", "main")
            self._git(repository, "config", "user.name", "Codex Check")
            self._git(repository, "config", "user.email", "codex@example.invalid")
            tracked = repository / "tracked.txt"
            tracked.write_text("clean\n", encoding="utf-8")
            self._git(repository, "add", "tracked.txt")
            self._git(repository, "commit", "-q", "-m", "baseline")
            self._git(repository, "switch", "-q", "-c", "feature")

            tracked.write_text("unstaged trailing space \n", encoding="utf-8")
            self._assert_whitespace_failure(repository)

            self._git(repository, "add", "tracked.txt")
            self._assert_whitespace_failure(repository)

            self._git(repository, "commit", "-q", "-m", "bad whitespace")
            self._assert_whitespace_failure(repository)

    def _assert_whitespace_failure(self, repository: Path) -> None:
        environment = {
            **os.environ,
            "CHECK_REPO_ROOT": str(repository),
            "CHECK_BASE_REF": "main",
        }
        result = subprocess.run(
            [str(ROOT / "scripts" / "check_whitespace.sh")],
            cwd=repository,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trailing whitespace", result.stdout + result.stderr)

    @staticmethod
    def _git(repository: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )


class DocumentationTests(unittest.TestCase):
    """Reject stale active model guidance while allowing eval history."""

    def test_obsolete_model_ids_are_absent(self) -> None:
        text_paths = [
            ROOT / "README.md",
            ROOT / "config.toml",
            ROOT / "global-agents.md",
            ROOT / "profile-template.toml",
        ]
        text_paths.extend(SKILL_ROOT.glob("**/*.md"))
        combined = "\n".join(read_text(path) for path in text_paths)
        self.assertNotIn("gpt-5.5-cyber-preview", combined)
        self.assertNotIn("gpt-5.4-cyber", combined)
        self.assertNotIn("gpt-5.5", combined)

    def test_readme_describes_ignore_flags_narrowly(self) -> None:
        readme = read_text(ROOT / "README.md")
        self.assertIn("skips `$CODEX_HOME/config.toml`", readme)
        self.assertIn("skips user and project exec-policy `.rules` files", readme)
        self.assertNotIn("shrink the hidden harness context", readme)

    def test_eval_matrix_marks_gpt_5_5_as_historical(self) -> None:
        matrix = tomllib.loads(read_text(ROOT / "evals" / "matrix.toml"))
        configurations = matrix["configuration"]
        self.assertEqual(len(configurations), 4)
        historical = [item for item in configurations if item["model"] == "gpt-5.5"]
        self.assertEqual(len(historical), 1)
        self.assertTrue(historical[0]["historical_baseline"])
        self.assertEqual(
            [item["source"] for item in configurations].count("candidate"), 1
        )
        candidate = next(
            item for item in configurations if item["source"] == "candidate"
        )
        self.assertEqual(candidate["reasoning_effort"], "xhigh")
        self.assertEqual(
            [item["dimension"] for item in matrix["comparison"]],
            ["model", "reasoning_effort", "prompt"],
        )

    def test_eval_runner_retains_only_sanitized_root_results(self) -> None:
        ignore = read_text(ROOT / "evals" / ".gitignore")
        self.assertIn("results/*/", ignore)
        self.assertIn("results/*.sh", ignore)
        self.assertNotIn("results/\n", ignore)
        runner = read_text(ROOT / "evals" / "evaluate.py")
        self.assertIn("OPENAI_API_KEY", runner)
        self.assertIn("CODEX_ACCESS_TOKEN", runner)
        self.assertIn("assert_secret_absent", runner)

    def test_eval_trace_detects_references_read_from_skill_directory(self) -> None:
        sys.path.insert(0, str(ROOT / "evals"))
        try:
            from grade import parse_trace
        finally:
            sys.path.pop(0)

        event = {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": "sed -n '1,320p' python.md && sed -n '1,320p' github-actions.md",
                "aggregated_output": "",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            trace.write_text(f"{json.dumps(event)}\n", encoding="utf-8")
            evidence = parse_trace(trace)

        self.assertEqual(evidence.loaded_references, ("github-actions.md", "python.md"))

    def test_eval_cases_reference_existing_fixtures(self) -> None:
        cases = sorted((ROOT / "evals" / "cases").glob("*.md"))
        self.assertEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case=case.name):
                match = re.search(r"`evals/fixtures/([^/]+)/`", read_text(case))
                self.assertIsNotNone(match)
                assert match is not None
                self.assertTrue((ROOT / "evals" / "fixtures" / match.group(1)).is_dir())


if __name__ == "__main__":
    unittest.main()
