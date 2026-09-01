# Go

Use the version in `go.mod`, the repository's task runner, and its configured linters. For
greenfield work or when no project convention exists:

- Format with `gofmt` and organize imports with the project's chosen import tool.
- Run `go test ./...`, `go vet ./...`, and `go build ./...` when they match the module layout.
- Use `golangci-lint` only with a checked-in configuration and a pinned CI version.
- Wrap errors with operation context and preserve the original error for `errors.Is` or
  `errors.As`. Do not discard returned errors.
- Prefer small interfaces defined by consumers. Avoid interface abstractions created only for
  hypothetical reuse.
