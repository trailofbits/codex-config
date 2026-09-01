---
name: development-standards
description: >-
  Apply implementation standards only when a task requires changes to code,
  tests, dependencies, build configuration, shell scripts, or CI. Do not invoke
  for diagnosis or advice without code changes, documentation-only work, or chat.
---

# Development Standards

## Routing

Read only the references that match files in scope:

- Python source, tests, `pyproject.toml`, or Python lockfiles:
  [references/python.md](references/python.md)
- JavaScript, TypeScript, `package.json`, or Node lockfiles:
  [references/node-typescript.md](references/node-typescript.md)
- Rust source, `Cargo.toml`, or `Cargo.lock`: [references/rust.md](references/rust.md)
- Go source, `go.mod`, or `go.sum`: [references/go.md](references/go.md)
- Shell scripts: [references/shell.md](references/shell.md)
- GitHub Actions workflows or action metadata:
  [references/github-actions.md](references/github-actions.md)

For mixed changes, load each matching reference and no others. Skip them for documentation or
advisory tasks.

## Code

- Create a shared utility only after the same pattern occurs in multiple places.
- Prefer explicit control flow and cohesive modules. Simplify or justify long, complex, deeply
  nested functions and interfaces with many positional parameters.
- Use the standard library or an existing dependency when it fits. Before adding or upgrading a
  dependency, verify its supported release and compatibility, inspect the lockfile, and follow the
  project's pinning and supply-chain policy.
- Fail with the operation, relevant input or state, and a useful next step; do not swallow errors.
- Delete commented-out code. Comments should explain constraints or surprising behavior.

## Testing

- Test behavior rather than implementation details. Cover boundaries, malformed and empty input,
  failures, and intentional error paths.
- Mock only slow, non-deterministic, or external boundaries.
- For a regression or important invariant, confirm the test fails against the faulty behavior.
- Fix warnings caused by the change. If a warning cannot be removed safely, use the narrowest
  valid suppression and explain it.
