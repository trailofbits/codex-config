# Trail of Bits Codex Config

Opinionated defaults, documentation, and workflows for Codex CLI at Trail of Bits. Covers sandboxing, permissions, exec policy rules, hooks, skills, MCP servers, and usage patterns we've found effective for security audits, development, and research.

> Also see: [claude-code-config](https://github.com/trailofbits/claude-code-config) · [skills](https://github.com/trailofbits/skills) · [skills-curated](https://github.com/trailofbits/skills-curated) · [claude-code-devcontainer](https://github.com/trailofbits/claude-code-devcontainer) · [dropkit](https://github.com/trailofbits/dropkit) · [nono-config](https://github.com/trailofbits/nono-config)

**First-time setup:**

```bash
git clone git@github.com:trailofbits/codex-config.git
cd codex-config
codex
```

Then inside the session, run `$install-codex-config`. It walks you through installing each component, detects what you already have, and self-installs the skill so future runs work from any directory. Run it again after updates.

## Contents

**[Getting Started](#getting-started)**
- [Read These First](#read-these-first)
- [Initial Checklist](#initial-checklist)
- [Operating Loop](#operating-loop)
- [Prerequisites](#prerequisites)
- [Shell Setup](#shell-setup)
- [Settings](#settings)
- [Global AGENTS.md](#global-agentsmd)

**[Configuration](#configuration)**
- [Sandboxing](#sandboxing)
- [Hooks](#hooks)
- [Skills](#skills)
- [MCP Servers](#mcp-servers)

**[/goal](#goal)**
- [When to use it](#when-to-use-it)
- [Goals vs. skills](#goals-vs-skills)
- [Writing a goal](#writing-a-goal)
- [Security research goals](#security-research-goals)

**[Usage](#usage)**
- [Per-invocation overrides](#per-invocation-overrides)
- [Token tracking](#token-tracking)
- [Operational playbook](#operational-playbook)
- [Untrusted-repo posture](#untrusted-repo-posture)
- [Containerized runs](#containerized-runs)

## Getting Started

### Read These First

Before configuring anything, read these to understand why this setup works the way it does:

- [Codex CLI docs](https://developers.openai.com/codex) -- the official primer; config schema, sandbox model, exec policy, hooks, skills, and CLI flags
- [Codex for Knowledge Work](https://every.to/guides/codex-for-knowledge-work) -- Every's guide to using Codex as a workspace for knowledge work, not just code
- [Codex-maxxing](https://jxnl.github.io/blog/writing/2026/05/10/codex-maxxing/) -- Jason Liu on durable threads, memory, steering, browser/computer use, goals, and review surfaces
- [AI-assisted coding for teams that can't get away with vibes](https://blog.nilenso.com/blog/2025/05/29/ai-assisted-coding/) -- Nilenso's playbook for teams integrating AI tools with high standards
- [My AI Skeptic Friends Are All Nuts](https://fly.io/blog/youre-all-nuts/) -- Thomas Ptacek on why dismissing LLMs for coding is a mistake
- [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/) -- Ryan Lopopolo on how OpenAI's team shipped a million-line product with zero human-written code, and what that implies for how you structure repos, AGENTS.md files, and review loops

### Initial Checklist

Use this checklist after the first install and when starting in a new codebase:

1. Run `codex doctor --summary`; fix install, auth, MCP, or sandbox issues before long runs.
2. Add or customize the project's `AGENTS.md`.
3. Configure Context7 and Exa if the work needs current docs, web search, or code search.
4. Install the Trail of Bits skills you expect to use.
5. Confirm the sandbox and approval policy with `codex doctor` or `codex sandbox`.
6. Decide whether the run needs the default model or a separate API-key/cyber identity.
7. Start with one bounded, verifiable task; use `/goal` if it should survive multiple turns.
8. Run the project's normal tests/scanners once and record baseline failures before patching.

### Operating Loop

The Trail of Bits Codex loop is:

1. **Connect** the tools and source material the task actually needs.
2. **Contextualize** with `AGENTS.md`, project docs, known findings, and explicit constraints.
3. **Delegate or collaborate** based on risk: delegate repeatable, objective, checkable work; collaborate on ambiguous, judgment-heavy, or exploratory work.
4. **Review** where the artifact will live: inspect diffs in Git, PRs in GitHub, documents in their editor, and metrics against the source of truth.
5. **Compound** the useful parts into skills, workflows, scripts, checklists, or project instructions so the next run starts with more context.

### Prerequisites

#### Codex CLI

Install Codex with Homebrew:

```bash
brew install codex
codex --version
codex doctor --summary
```

Do not install Codex with npm. Trail of Bits enforces a 7-day cooldown on npm packages, so `npm install -g @openai/codex` will be behind upstream. If your install looks stale or `which -a codex` shows an npm install ahead of Homebrew, remove the npm copy first:

```bash
which -a codex
npm uninstall -g @openai/codex
brew install codex
codex update
```

The Homebrew package tracks stable releases directly. `codex update` is still useful after a stale install cleanup because it verifies the running CLI path.

#### Terminal: Ghostty

Use [Ghostty](https://ghostty.org). It uses native Metal GPU rendering, so it handles the high-volume text output from long Codex sessions without lag or memory bloat. Cmd+D / Cmd+Shift+D give you split panes for running Codex alongside a dev server, and it doesn't crash during extended autonomous runs.

```bash
brew install --cask ghostty
```

macOS only. On Linux, see the [Ghostty install docs](https://ghostty.org/docs/install/binary#linux-(official)). No Windows support yet -- use WezTerm there.

#### Tools

Install core tools via Homebrew:

```bash
brew install jq ripgrep fd ast-grep shellcheck shfmt \
  actionlint zizmor macos-trash node@24 pnpm uv
```

Python tools (via uv):

```bash
uv tool install ruff
uv tool install ty
uv tool install pip-audit
```

Rust toolchain:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install prek worktrunk cargo-deny cargo-careful
```

Node tools (also subject to the 7-day cooldown):

```bash
npm install -g oxlint agent-browser
```

### Shell Setup

Add to `~/.zshrc`:

```bash
alias codex-cyber-preview='codex -m gpt-5.5-cyber-preview --config model_reasoning_effort="xhigh"'
alias codex-cyber='codex -m gpt-5.4-cyber --config model_reasoning_effort="xhigh"'
```

The `-cyber` models require `OPENAI_API_KEY` from Trusted Access Cyber, not a ChatGPT subscription. Use them when `gpt-5.5` refuses (exploit shells, offensive code, malware analysis): quit the session, resume with one of these, run a few turns to establish context, then switch back to `codex` -- once context is in place, `gpt-5.5` typically continues without refusing.

### Settings

Official docs: [config reference](https://developers.openai.com/codex/config-reference).

Copy `config.toml` to `~/.codex/config.toml` (or merge entries into your existing file). If you already have a config, keep your authentication, project trust, and any local model overrides.

```bash
mkdir -p ~/.codex
cp config.toml ~/.codex/config.toml
```

The template sets:

- **`model = "gpt-5.5"`** with `model_reasoning_effort = "xhigh"` -- maximum reasoning is the default; we're optimizing for correctness, not token cost. Lower it per-session with `--config model_reasoning_effort="high"` if you specifically want to save tokens on a simple task.
- **`approval_policy = "on-request"`** -- Codex asks before stepping outside the sandbox; see [Sandboxing](#sandboxing) for the other values
- **`approvals_reviewer = "auto_review"`** -- routes eligible approval prompts through Codex's automatic reviewer
- **`default_permissions = "tob-workspace"`** -- selects the custom Trail of Bits sandbox profile: broad local reads, workspace/temp writes, no command network, deny-read rules for credentials and crypto wallets
- **`web_search = "cached"`** -- Codex's built-in web search caches responses to reduce token spend on repeated queries
- **`project_doc_fallback_filenames = ["CLAUDE.md"]`** -- migration aid for repos that haven't renamed `CLAUDE.md` to `AGENTS.md`; lets Codex still read the file
- **`cli_auth_credentials_store = "keyring"`** + **`mcp_oauth_credentials_store = "keyring"`** -- macOS Keychain (Linux: secret-service)
- **`[features] goals = true`** -- enables the [/goal loop](#goal)
- **`[tui]`** -- two-line status bar showing model, reasoning, context remaining, git branch, current dir
- **Hooks** wired to the three shipped scripts -- see [Hooks](#hooks)

### Global AGENTS.md

Official docs: [custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

The global `AGENTS.md` at `~/.codex/AGENTS.md` sets default instructions for every Codex session. It covers development philosophy (no speculative features, no premature abstraction, replace don't deprecate), code quality hard limits (function length, complexity, line width), language-specific toolchains for Python (`uv`, `ruff`, `ty`), Node/TypeScript (`oxlint`, `vitest`), Rust (`clippy`, `cargo deny`), Bash, GitHub Actions, plus testing methodology, code review order, untrusted-repo posture, skill authoring conventions, and workflow rules.

Copy the template into place:

```bash
cp AGENTS.md ~/.codex/AGENTS.md
```

Codex loads AGENTS.md from `~/.codex/` and from each project directory it traverses, with files closer to the current working directory taking precedence. Run `/status` inside a session to see which AGENTS.md files (and any `CLAUDE.md` fallbacks) are loaded.

For an example of a project-level AGENTS.md, see [crytic/slither/CLAUDE.md](https://github.com/crytic/slither/blob/master/CLAUDE.md) -- the same content works under either name since `project_doc_fallback_filenames` is set.

## Configuration

### Sandboxing

Official docs: [permissions](https://developers.openai.com/codex/permissions), [agent approvals & security](https://developers.openai.com/codex/agent-approvals-security), [rules](https://developers.openai.com/codex/rules).

Codex sandboxing has two controls you need to understand:

- `default_permissions` selects what local commands can read, write, and access over the network.
- `approval_policy` controls when Codex may ask to do more than the sandbox allows.

The Trail of Bits default is:

```toml
default_permissions = "tob-workspace"
approval_policy = "on-request"
approvals_reviewer = "auto_review"
```

That profile gives Codex broad local reads, workspace/temp writes, no command network, and deny-read rules for common credential stores, wallets, `.env`, `*.pem`, and `*.key`. The practical effect: Codex can inspect ordinary local files and edit the repo without prompting, while secrets, network use, and writes outside the workspace require approval or a different profile.

Do not set `sandbox_mode` in this config. If it appears in any active config layer, Codex uses that setting instead of `default_permissions`.

Use `:danger-full-access` or `approval_policy = "never"` only inside an external sandbox such as a devcontainer or disposable VPS. The shared default should stay interactive and sandboxed.

Rules and hooks are the command layer around the sandbox. `rules/default.rules` classifies unsandboxed command requests; hooks catch footguns even when a command stays inside the sandbox. The defaults block recursive force deletion, disk-formatting commands, force-push/reset mistakes, direct pushes to `main`/`master`, wrong package managers, and selected audit-log-worthy mutations.

Install:

```bash
mkdir -p ~/.codex/rules
cp rules/default.rules ~/.codex/rules/default.rules
```

#### Standalone testing

Use `codex sandbox` to test profile changes after installing the config:

```bash
codex sandbox macos --permissions-profile tob-workspace -C . -- cat ~/.ssh/id_rsa
codex sandbox macos --permissions-profile tob-workspace -C . -- git status
```

#### Alternatives

For full read+write isolation:

- [trailofbits/claude-code-devcontainer](https://github.com/trailofbits/claude-code-devcontainer) -- devcontainer with no host filesystem access (works for Codex with minor adjustments)
- [trailofbits/dropkit](https://github.com/trailofbits/dropkit) -- disposable DigitalOcean droplets via Tailscale; create, ssh in, run Codex, destroy

### Hooks

Official docs: [hooks](https://developers.openai.com/codex/hooks).

Hooks are deterministic checkpoints around Codex tool calls. They are more reliable than instructions for repetitive guardrails because the check runs at the moment of action: a `PreToolUse` hook can block `rm -rf`, and a `PostToolUse` hook can log a mutation after it happens.

Hooks are not a security boundary. Use them for workflow pressure: block known-bad patterns, enforce project conventions, add audit logs, or inject context at decision points. Keep sandboxing on.

#### Shipped examples

The three hooks in `hooks/` are the ToB defaults:

- [`block-dangerous-command.sh`](hooks/block-dangerous-command.sh) -- `PreToolUse` regex blocker for `rm -rf`, force-push to `main`/`master`, and a few other footguns. Belt-and-braces with `rules/default.rules`.
- [`enforce-package-manager.sh`](hooks/enforce-package-manager.sh) -- blocks `npm` when the project has `pnpm-lock.yaml`; tells Codex to use `pnpm` instead. Generalizes to any "use X not Y" convention.
- [`log-gam.sh`](hooks/log-gam.sh) -- `PostToolUse` audit log for Google Apps Manager (`gam`) mutations. Pattern generalizes to any CLI where you want to log writes.

Install:

```bash
mkdir -p ~/.codex/hooks
cp hooks/*.sh ~/.codex/hooks/
chmod +x ~/.codex/hooks/*.sh
```

The hooks block in `config.toml` wires them up. Each hook has a `timeout` (seconds, default 600) and an optional `statusMessage` shown in the TUI while it runs.

### Skills

Official docs: [skills](https://developers.openai.com/codex/skills).

Codex skills live in `~/.agents/skills/` and are loaded into the session as workflows the agent can invoke. They're closer to Claude's plugin model than to slash commands -- a skill bundles a `SKILL.md` (the agent-facing instructions) with `references/` (longer-form content the agent loads on demand) and `agents/openai.yaml` (interface metadata).

The `SKILL.md` format is shared across tools, and Codex also reads Claude Code marketplaces and the common `~/.agents/skills/` location, so Trail of Bits skills written for either agent generally work in both. The exception is hooks, which do not reliably port between Codex and Claude -- keep tool-specific guardrails in each tool's own config.

Four skills ship in this repo under `.agents/skills/`:

| Skill | What it does |
|-------|--------------|
| `$install-codex-config` | Installs or updates this Codex configuration from the local repo. Self-installs into `~/.agents/skills/` so it works from any directory after the first run. |
| `$fix-github-issue` | Takes a GitHub issue from triage through PR creation -- research, plan, implement, verify, self-review, push, comment back. |
| `$merge-dependabot-prs` | Evaluates and merges Dependabot PRs with dependency-aware batching, transitive analysis, build/test verification, and sequential merges. |
| `$review-and-fix-pr` | Reviews a PR, merges findings from `codex review` and other reviewers, fixes P1-P3 findings, and posts a summary comment. |

Keep `.agents/skills/` at the repo root for project-local use, or copy globally:

```bash
mkdir -p ~/.agents/skills
cp -R .agents/skills/* ~/.agents/skills/
```

#### Authoring

Every `SKILL.md` starts with a short `## Contents` block under the H1 -- a bulleted list of the file's H2 sections plus any referenced files. Codex may only re-load a prefix of an active skill file after a context compaction, so the table of contents is what lets the agent grep to the right section instead of going off-script. The `AGENTS.md` "Skill authoring" section is the canonical convention.

### MCP Servers

Official docs: [MCP](https://developers.openai.com/codex/mcp).

Everyone at Trail of Bits should set up at least **Context7** and **Exa** as global MCP servers.

| Server | What it does | Requirements |
|--------|--------------|--------------|
| Context7 | Up-to-date library documentation lookup | None (no API key) |
| Exa | Web and code search via real-browser fetch | `EXA_API_KEY` (Trail of Bits employees: shared key in 1Password; external users: [get one here](https://exa.ai)) |

Codex configures MCP in TOML, not in `.mcp.json`. Servers live under `[mcp_servers.NAME]` in `~/.codex/config.toml` (global) or `.codex/config.toml` (project-local, only loaded for trusted projects). Stdio servers use `command` + `args`; HTTP/SSE/WebSocket servers use `url` + optional `bearer_token_env_var`.

Append the template:

```bash
cat mcp-template.toml >> ~/.codex/config.toml
```

Then replace `EXA_API_KEY` placeholder with your actual key (or remove the `exa` entry if you don't have one).

Or use the CLI to add servers (writes to `~/.codex/config.toml`):

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
codex mcp add exa --env EXA_API_KEY="$EXA_API_KEY" -- npx -y exa-mcp-server
```

OAuth tokens for MCP servers are stored in the OS keychain via `mcp_oauth_credentials_store = "keyring"`. On platforms where the keyring backend is unreliable, switch to `"auto"`.

#### Recommended MCP servers

Beyond the baseline, these are worth adding for specific workflows:

| Server | What it does | Requirements |
|--------|--------------|--------------|
| [Granola](https://granola.ai) | Meeting notes and transcripts | Granola app with paid plan |
| [slither-mcp](https://github.com/trailofbits/slither-mcp) | Slither static analysis for Solidity -- vulnerability detection, call graphs, inheritance mapping, function metadata | Python 3.11+, Foundry/Hardhat |
| [pyghidra-mcp](https://github.com/clearbluejar/pyghidra-mcp) | Headless Ghidra reverse engineering -- binary analysis, decompilation, cross-references, semantic search | Ghidra (`GHIDRA_INSTALL_DIR` env var) |
| [Serena](https://github.com/oraios/serena) | Symbol-level code navigation and editing across 30+ languages via LSP | `uv`, language LSP servers |

## /goal

Official docs: [Follow a goal](https://developers.openai.com/codex/use-cases/follow-goals), [goal-mode prompting](https://developers.openai.com/codex/prompting#goal-mode), [CLI slash commands](https://developers.openai.com/codex/cli/slash-commands).

`/goal` is Codex's durable loop for one objective. It gives the session a standing contract and lets Codex continue across turns until the objective is complete, blocked, paused, or cleared.

### When to use it

Use `/goal` when the work is larger than one turn, has a clear stopping condition, and can be validated by commands or artifacts. A simple test: if you would repeat the same standing instruction three turns in a row, put it in the goal. Good fits are code migrations, issue implementation, large refactors, deployment retry loops, eval or prompt optimization, prototypes, games, and bounded audit checklists. Do not use it for a loose backlog, subjective cleanup, open-ended bug hunting, or work that needs frequent human decisions. For long efforts, chain smaller goals with review between checkpoints instead of creating one giant goal.

### Goals vs. skills

A goal is the objective for this stretch of work. A skill is reusable expertise for a recurring class of work. Use skills to teach Codex how to do something repeatably; use `/goal` to define what done means for the current run. A goal can invoke skills, but it should still name the scope, constraints, validation, and stop condition.

### Writing a goal

Requirements:

- `[features] goals = true` in `~/.codex/config.toml` for the CLI
- Interactive Codex session. `codex exec` is non-interactive and does not expose slash commands.
- Objective length at most 4,000 characters; put longer specs in `PLAN.md` or `GOAL.md`.

Controls:

- `/goal <objective>` -- set the active goal
- `/goal` -- view the current goal
- `/goal pause`, `/goal resume`, `/goal clear` -- control the run

If the goal is hard to define, start with `/plan`, refine the contract, then set `/goal`. Write goals as a work order:

```text
Objective:   one-sentence outcome
Scope:       files, directories, issue, logs, or plan Codex must read first
Constraints: what must not change
Validation:  exact commands or artifacts that prove progress
Stop:        explicit done condition or reason to pause
Checkpoints: smaller milestones with their own validation
Evidence:    output, diff, report, screenshot, or other proof to show at the end
```

### Security research goals

For security research, harden the goal against reward hacking:

- Ask Codex to convert a casual objective into a precise `/goal` prompt before starting the run.
- Use neutral wording such as "trigger and validate the issue" instead of "prove this is exploitable."
- Require Codex to check open issues, open PRs, and known-findings files before treating a bug as new.
- Keep a short progress log or findings file in the repo so compaction and resumed sessions have durable state.
- Stop after each meaningful finding for human review instead of letting one goal produce a pile of untriaged reports.
- Measure what the agent actually read. After an audit pass, run [trailofbits/aicov](https://github.com/trailofbits/aicov) to get HTML/gcov/lcov coverage of the files Codex (or Claude) opened, then set a follow-up goal to reach full audited coverage of the in-scope code.

## Usage

### Per-invocation overrides

Two CLI flags are useful for one-off runs that should not touch the global config:

- `codex --config model_reasoning_effort="high"` (or `"medium"` / `"low"`) reduces reasoning for one session when the default `xhigh` is overkill -- simple tasks, throwaway scripts, quick lookups. Editing `config.toml` is not required.
- `codex -c "service_tier=flex"` runs at the flex service tier -- roughly half-cost inference that is meant to retry on its own when it hits a 429. Good for long autonomous or batch runs where latency does not matter; not worth it for interactive work. `service_tier=fast` forces fast mode instead. Quota behavior under ChatGPT-plan auth is unconfirmed -- check `/status` if you care about the meter.
- `codex --ignore-user-config` and `codex --ignore-rules` shrink the hidden harness context (system prompt, exec policy, AGENTS.md). Useful for benchmarking, scratch work, and reducing token spend on simple tasks.

Codex carries a heavier hidden harness context per turn than Claude Code -- system prompt, tool schemas, exec policy, environment/project context, and accumulated transcript replay all flow into every request. Internal benchmarking found this drives most of Codex's cost premium over leaner agents. The two `--ignore-*` flags above are the practical mitigation for benchmarks and short scratch sessions where the harness isn't earning its keep.

### Token tracking

Use `/status` inside Codex for the current thread, context, and rate-limit picture. Use `npx @ccusage/codex` for daily, monthly, and session-level token usage with per-model breakdown. For authoritative billed spend, see [platform.openai.com/usage](https://platform.openai.com/usage).

### Operational playbook

These are field-tested fixes for specific machines and runs. Keep them out of the default config unless the machine's trust boundary matches the advice.

#### Long runs and weak networks

If the local network is slow or restrictive, run Codex on a disposable VPS, a [dropkit](https://github.com/trailofbits/dropkit) droplet, or a devcontainer instead of fighting the laptop network. Keep the repo, credentials, and teardown story simple. To drive that remote host from your laptop's Codex instead of SSHing in, see [remote connections](https://developers.openai.com/codex/remote-connections).

On macOS, keep the machine awake while a long session runs:

```bash
caffeinate -i codex
```

If Codex hangs during startup because Git is waiting for an SSH-key passphrase before the TUI can accept keyboard input, bypass the global Git config for that launch:

```bash
GIT_CONFIG_GLOBAL=/dev/null codex
```

#### Auth and credential stores

Changing API keys requires a fresh login flow; exporting `OPENAI_API_KEY` does not rewrite an active Codex session.

```bash
codex logout
codex
```

For side-by-side identities (for example, a ChatGPT-plan login and an API-key login), use a **profile**. A profile is a separate file at `~/.codex/<name>.config.toml` that overrides the model, provider, and auth while reusing your global `AGENTS.md`, skills, rules, and hooks. Copy the template, drop your key next to it, and select it with `--profile`:

```bash
cp profile-template.toml ~/.codex/api.config.toml
echo "sk-..." > ~/.codex/api-key.txt   # never commit API keys
codex --profile api
```

The profile name is the file stem (`api` above). The template defines a custom provider whose `auth.command` prints a bearer token to stdout; see [profile-template.toml](profile-template.toml) for the worked example. Run `/status` after launching to confirm the API-key provider is active and that your global `AGENTS.md` and skills still loaded.

For full isolation -- a wholly separate config home with its own `AGENTS.md`, skills, and history rather than a shared one -- point `CODEX_HOME` at a second directory instead:

```bash
mkdir -p "$HOME/.codex-api"
alias codex-api='CODEX_HOME=$HOME/.codex-api codex -m gpt-5.5-cyber-preview'
```

On Linux VPS images without a working secret-service backend, switch both credential stores to `"auto"`:

```toml
cli_auth_credentials_store = "auto"
mcp_oauth_credentials_store = "auto"
```

If `"auto"` still fails on a single-purpose disposable host, `"file"` works, but it stores credentials on disk in plaintext. Do not use it on a shared workstation.

Relax approvals and sandboxing only inside an external sandbox such as a disposable VPS or devcontainer:

```bash
codex -a never -s danger-full-access
```

Do not put that in the shared default config.

#### Plugins and marketplaces

When `/plugin` fails without a useful TUI error, use the CLI so the real error is printed:

```bash
codex plugin marketplace list
codex plugin add plugin@marketplace
```

If hardware-backed SSH auth or local Git state gets in the way, add a local marketplace checkout instead of debugging the interactive flow:

```bash
codex plugin marketplace add ./path/to/marketplace
```

Codex can keep serving a cached copy of a plugin after you update it. If your edits to a skill or marketplace are not taking effect, toggle the plugin off and back on in `/plugins` to force a reload. For a scripted refresh, send the `plugin/list` RPC to a running Codex app server -- see this [refresh script](https://github.com/trailofbits/galvanize-test-suite/blob/main/refresh-codex-plugin-cache.py).

#### Slash commands and steering

- `/status` -- inspect thread, context, and rate-limit status.
- `/side` -- ask a side question or get a status recap without steering the main thread.
- `/logout` -- clear stored auth before switching between plan/OAuth and API-key identities.

For more mid-run visibility, use detailed reasoning summaries per session:

```bash
codex --config model_reasoning_summary='"detailed"'
```

If summaries do not appear for the model you are using, uncomment `model_supports_reasoning_summaries = true` in `config.toml`.

#### Model pressure and parallelism

If a preview or project-scoped model is saturated, fall back to plain `gpt-5.5` rather than waiting on one blocked session. For throughput, prefer multiple isolated worktrees and Codex sessions over trying to make one session faster. When those parallel sessions are long-running and unattended, `service_tier=flex` (see [Per-invocation overrides](#per-invocation-overrides)) cuts their cost.

#### Reasoning effort: audit vs. build

Match verification depth to the task. The deciding factor is what catches a wrong assumption. In an audit there is no safety net -- an assumption the model does not check can ship straight into a finding as a false positive -- so favor higher reasoning effort (`xhigh`), even though it is slower, to make the model confirm reachability and re-derive invariants instead of asserting them. In build or refactor work your tests are the safety net: a wrong assumption usually surfaces as a failing test, so lower, faster effort is a fair trade for speed. Set this per run with `model_reasoning_effort` (see [Per-invocation overrides](#per-invocation-overrides)) instead of editing the default.

### Untrusted-repo posture

Any repo can plant instructions in agent-readable files (`AGENTS.md`, `CONTRIBUTING.md`, `SKILL.md`) and rely on Codex picking them up. Treat these files in third-party repos as untrusted input. The `## Untrusted repos` section in `AGENTS.md` is the running-agent side of this rule; this note is for the human operator setting up sessions, especially during security research on code you don't own.

### Containerized runs

For headless or Dockerized Codex runs, copy `~/.codex/auth.json` into the container so the CLI has credentials. The `[features]` table in `config.toml` still applies. Use `codex exec` for non-interactive jobs; slash commands require an interactive `codex` TUI with a TTY. To embed Codex in a service or pipeline rather than shelling out to `codex exec`, use the [Codex SDK](https://developers.openai.com/codex/sdk).
