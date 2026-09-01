# Python Change

## Fixture

Copy `evals/fixtures/python-change/` into a clean worktree.

## Prompt

Update `parse_port` so it rejects port zero and strings with leading or trailing whitespace while
continuing to accept decimal ports from 1 through 65535. Preserve its public signature, include the
bad input in each `ValueError`, add focused tests, and run the relevant checks.

## Mandatory rubric

- Changes only the Python implementation and tests needed for the behavior.
- Covers zero, whitespace, lower and upper valid boundaries, and the existing malformed case.
- Reports exact test evidence.
- Loads `development-standards/SKILL.md` and `python.md`, with no other language reference.
