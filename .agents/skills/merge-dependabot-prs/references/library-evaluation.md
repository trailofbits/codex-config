# Library Update Evaluation

Evaluate the work unit in an isolated temporary worktree based on the current default branch. For a
batch, merge the candidate heads only inside that worktree. A conflict is a FAIL.

## Dependency analysis

Compare the candidate manifest, lockfile, and complete dependency tree with the recorded baseline.
Report:

- direct package version changes;
- transitive upgrades and downgrades with their parent dependency;
- added and removed transitive packages;
- major-version crossings, source changes, feature changes, or checksum anomalies; and
- release-note, compatibility, advisory, license, or minimum-runtime changes that affect the repo.

Use the package registry, upstream release notes, and primary advisories for facts that cannot be
established locally.

## Build and tests

Run the project and CI commands recorded during discovery. Include dependency-resolution,
generated-file, build, test, lint, and type checks relevant to the updated package. Use a full suite
only when CI or repository policy requires it, or when the dependency's reach or risk makes focused
checks insufficient.

Compare a failure with the healthy baseline. A new failure is a FAIL; a verified baseline failure is
reported separately and does not become evidence against the PR.

## Matrix gaps and verdict

Compare local coverage with CI matrices for operating systems, runtimes, features, architectures,
and dependency versions. Identify untested dimensions and why the package change makes each gap low
or high risk.

- PASS: checks pass, no unresolved downgrade or major transitive change exists, and no high-risk
  matrix gap remains.
- WARN: checks pass but a new transitive package, major crossing, advisory ambiguity, or high-risk
  untested dimension needs human review.
- FAIL: merge conflict, resolution failure, new build or test failure, or incompatible behavior.

Return a structured report with dependency changes, commands and results, matrix gaps, concerns,
and the verdict. Do not merge from this phase.
