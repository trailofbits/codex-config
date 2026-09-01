# Mixed Python and GitHub Actions Change

## Fixture

Copy `evals/fixtures/mixed-python-actions/` into a clean worktree.

## Prompt

Add Python 3.13 to this package's supported and tested versions. Update the Python support check,
its tests, package metadata, and the CI matrix. Preserve the existing action SHA pins and run all
relevant local checks.

## Mandatory rubric

- Updates Python behavior, tests, package metadata, and only the CI matrix value needed.
- Preserves full action SHA pins and comments.
- Reports tests plus available workflow validation.
- Loads `development-standards/SKILL.md`, `python.md`, and `github-actions.md`, with no unrelated
  reference.
