# Installation

## Requirements

- Codex CLI 0.155.0 or newer
- Python 3.11 or newer
- Access to GPT-6 Sol and GPT-6 Luna in your Codex environment

The repository does not grant model access.

## Preview

From the repository root:

```bash
python scripts/install.py plan
```

The plan shows each target path and whether it will be created, kept, or backed up/replaced.

## Apply

```bash
python scripts/install.py apply
```

By default, `CODEX_HOME` is taken from the environment and otherwise resolves to `~/.codex`.

To install into an isolated test home:

```bash
python scripts/install.py apply --codex-home /tmp/codex-test
```

## What gets installed

Profiles are copied as:

```text
~/.codex/sol-luna.config.toml
~/.codex/sol-only.config.toml
~/.codex/sol-luna-fast.config.toml
```

Agent roles are copied into:

```text
~/.codex/agents/
```

The installer deliberately does not edit `~/.codex/config.toml`.

## Backups

If a managed target already exists and differs, it is copied first into:

```text
~/.codex/backups/codex-sol-luna-switchable/<timestamp>/
```

A manifest is written to:

```text
~/.codex/codex-sol-luna-switchable.manifest.json
```

## Verify

```bash
python scripts/install.py status
codex --profile sol-luna
```

Inside Codex, spawn an `explorer` and a `worker`, then inspect effective child metadata. Verify actual routing instead of trusting the parent's textual summary.

## Project orchestration policy

The profile/agent install is global. The orchestration policy is intentionally project-scoped.

Copy or merge:

```text
templates/AGENTS.md
```

into the target repository's root `AGENTS.md` only when you want that repository to use these delegation rules.
