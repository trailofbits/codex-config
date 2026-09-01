#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
DEFAULT_CODEX_HOME=${CODEX_HOME:-$HOME/.codex}
DEFAULT_SKILL_VALIDATOR="$DEFAULT_CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py"
SKILL_VALIDATOR=${CODEX_SKILL_VALIDATOR:-$DEFAULT_SKILL_VALIDATOR}
CHECK_TMP=""

cleanup() {
	if [[ -n "$CHECK_TMP" && -d "$CHECK_TMP" ]]; then
		rm -r -- "$CHECK_TMP"
	fi
}
trap cleanup EXIT

cd "$REPO_ROOT"

uv run --frozen python -m unittest discover -s tests -p 'test_*.py'
shellcheck hooks/*.sh scripts/*.sh
shfmt -d hooks/*.sh scripts/*.sh

CHECK_TMP=$(mktemp -d)
cp config.toml "$CHECK_TMP/config.toml"
if ! CODEX_HOME="$CHECK_TMP" codex --strict-config doctor --json >"$CHECK_TMP/doctor.json"; then
	echo "Codex doctor reported expected environment checks; inspecting config.load only."
fi
uv run --frozen python scripts/assert_doctor_config.py "$CHECK_TMP/doctor.json"

if [[ ! -f "$SKILL_VALIDATOR" ]]; then
	echo "Bundled skill validator not found: $SKILL_VALIDATOR" >&2
	echo "Set CODEX_SKILL_VALIDATOR to quick_validate.py and retry." >&2
	exit 1
fi

while IFS= read -r skill_file; do
	uv run --frozen python "$SKILL_VALIDATOR" "$(dirname -- "$skill_file")"
done < <(uv run --frozen python scripts/list_skills.py "$REPO_ROOT")

INVALID_SKILL="$CHECK_TMP/invalid-skill"
mkdir -p "$INVALID_SKILL"
printf '%s\n' '---' 'name: invalid-skill' "description: 'unterminated" '---' \
	'# Invalid skill' >"$INVALID_SKILL/SKILL.md"
if uv run --frozen python "$SKILL_VALIDATOR" "$INVALID_SKILL" >/dev/null 2>&1; then
	echo "Skill validator accepted malformed YAML frontmatter." >&2
	exit 1
fi

codex execpolicy check --pretty --rules rules/default.rules -- git status
scripts/check_whitespace.sh
