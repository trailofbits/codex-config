# Rust

Use the repository's pinned toolchain, features, workspace layout, and lint configuration. For
greenfield work or when the project has no established choice:

- Use the latest stable toolchain with `cargo fmt`, `cargo test`, and
  `cargo clippy --all-targets --all-features -- -D warnings`.
- Use `cargo deny check` for advisories, licenses, and bans. Use `cargo careful test` when its
  additional runtime checks justify the cost.
- Prefer clear `for` loops and mutable accumulators to dense iterator chains. Use `let ... else`
  for early exits and keep the happy path unindented.
- Shadow values through transformations instead of accumulating `raw_` and `parsed_` names.
- Use newtypes for distinct identifiers and enums for state machines. Use `thiserror` in libraries,
  `anyhow` in applications, and `tracing` for diagnostics.
- Avoid wildcard matches and panic paths in production logic. Configure Cargo lints to deny
  `unwrap_used`, `panic`, `unimplemented`, `todo`, debug/print macros, and unsafe lifecycle
  shortcuts when the project's compatibility needs allow it.

For a new crate, use this manifest lint block as a starting point. Keep restriction lints
individually selected and relax any lint that conflicts with the crate's supported Rust version or
public contract.

```toml
[lints.clippy]
pedantic = { level = "warn", priority = -1 }

unwrap_used = "deny"
expect_used = "warn"
panic = "deny"
panic_in_result_fn = "deny"
unimplemented = "deny"
allow_attributes = "deny"

dbg_macro = "deny"
todo = "deny"
print_stdout = "deny"
print_stderr = "deny"

await_holding_lock = "deny"
large_futures = "deny"
exit = "deny"
mem_forget = "deny"

module_name_repetitions = "allow"
similar_names = "allow"
```

Reference: [Clippy lint configuration](https://doc.rust-lang.org/clippy/lint_configuration.html).

Run tests with the same features CI uses. Do not assume `--all-features` is valid for a workspace
whose features are intentionally mutually exclusive.

Use `cargo-mutants` when mutation testing will materially test the suite's ability to catch faulty
behavior. Use `proptest` for parsers, serialization, state machines, and algorithms with useful
invariants. Neither tool is a routine requirement for every change.
