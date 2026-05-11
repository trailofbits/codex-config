#!/bin/bash
set -euo pipefail

# Codex PostToolUse hook for Bash. Logs GAM (Google Apps Manager) write
# operations to JSONL. Adapt verb patterns for any CLI that needs mutation logs.

INPUT=$(cat)
COMMAND=$(printf '%s' "${INPUT}" | jq -r '.tool_input.command // empty')
CWD=$(printf '%s' "${INPUT}" | jq -r '.cwd // env.PWD')

[[ -z "${COMMAND}" ]] && exit 0
[[ "${COMMAND}" != *'gam7/gam '* ]] && exit 0

# Verb lists verified against GamCommands.txt v7.33.00.
READ_PATTERN='(print|show|info|get|list|report|check|version|help)'
WRITE_PATTERN='(create|add|update|delete|remove|suspend|unsuspend|wipe|sync|move|transfer'
WRITE_PATTERN+='|trash|purge|enable|disable|deprovision)'

GAM_ARGS="${COMMAND#*gam7/gam }"
FIRST_WORD="${GAM_ARGS%% *}"

printf '%s\n' "${FIRST_WORD}" | grep -qiE "^${READ_PATTERN}$" && exit 0

ACTION=$(
	printf '%s\n' "${GAM_ARGS}" |
		grep -oiE "(^|[[:space:]])${WRITE_PATTERN}([[:space:]]|$)" |
		head -1 |
		tr -d ' ' || true
)
[[ -z "${ACTION}" ]] && exit 0

EXIT_CODE=$(
	printf '%s' "${INPUT}" |
		jq -r '.tool_response.exit_code // .tool_result.exit_code // 0'
)
if [[ "${EXIT_CODE}" == "0" ]]; then
	STATUS="success"
else
	STATUS="failed"
fi

LOG_FILE="${CWD}/google/.changelog-raw.jsonl"
mkdir -p "$(dirname "${LOG_FILE}")"

jq -nc \
	--arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
	--arg action "${ACTION}" \
	--arg command "${COMMAND}" \
	--arg status "${STATUS}" \
	'{timestamp: $ts, action: $action, command: $command, status: $status}' \
	>>"${LOG_FILE}"

if [[ "${STATUS}" == "success" ]]; then
	printf 'GAM MUTATION: %s - logged to %s\n' "${ACTION}" "${LOG_FILE}"
fi

exit 0
