---
name: merge-dependabot-prs
description: >-
  Discover, evaluate, and optionally merge open Dependabot pull requests with
  dependency-aware ordering and post-merge verification. Use when asked to
  process or merge Dependabot PRs for a repository.
---

# Merge Dependabot PRs

## Contents

- Workflow
- Authorization
- Discovery and baseline
- Cleanup and report
- references/library-evaluation.md
- references/actions-evaluation.md
- references/merge.md

## Workflow

Treat `owner/repo` as the primary input and infer it from local remotes when possible.

1. Follow [Discovery and baseline](#discovery-and-baseline) to inventory PRs, establish a healthy
   baseline, classify updates, and order work units.
2. Before evaluating library updates, read
   [references/library-evaluation.md](references/library-evaluation.md). Do not load the Actions
   evaluation template unless the run also includes Actions updates.
3. Before evaluating GitHub Actions updates, read
   [references/actions-evaluation.md](references/actions-evaluation.md). Do not load the library
   evaluation template unless the run also includes library updates.
4. If merging is authorized and PASS work units exist, read
   [references/merge.md](references/merge.md) immediately before the first merge.
5. Follow [Cleanup and report](#cleanup-and-report) after evaluation or merging.

Evaluate work units sequentially unless the user explicitly requested parallel agents. Any editing
subagent must use an isolated worktree.

## Authorization

Processing can mean evaluation without mutation. Do not approve, merge, push, comment, or open a
configuration PR unless the user explicitly authorized those GitHub writes. Before the first write,
confirm the exact repository, PR set, merge method, and current branch-protection status.

## Discovery and baseline

### Repository and configuration

Use the supplied checkout when suitable; otherwise clone the exact `owner/repo` into a fresh
temporary directory. Resolve the default branch from GitHub rather than assuming `main`.

Inspect `.github/dependabot.yml` and active manifests for ecosystem coverage, correct directories,
weekly scheduling, a seven-day cooldown, and useful grouping. A repository with `uv.lock` should use
Dependabot's `uv` ecosystem for that directory. Preserve repository-specific labels, reviewers,
limits, and schedules. Report configuration gaps; create a corrective branch or PR only when that
external work is explicitly authorized.

### Open pull requests

List open pull requests authored by Dependabot with number, title, head ref, changed files, labels,
mergeability, checks, and dependency metadata.

Classify a PR as an Actions update only when all changed files are under `.github/workflows/` or
`.github/actions/`. Classify every other dependency update as a library update.

### Healthy baseline

Check out and update the default branch. Discover required commands from project instructions, CI,
manifests, lockfiles, and task runners. Use the development-standards skill only for missing generic
guidance.

Run the CI-required and change-relevant baseline build and tests. Use a full suite when repository
policy, CI, or the breadth of queued dependency changes justifies it. If the default branch is
unhealthy, stop before evaluating PRs and report the failing baseline.

Record the dependency tree or lockfile state, commands, passing result, and CI matrix dimensions.

### Work units

For library PRs, identify direct dependencies and compare overlapping lockfile sections and
transitive relationships. Batch PRs only when they update interdependent packages or cannot be
evaluated independently without lockfile conflicts. Keep Actions updates independent.

Order library work units from leaf dependencies toward shared or core dependencies. Print the
planned order and the reason for each batch before evaluation.

## Cleanup and report

Remove only temporary branches and worktrees created by this run. Return the primary checkout to its
original branch and preserve unrelated local state.

Report every discovered PR with title, type, evaluated head SHA, verdict, action, and concise notes.
Include totals for merged, WARN, FAIL, skipped after prior merges, and not evaluated. For every
non-merged PR, include the specific concern or failure and the smallest next step.

Also report:

- baseline commands and result;
- Dependabot configuration gaps and whether a corrective PR was authorized or created;
- external sources used for release, advisory, or pin verification;
- CI matrix dimensions not tested locally; and
- exact GitHub writes performed.

Do not describe an approval, merge, comment, or configuration change as complete until its GitHub
state has been read back and verified.
