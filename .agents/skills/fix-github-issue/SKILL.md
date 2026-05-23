---
name: fix-github-issue
description: >-
  End-to-end GitHub issue implementation workflow. Use when asked to fix or
  implement a GitHub issue, create a branch, make code changes, run tests and
  linters, self-review, push a branch, open a PR, and comment back on the issue.
---

# Fix GitHub Issue

## Contents
- Workflow
- references/workflow.md

Use this skill to take a GitHub issue from triage through PR creation.

## Workflow

1. Read `references/workflow.md`.
2. Treat the issue number as the primary input. If the issue number or
   canonical repo is missing and cannot be discovered from the local git
   remotes, ask one concise question.
3. Follow the workflow phases in order: research, plan, branch, implement,
   verify, self-review, fix findings, commit, push, PR, issue comment.
4. Prefer the project's CI configuration over generic defaults when discovering checks.
5. Use Exa MCP if configured for external research. Otherwise use Codex web
   search and cite sources when research informs the fix.
6. Use Codex-native review tools where the reference mentions Claude-specific
   commands. `codex review --base <base>` is the default external review pass.
7. Before writing to GitHub, confirm the target repo and branch are correct.

Delete temporary planning files before committing unless the user explicitly
asks to keep them.
