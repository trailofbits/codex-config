# Shell

- Follow the script's current interpreter and portability target. Do not rewrite POSIX shell as
  Bash, or the reverse, without a requirement.
- New Bash scripts start with a suitable shebang followed by `set -euo pipefail`.
- Quote expansions, use arrays for argument lists in Bash, and keep paths resolved and bounded
  before destructive operations.
- Validate changed shell scripts with `shellcheck` and `shfmt -d` using the repository's formatting
  options. Use `shfmt -w` only when formatting changes are in scope.
- Prefer small scripts with clear exit statuses and actionable stderr. Use `jq` or another
  structure-aware parser for JSON rather than shell splitting.

Do not hide failures with broad `|| true`. When a command may fail legitimately, capture its status
and handle the expected cases explicitly.
