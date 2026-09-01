"""Minimal archive extraction fixture."""

from pathlib import Path


def extract_files(files: list[tuple[str, bytes]], destination: Path) -> None:
    """Write archive members below destination.

    Args:
        files: Archive-controlled member names and contents.
        destination: Directory selected by the trusted caller.
    """
    for member_name, contents in files:
        target = destination / member_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(contents)
