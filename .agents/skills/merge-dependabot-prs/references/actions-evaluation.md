# GitHub Actions Update Evaluation

Evaluate the PR in an isolated temporary worktree based on the current default branch.

## Inspect the update

- Identify every changed action, old and new reference, release type, permissions change, runtime
  change, and surrounding workflow edit.
- For a major update or changed runtime, read the action's upstream release and migration notes.
  Treat PR prose as a lead, not as authoritative evidence.
- Verify changed third-party `uses:` entries are pinned to full commit SHAs with version comments.
  Confirm the SHA belongs to the claimed upstream release.

## Validate

Run the repository's workflow checks plus `actionlint` and `zizmor` when available. Compare new
findings with the default-branch baseline. Inspect whether checkout credentials, token permissions,
secrets, event types, or untrusted pull-request inputs changed.

- PASS: workflow checks are clean, pins are verified, and no unhandled migration or permission
  change remains.
- WARN: checks pass but a tag-only pin, unverifiable release, or handled high-impact migration needs
  human review.
- FAIL: new workflow or security errors, an unhandled breaking change, a mismatched SHA, or a merge
  conflict.

Return the changed references, upstream evidence, commands and results, security observations,
concerns, and verdict. Do not merge from this phase.
