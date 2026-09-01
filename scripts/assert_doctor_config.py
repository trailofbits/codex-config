#!/usr/bin/env -S uv run --script
"""Assert that a Codex doctor JSON report loaded config successfully."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def main(arguments: list[str]) -> int:
    """Check only the config.load row in a doctor report."""
    if len(arguments) != 2:
        print("usage: assert_doctor_config.py <doctor.json>", file=sys.stderr)
        return 2

    report: dict[str, Any] = json.loads(Path(arguments[1]).read_text(encoding="utf-8"))
    config_check = report.get("checks", {}).get("config.load", {})
    if config_check.get("status") != "ok":
        print(json.dumps(config_check, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    print("Codex strict config load: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
