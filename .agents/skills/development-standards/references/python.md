# Python

Use the project's supported Python versions and configured tools. For greenfield work or when the
project has no established choice:

- Prefer absolute imports. Give non-trivial public APIs Google-style docstrings when the project
  does not specify another convention.
- Use a current supported Python release and create environments with `uv venv`.
- Manage dependencies and lock state with `uv`; do not introduce pip, Poetry, or another manager
  alongside it.
- Use `ruff check` and `ruff format`, `ty check`, and `pytest -q`.
- Put tests under `tests/` in a structure that mirrors the package. Use `uv_build` for pure Python
  packages and `hatchling` when an extension build needs it.
- Configure strict type rules in `pyproject.toml` and keep public interfaces typed.
- Before deployment, run the project's dependency audit. For a new deployable project, use
  `pip-audit`, exact direct-dependency pins, a lockfile, and hash verification where supported.

For a new project, use this Ruff configuration as a starting point and adjust it to the project's
public API and compatibility requirements:

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = [
  "A", "B", "C4", "C90", "D", "E", "F", "I", "N",
  "PL", "PT", "RUF", "SIM", "TID", "UP",
]

[tool.ruff.lint.mccabe]
max-complexity = 8

[tool.ruff.lint.pylint]
max-args = 5
max-positional-args = 5
max-statements = 50

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D"]
```

The matching rule families must be selected for these limits to run: `C90` for cyclomatic
complexity, `PL` for argument and statement limits, `D` for the docstring convention, and `TID`
for the relative-import ban. Ruff 0.15 exposes `PLR0917`, the positional-argument rule, only in
preview mode; Ruff 0.16 stabilizes it. If the project supports an older Ruff, confirm the rule is
available, then either enable preview mode deliberately or omit `max-positional-args` and rely on
`max-args`.

Reference: [Ruff settings](https://docs.astral.sh/ruff/settings/).

Use `uv run <tool>` for tools in the project environment. Do not modify the global environment
merely to satisfy a generic fallback recommendation.
