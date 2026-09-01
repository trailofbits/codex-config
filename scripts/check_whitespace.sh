#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=${CHECK_REPO_ROOT:-$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)}

cd "$REPO_ROOT"

git diff --check
git diff --cached --check

base_ref=${CHECK_BASE_REF:-}
if [[ -z "$base_ref" ]]; then
	for candidate in refs/remotes/origin/main refs/heads/main; do
		if git rev-parse --verify --quiet "$candidate" >/dev/null; then
			base_ref=$candidate
			break
		fi
	done
fi

if [[ -z "$base_ref" ]]; then
	echo "No main branch found; set CHECK_BASE_REF to enable committed whitespace checks." >&2
	exit 1
fi

merge_base=$(git merge-base HEAD "$base_ref")
git diff --check "$merge_base" HEAD
