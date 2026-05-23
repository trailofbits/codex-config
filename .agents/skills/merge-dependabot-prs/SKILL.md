---
name: merge-dependabot-prs
description: >-
  Evaluate and merge Dependabot PRs with dependency-aware batching, transitive
  dependency analysis, build/test verification, GitHub Actions pin checks,
  sequential merges, and a summary report. Use when asked to merge or process
  open Dependabot PRs for a repository.
---

# Merge Dependabot PRs

## Contents
- Workflow
- references/workflow.md

Use this skill for controlled Dependabot PR evaluation and merging.

## Workflow

1. Read `references/workflow.md`.
2. Treat `owner/repo` as the primary input. If it is missing and cannot be
   inferred from the local git remote, ask one concise question.
3. Audit Dependabot configuration unless the user asks to skip it.
4. Verify the default branch build and tests before evaluating PRs.
5. Build a dependency graph, batch overlapping PRs, and evaluate independent
   work units.
6. Use parallel subagents only when the user explicitly requests a
   parallel/autonomous run; otherwise evaluate work units sequentially.
7. Merge only PASS work units. Leave WARN and FAIL results for human review
   with enough detail to act.
8. Re-test after each merge before proceeding to the next work unit.

Never merge directly on a warning, unresolved test failure, merge conflict, or
high-risk matrix gap.
