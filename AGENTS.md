# Codex Config Repository Instructions

## Contents

- [Repository role](#repository-role)
- [Source of truth](#source-of-truth)
- [File map](#file-map)
- [Editing rules](#editing-rules)
- [Validation](#validation)
- [Pull requests](#pull-requests)

## Repository role

This `AGENTS.md` is for contributors developing this repository. It is not the
global Codex guidance template installed for users.

The installable global guidance lives in `global-agents.md`. The installer copies
that file to `~/.codex/AGENTS.md`.

## Source of truth

Codex changes quickly. Before changing Codex config keys, model names, hook
events, rules syntax, permission profiles, MCP configuration, plugin layout, or
installer behavior, verify the current behavior with the official Codex docs or
the installed `codex` CLI.

If official docs and local CLI behavior disagree, state the mismatch in the PR
or final summary and keep the repository aligned with current local behavior
only when that is what users will actually run.

## File map

- `global-agents.md` - global `~/.codex/AGENTS.md` template for new installs.
- `config.toml` - default Codex config template.
- `mcp-template.toml` - optional MCP server entries to merge into config.
- `profile-template.toml` - optional profile for a second auth identity.
- `hooks/*.sh` - lifecycle hook scripts copied into `~/.codex/hooks/`.
- `rules/default.rules` - exec policy rules copied into `~/.codex/rules/`.
- `.agents/skills/install-codex-config/` - local installer workflow.
- `.agents/skills/*` - reusable workflows shipped with this config.
- `README.md` - user-facing setup and operating guide.

## Editing rules

- Keep this file repo-specific. Put reusable global agent behavior in
  `global-agents.md`.
- When an installable component changes, update `README.md` and
  `.agents/skills/install-codex-config/references/workflow.md` in the same
  change.
- When installer discovery or component names change, update
  `.agents/skills/install-codex-config/SKILL.md` too.
- Keep hooks small, deterministic, and POSIX-friendly Bash with
  `set -euo pipefail`.
- Treat hooks and rules as workflow guardrails, not security boundaries.
- Do not add compatibility shims for old file layouts; update the installer and
  docs to the new layout.

## Validation

Run the focused checks that match the files changed:

```bash
shellcheck hooks/*.sh
shfmt -d hooks/*.sh
codex execpolicy check --pretty --rules rules/default.rules -- git status
git diff --check
```

When `config.toml`, `mcp-template.toml`, or `profile-template.toml` changes,
also validate TOML syntax and run a strict Codex config check when practical.
Document expected environment-only warnings, such as missing auth in a throwaway
test home.

## Pull requests

Explain what the shipped config does now. Do not describe discarded approaches.
Call out any current-docs lookup used for Codex behavior, model names, hooks,
rules, MCP, or permission changes.
