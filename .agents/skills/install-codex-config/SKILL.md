---
name: install-codex-config
description: >-
  Install or update this organization's Codex configuration from repo-local
  files into the user's Codex home. Use when asked to set up, install, update,
  bootstrap, or sync this Codex configuration, including AGENTS.md, config.toml,
  hooks, rules, MCP servers, and bundled skills.
---

# Install Codex Config

## Contents
- Workflow
- references/workflow.md

Use this skill to install or update the checked-in Codex configuration on the
current machine.

## Workflow

1. Read `references/workflow.md`.
2. Use only files from the local repository. Do not fetch configuration from
   GitHub or any other network source.
3. Discover the source root:
   - If the repo contains `codex-config/config.toml`, use `codex-config/`.
   - Otherwise, if the repo root contains `config.toml` and `AGENTS.md`, use the
     repo root. This is the expected layout after extracting `codex-config/` into
     its own repository.
4. Inventory the target Codex files and ask the user which components to
   install or update before writing outside the repository.
5. Preview merges for existing `~/.codex/config.toml` and `~/.codex/AGENTS.md`;
   never silently overwrite likely user-customized files.
6. Install selected components into Codex paths, then summarize what changed and
   any follow-up needed for MCP credentials.

When installing globally, this skill should also install or update itself in
`~/.agents/skills/install-codex-config/` so it can be reused from any project.
