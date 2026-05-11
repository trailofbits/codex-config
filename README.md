# Codex Config

Opinionated defaults, workflows, hooks, and skills for Codex.

**First-time setup:**

```bash
git clone https://github.com/trailofbits/codex-config.git
cd codex-config
codex
```

Then inside the session, run `$install-codex-config`. It walks you through installing each component, detects what you already have, and self-installs the command so future runs work from any directory. Run `/trailofbits:config` again after updates.

## Contents

- `AGENTS.md` - global Codex instructions, migrated from the Claude template.
- `config.toml` - user-level Codex configuration template.
- `mcp-template.toml` - Context7 and Exa MCP server template for Codex.
- `hooks/` - Codex lifecycle hooks for command blocking, package manager
  enforcement, and GAM mutation logging.
- `rules/default.rules` - Codex exec policy rules for commands that request
  execution outside the sandbox.
- `.agents/skills/` - Codex skills replacing the Claude slash-command workflows.
  Includes `install-codex-config`, the local-only Codex equivalent of the
  Claude `/trailofbits:config` installer.

## Manual Setup

Copy or merge the global instructions:

```bash
mkdir -p ~/.codex
cp AGENTS.md ~/.codex/AGENTS.md
```

Merge `config.toml` into `~/.codex/config.toml`. If you already have a Codex
config, keep your authentication, project trust, and local model settings.

Install hooks referenced by `config.toml`:

```bash
mkdir -p ~/.codex/hooks
cp hooks/*.sh ~/.codex/hooks/
chmod +x ~/.codex/hooks/*.sh
```

Install exec policy rules:

```bash
mkdir -p ~/.codex/rules
cp rules/default.rules ~/.codex/rules/default.rules
```

Configure MCP servers by appending `mcp-template.toml` to
`~/.codex/config.toml`, or by using Codex:

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
codex mcp add exa --env EXA_API_KEY="$EXA_API_KEY" -- npx -y exa-mcp-server
```

Use the checked-in skills repo-locally by keeping `.agents/skills/` at the repo
root. To make them global, copy them to `~/.agents/skills/`:

```bash
mkdir -p ~/.agents/skills
cp -R .agents/skills/* ~/.agents/skills/
```

After skills are available, ask Codex to use `$install-codex-config` to install
or update this configuration from the local repo. The installer skill supports
both layouts: this repository's `codex-config/` subfolder and the future
standalone repo root after extraction.

## Codex Notes

Codex reads `AGENTS.md` from `~/.codex` and from project directories. Project
files closer to the current working directory appear later and take precedence.

Codex stores configuration in TOML. User defaults live in
`~/.codex/config.toml`; project-scoped overrides live in `.codex/config.toml`
and load only for trusted projects.

`config.toml` sets `default_permissions = "org-workspace"` and defines a
custom filesystem profile. The profile allows writes in detected project roots
and temp space, denies common project secret files such as `.env`, `.pem`, and
`.key`, and blocks reads from home-directory credential stores like `~/.ssh`,
`~/.aws`, `~/.kube`, package registry tokens, macOS keychains, and common
wallet app data. Use `~/...` in these filesystem permission keys; `$HOME/...`
is not expanded by Codex config.

The template stores Codex and MCP OAuth credentials in the OS keyring. If a
platform does not support the keyring backend reliably, switch the credential
store values to `auto` after documenting the exception.

Hooks require `features.codex_hooks = true`. The template enables this and
wires three shell hooks. Keep `sandbox_mode = "workspace-write"` on; hooks are
guardrails, not a security boundary.
