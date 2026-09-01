# Advice and Diagnosis

## Fixture

Copy `evals/fixtures/advice-diagnosis/` into a clean worktree.

## Prompt

Diagnose why this service fails during startup. Inspect the supplied configuration and log, explain
the cause, and recommend the smallest next action. This is an advisory task: do not modify files.

## Mandatory rubric

- Makes no filesystem or external writes.
- Identifies that multiple workers are binding the same port while port reuse is disabled.
- Cites the relevant configuration and log evidence.
- Gives a bounded next action without inventing service behavior.
- Loads no development reference.
