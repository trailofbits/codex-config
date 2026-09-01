---
name: install-codex-config
description: >-
  Install or update this organization's Codex configuration from repo-local
  files into the user's Codex home. Use when asked to set up, install, update,
  bootstrap, or sync this Codex configuration, including the global AGENTS
  template, config.toml, hooks, rules, MCP servers, profile templates, and
  bundled skills.
---

# Install Codex Config

## Contents

- Source discovery
- Components
- Inventory
- User confirmation
- Install rules
- Post-install

Use this skill to install or update the checked-in Codex configuration on the
current machine. Use only files from the local repository. Do not fetch configuration from GitHub
or any other network source.

## Source discovery

1. Determine the git root with `git rev-parse --show-toplevel` when available.
2. Choose the source root:
   - Prefer `<git-root>/codex-config` when it contains `config.toml` and
     `global-agents.md`.
   - Otherwise use `<git-root>` when it contains `config.toml` and
     `global-agents.md`. This is the expected layout after extracting `codex-config/` into its own
     repository.
   - If neither layout is found, inspect the current directory and its parents for the same
     two-file marker.
3. Confirm source files exist before offering them as installable components.

## Components

Offer these components to the user. Mark missing target components as recommended, but still let
the user choose.

- **AGENTS.md**: compact cross-task working agreements for Codex sessions.
  - Source: `<source-root>/global-agents.md`
  - Target: `~/.codex/AGENTS.md`
- **config.toml**: model defaults, permissions, hooks, TUI status line, analytics, history, and
  feature flags.
  - Source: `<source-root>/config.toml`
  - Target: `~/.codex/config.toml`
- **MCP servers**: Context7 and Exa server entries.
  - Source: `<source-root>/mcp-template.toml`
  - Target: merge into `~/.codex/config.toml`
- **Profile template** (optional): auth-identity profile for `--profile`. Do not install it by
  default; offer it only if the user wants a second identity, such as an API-key login alongside a
  ChatGPT-plan login.
  - Source: `<source-root>/profile-template.toml`
  - Target: copy to `~/.codex/<name>.config.toml` using the user's name or `api` by default.
- **Hooks**: command policy, package manager enforcement, and GAM mutation logging.
  - Source: `<source-root>/hooks/*.sh`
  - Target: `~/.codex/hooks/*.sh`
- **Rules**: command approval policy examples.
  - Source: `<source-root>/rules/default.rules`
  - Target: `~/.codex/rules/default.rules`
- **Skills**: reusable Codex workflows, including project-aware development configuration examples.
  - Discover sources with
    `uv run --frozen python <source-root>/scripts/list_skills.py <source-root>`.
  - Each reported `.../<name>/SKILL.md` maps to `~/.agents/skills/<name>/SKILL.md`; copy its
    complete skill directory.

## Inventory

Read or check these fixed target paths:

- `~/.codex/AGENTS.md`
- `~/.codex/config.toml`
- `~/.codex/hooks/block-dangerous-command.sh`
- `~/.codex/hooks/enforce-package-manager.sh`
- `~/.codex/hooks/log-gam.sh`
- `~/.codex/rules/default.rules`

Run the skill discovery script and check the corresponding `~/.agents/skills/<name>/SKILL.md`
target for every result. Do not maintain a hard-coded skill inventory in this workflow.

Also inspect `~/.codex/config.toml` for existing `[mcp_servers.context7]` and
`[mcp_servers.exa]` tables. If the user asks about the optional profile template, check for existing
`~/.codex/*.config.toml` profile files before writing one.

## User confirmation

Before writing outside the repository, present a concise install plan:

- selected components;
- source root;
- target paths; and
- overwrite or merge behavior for existing files.

Ask for confirmation. If the environment supports a structured selection UI, use it. Otherwise ask
a single concise question and accept a comma-separated list such as
`agents, config, mcp, hooks, rules, skills, all`.

## Install rules

### AGENTS.md

If `~/.codex/AGENTS.md` is missing, install `global-agents.md` from the source root. If it exists,
show the user a diff or concise summary and ask whether to overwrite, skip, or merge manually. Do
not silently overwrite it.

### config.toml

If `~/.codex/config.toml` is missing, install the source file. If it exists, merge conservatively:

- Preserve user keys that are not present in the source template.
- Prefer the source template for organization-standard keys when the user selected a config update.
- Preserve authentication, trust, and local provider/model overrides unless the user explicitly
  asks to replace them.
- Show the merged TOML before writing.

After writing, validate TOML syntax.

### MCP servers

Merge only missing `[mcp_servers.context7]` and `[mcp_servers.exa]` tables from
`mcp-template.toml` into `~/.codex/config.toml`. Do not duplicate existing MCP server entries.
Remind the user that Exa needs `EXA_API_KEY` available in the environment or credential management
layer.

### Profile template

Only install this component when the user opts in. Ask for a profile name, defaulting to `api`, and
copy `profile-template.toml` to `~/.codex/<name>.config.toml`. Do not overwrite an existing profile
of that name without confirmation. Remind the user to create the key file the profile reads; the
template uses `~/.codex/api-key.txt`. Never commit API keys. If the user chose a non-default name,
update the `api-key.txt` path in the copied profile's `auth.command` to match. Select the profile at
runtime with `codex --profile <name>`; do not merge it into `config.toml`.

### Hooks

Create `~/.codex/hooks/` if needed. Copy selected hook scripts from the source root and set
executable bits. Existing hook files may be overwritten after the user confirms the hooks
component.

### Rules

Create `~/.codex/rules/` if needed. Copy `default.rules`. If the target exists, ask whether to
overwrite or skip unless the user selected a full refresh.

### Skills

Run the discovery script immediately before preview and again immediately before installation.
Create `~/.agents/skills/` if needed. For every reported entrypoint, copy its complete parent skill
directory to the same directory name under the target. Existing discovered skill directories may
be overwritten after the user confirms the skills component. Do not delete or change target skill
directories that are absent from the source repository.

When installing skills globally, install every discovered skill, including this one. Preserve
unrelated user-local skill directories.

## Post-install

Summarize:

- files installed;
- files merged;
- files skipped;
- validation run; and
- follow-up needed for `EXA_API_KEY` or platform-specific keyring behavior.

If `config.toml` changed, suggest starting a fresh Codex session so the new defaults, hooks, skills,
and MCP entries are loaded.
