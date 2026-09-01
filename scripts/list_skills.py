#!/usr/bin/env -S uv run --script
"""List checked-in Codex skill entrypoints for the installer."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class SkillDiscoveryError(RuntimeError):
    """Raised when the checked-in skill inventory cannot be read."""


def run_git(source_root: Path, *arguments: str) -> bytes:
    """Run a read-only Git query for the source checkout."""
    try:
        result = subprocess.run(
            ["git", "-C", source_root, *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        message = "git is required to discover checked-in skills"
        raise SkillDiscoveryError(message) from error
    except subprocess.CalledProcessError as error:
        detail = os.fsdecode(error.stderr).strip()
        message = f"cannot read checked-in skills from {source_root}"
        if detail:
            message = f"{message}: {detail}"
        raise SkillDiscoveryError(message) from error

    return result.stdout


def discover_skill_files(source_root: Path) -> list[Path]:
    """Return every direct checked-in skill entrypoint below source_root.

    Args:
        source_root: Root of the codex-config checkout.

    Returns:
        Sorted absolute paths to `.agents/skills/*/SKILL.md` files.

    Raises:
        FileNotFoundError: If the repository skill directory is missing.
        SkillDiscoveryError: If source_root is not in a readable Git checkout.
    """
    source_root = source_root.resolve()
    skill_root = source_root / ".agents" / "skills"
    if not skill_root.is_dir():
        message = f"skill directory not found: {skill_root}"
        raise FileNotFoundError(message)

    git_root_output = run_git(source_root, "rev-parse", "--show-toplevel")
    git_root = Path(os.fsdecode(git_root_output).strip()).resolve()
    try:
        relative_skill_root = skill_root.relative_to(git_root)
    except ValueError as error:
        message = f"skill directory is outside the Git checkout: {skill_root}"
        raise SkillDiscoveryError(message) from error

    pathspec = f":(top,literal){relative_skill_root.as_posix()}"
    tracked_output = run_git(
        git_root,
        "ls-files",
        "--cached",
        "--full-name",
        "-z",
        "--",
        pathspec,
    )

    skill_files = []
    for relative_path_bytes in tracked_output.split(b"\0"):
        if not relative_path_bytes:
            continue
        relative_path = Path(os.fsdecode(relative_path_bytes))
        skill_file = git_root / relative_path
        skill_path = skill_file.relative_to(skill_root)
        if (
            len(skill_path.parts) == 2
            and skill_path.name == "SKILL.md"
            and skill_file.is_file()
        ):
            skill_files.append(skill_file)

    return sorted(skill_files)


def main(arguments: list[str]) -> int:
    """Print discovered skill entrypoints, one absolute path per line."""
    if len(arguments) != 2:
        print("usage: list_skills.py <source-root>", file=sys.stderr)
        return 2

    try:
        skill_files = discover_skill_files(Path(arguments[1]))
    except (FileNotFoundError, SkillDiscoveryError) as error:
        print(error, file=sys.stderr)
        return 1

    for skill_file in skill_files:
        print(skill_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
