# Codex Config Repository Instructions

## Contents

- [Repository role](#repository-role)
- [Style direction](#style-direction)
- [Source of truth](#source-of-truth)
- [Surface boundaries](#surface-boundaries)
- [File map](#file-map)
- [Change coupling](#change-coupling)
- [Editing rules](#editing-rules)
- [Validation](#validation)
- [Pull requests](#pull-requests)

## Repository role

This `AGENTS.md` is for contributors developing this repository. It is not the
global Codex guidance template installed for users.

The installable global guidance lives in `global-agents.md`. The installer copies
that file to `~/.codex/AGENTS.md`.

Keep this repository shaped as an operator config distribution: opinionated
defaults, clear setup docs, sandbox and permission posture, hooks, rules,
skills, MCP servers, and usage playbooks for security audits, development, and
research.

## Style direction

Treat this repo as an installable operating manual for Codex, not as an
application library. Changes should make a new Codex install safer, more
current, and easier to reason about.

- Prefer concrete shipped artifacts over prose-only preferences. If a README
  recommendation belongs in default behavior, encode it in `config.toml`,
  `global-agents.md`, a hook, a rule, or a skill.
- Adapt patterns from other agent configuration projects only after verifying
  the current Codex equivalent. Do not copy another tool's settings, commands,
  hooks, marketplace behavior, or model advice into this repo as-is.
- Keep the docs runbook-shaped: what to install, what the default does, why the
  tradeoff exists, and how to verify it. Avoid long history or discarded
  approaches.
- Keep the default posture conservative and usable: sandboxed local work,
  approval for boundary crossings, no command network by default, and explicit
  escape hatches only for disposable or externally sandboxed environments.
- Make agent workflows file-based and inspectable. Prefer TOML config, shell
  hooks, rules files, skills, and documented commands over hidden state.
- Do not document phantom capabilities. Every documented feature should map to
  a file, command, config key, installed skill, or verified Codex behavior.

## Source of truth

Codex changes quickly. Before changing Codex config keys, model names, hook
events, rules syntax, permission profiles, MCP configuration, plugin layout, or
installer behavior, verify the current behavior with the official Codex docs or
the installed `codex` CLI.

If official docs and local CLI behavior disagree, state the mismatch in the PR
or final summary and keep the repository aligned with current local behavior
only when that is what users will actually run.

When another agent tool and Codex differ, prefer Codex ground truth over parity.
Keep Codex concepts native: global instructions live in `global-agents.md`,
settings live in TOML, install workflows live in skills, and command controls
live in permission profiles, exec policy rules, and hooks.

## Surface boundaries

- `AGENTS.md` is for contributors changing this repository. Keep repo style,
  coupling rules, and validation guidance here.
- `global-agents.md` is the installable `~/.codex/AGENTS.md` template. Put
  reusable agent behavior there, not in this file.
- `README.md` is the human setup and operating guide. It should describe the
  current shipped defaults and the practical tradeoffs for using them.
- `config.toml` is the default machine-readable Codex config. Keep comments
  short and focused on local behavior that matters during installation.
- `mcp-template.toml` and `profile-template.toml` are optional install snippets,
  not independent guides. Their README and installer descriptions must match.
- `hooks/*.sh` are deterministic lifecycle checks. They should read Codex hook
  JSON from stdin, emit clear blocking messages, and exit predictably.
- `rules/default.rules` classifies unsandboxed command requests. It complements
  sandboxing and hooks; it does not replace either.
- `.agents/skills/install-codex-config/` is the local-only installer workflow.
  It must install from checked-in repo files, not fetch raw files from GitHub.
- `.agents/skills/*` are reusable workflows shipped with the config. Keep each
  skill's `SKILL.md`, `references/`, and `agents/openai.yaml` aligned.

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

## Change coupling

Most changes in this repo have a documentation or installer twin. Before
committing, check the row that matches your edit:

| If you change | Also check |
|---------------|------------|
| `global-agents.md` | `README.md` global AGENTS section and installer component text |
| `config.toml` | `README.md` settings, sandboxing, hooks, `/goal`, and profile notes |
| `mcp-template.toml` | `README.md` MCP section and installer merge workflow |
| `profile-template.toml` | `README.md` auth/profile section and installer profile workflow |
| `hooks/*.sh` | `README.md` hooks section, `config.toml` hook wiring, shell lint output |
| `rules/default.rules` | `README.md` sandbox/rules section and `codex execpolicy check` output |
| `.agents/skills/*` | The skill `## Contents`, referenced workflows, and README skill table |
| Installer discovery or paths | Installer `SKILL.md`, `references/workflow.md`, and README setup |

If a merge from `main` adds global guidance to root `AGENTS.md`, move that
content to `global-agents.md` unless it is specifically about developing this
repo. If a merge introduces stale feature names, config keys, model names, or
reviewer semantics, resolve the factual drift as part of the conflict.

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
- Keep hook parsing structure-aware where practical. Prefer reading hook JSON
  with `jq` over ad hoc shell splitting.
- Treat hooks and rules as workflow guardrails, not security boundaries. The
  sandbox and approval policy are still the safety boundary.
- Keep `rules/default.rules` examples useful. New rules should include `match`
  examples and, where helpful, `not_match` examples.
- Keep `config.toml` root keys before TOML tables, and do not set
  `sandbox_mode` alongside `default_permissions`.
- Do not add compatibility shims for old file layouts; update the installer and
  docs to the new layout.
- Preserve user-local state in installer guidance: auth, trust decisions, local
  model/provider overrides, and existing skill directories should not be
  deleted or overwritten silently.

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

When editing only Markdown, run at least `git diff --check` and scan for stale
references to old install paths, other-tool-specific terms, outdated model names, or
Codex settings not present in the shipped templates.

## Pull requests

Explain what the shipped config does now. Do not describe discarded approaches.
Call out any current-docs lookup used for Codex behavior, model names, hooks,
rules, MCP, or permission changes.

Keep PRs small enough to review as one configuration decision. A good PR usually
updates the template, installer, docs, and validation evidence for one coherent
change instead of mixing unrelated workflow opinions.
