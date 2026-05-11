#!/bin/bash
set -euo pipefail

# Codex PreToolUse hook for Bash. Blocks npm commands in projects that use pnpm.
# Extend this pattern for other package-manager conventions.

INPUT=$(cat)
CMD=$(printf '%s' "${INPUT}" | jq -r '.tool_input.command // empty')
CWD=$(printf '%s' "${INPUT}" | jq -r '.cwd // env.PWD')

[[ -z "${CMD}" ]] && exit 0
[[ ! -f "${CWD}/pnpm-lock.yaml" ]] && exit 0

if printf '%s\n' "${CMD}" | grep -qE '(^|;[[:space:]]*|&&[[:space:]]*)npm([[:space:]]|$)'; then
	printf 'BLOCKED: This project uses pnpm, not npm. Use pnpm instead.\n' >&2
	exit 2
fi

exit 0
