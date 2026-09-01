# Rust Change

## Fixture

Copy `evals/fixtures/rust-change/` into a clean worktree.

## Prompt

Change `parse_retries` to accept decimal values from 1 through 10 and reject zero or larger values
with an actionable error. Preserve the function signature, add boundary tests, and run the relevant
Rust checks.

## Mandatory rubric

- Preserves the `Result<u8, RetryError>` interface.
- Tests zero, one, ten, eleven, and malformed input.
- Runs and reports the repository's relevant Rust checks.
- Loads `development-standards/SKILL.md` and `rust.md`, with no other language reference.
