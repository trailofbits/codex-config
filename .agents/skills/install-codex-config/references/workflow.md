# Install Codex Config Workflow

This workflow installs the repository's Codex configuration into the user's
local Codex directories. It replaces the Claude `/trailofbits:config` installer
pattern with a Codex skill. It is intentionally local-only: never fetch files
from GitHub or any remote URL.

## Source Discovery

1. Determine the git root with `git rev-parse --show-toplevel` when available.
2. Choose the source root:
   - Prefer `<git-root>/codex-config` when it contains `config.toml` and
     `AGENTS.md`.
   - Otherwise use `<git-root>` when it contains `config.toml` and `AGENTS.md`.
   - If neither layout is found, inspect the current directory and its parents
     for the same two-file marker.
3. Confirm source files exist before offering them as installable components.

## Components

Offer these components to the user. Mark missing target components as
recommended, but still let the user choose.

- **AGENTS.md** - global Codex development standards.
  - Source: `<source-root>/AGENTS.md`
  - Target: `~/.codex/AGENTS.md`

- **config.toml** - model defaults, permissions, hooks, UI, analytics, history,
  and feature flags.
  - Source: `<source-root>/config.toml`
  - Target: `~/.codex/config.toml`

- **MCP servers** - Context7 and Exa server entries.
  - Source: `<source-root>/mcp-template.toml`
  - Target: merge into `~/.codex/config.toml`

- **Hooks** - command policy, package manager enforcement, and GAM mutation
  logging.
  - Source: `<source-root>/hooks/*.sh`
  - Target: `~/.codex/hooks/*.sh`

- **Rules** - command approval policy examples.
  - Source: `<source-root>/rules/default.rules`
  - Target: `~/.codex/rules/default.rules`

- **Skills** - reusable Codex workflows.
  - Source: `<source-root>/.agents/skills/*`
  - Target: `~/.agents/skills/*`

## Inventory

Read or check these target paths:

- `~/.codex/AGENTS.md`
- `~/.codex/config.toml`
- `~/.codex/hooks/block-dangerous-command.sh`
- `~/.codex/hooks/enforce-package-manager.sh`
- `~/.codex/hooks/log-gam.sh`
- `~/.codex/rules/default.rules`
- `~/.agents/skills/fix-github-issue/SKILL.md`
- `~/.agents/skills/review-and-fix-pr/SKILL.md`
- `~/.agents/skills/merge-dependabot-prs/SKILL.md`
- `~/.agents/skills/install-codex-config/SKILL.md`

Also inspect `~/.codex/config.toml` for existing `[mcp_servers.context7]` and
`[mcp_servers.exa]` tables.

## User Confirmation

Before writing outside the repository, present a concise install plan:

- selected components
- source root
- target paths
- overwrite or merge behavior for existing files

Ask for confirmation. If the environment supports a structured selection UI,
use it. Otherwise ask a single concise question and accept a comma-separated
list such as `agents, config, mcp, hooks, rules, skills, all`.

## Install Rules

### AGENTS.md

If `~/.codex/AGENTS.md` is missing, install the source file. If it exists, show
the user a diff or concise summary and ask whether to overwrite, skip, or merge
manually. Do not silently overwrite it.

### config.toml

If `~/.codex/config.toml` is missing, install the source file. If it exists,
merge conservatively:

- Preserve user keys that are not present in the source template.
- Prefer the source template for org-standard keys when the user selected a
  config update.
- Preserve authentication, trust, and local provider/model overrides unless the
  user explicitly asks to replace them.
- Show the merged TOML before writing.

After writing, validate TOML syntax.

### MCP servers

Merge only missing `[mcp_servers.context7]` and `[mcp_servers.exa]` tables from
`mcp-template.toml` into `~/.codex/config.toml`. Do not duplicate existing MCP
server entries. Remind the user that Exa needs `EXA_API_KEY` available in the
environment or credential management layer.

### Hooks

Create `~/.codex/hooks/` if needed. Copy selected hook scripts from the source
root and set executable bits. Existing hook files may be overwritten after the
user confirms the hooks component.

### Rules

Create `~/.codex/rules/` if needed. Copy `default.rules`. If the target exists,
ask whether to overwrite or skip unless the user selected a full refresh.

### Skills

Create `~/.agents/skills/` if needed. Copy each source skill directory,
including this installer skill. Existing skill directories may be overwritten
after the user confirms the skills component. Do not delete skill directories
that are not present in the source repo.

## Post-Install

Summarize:

- files installed
- files merged
- files skipped
- validation run
- follow-up needed for `EXA_API_KEY` or platform-specific keyring behavior

If `config.toml` changed, suggest starting a fresh Codex session so the new
defaults, hooks, skills, and MCP entries are loaded.
