---
name: review-and-fix-pr
description: >-
  Review an existing GitHub PR, merge findings from Codex and other available
  reviewers, fix P1-P3 findings, verify the quality pipeline, push fixes, and
  post a PR summary comment. Use when asked to review and fix a PR by number.
---

# Review and Fix PR

## Contents
- Workflow
- references/workflow.md

Use this skill to review a PR and carry actionable findings through to fixes.

## Workflow

1. Read `references/workflow.md`.
2. Treat the PR number as the primary input. If the PR number or canonical repo
   is missing and cannot be discovered from the local git remotes, ask one
   concise question.
3. Check out the PR branch locally and understand the base branch, linked issues, commits, and diff.
4. Run review passes that are available in the current environment. Use
   `codex review --base <base>` as the default Codex review pass.
5. Deduplicate findings and rank them P1-P4. Fix or explicitly dismiss P1-P3
   findings; leave P4 as informational unless trivial.
6. Discover checks from CI before using language defaults. Re-run relevant
   checks after fixes.
7. Push a separate fix commit and post the requested PR comment only after
   verifying the target repo and branch.

When a referenced reviewer tool or plugin is unavailable, note that gap and
continue with the available review paths.
