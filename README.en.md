# Codex Sol/Luna Switchable

A community configuration for Codex CLI that keeps the **root model user-selectable** while delegating bounded exploration, research, implementation, testing, and first-pass review to **GPT-6 Luna**.

> Independent community project. Not affiliated with or endorsed by OpenAI. Model and Codex availability depend on account, plan, region, and client version.

## Profiles

```bash
codex --profile sol-luna
codex --profile sol-only
codex --profile sol-luna-fast
```

`sol-luna` is the recommended daily profile. `sol-only` disables multi-agent delegation. `sol-luna-fast` opts the whole session into Fast because current Codex children inherit the root service tier. None of these profiles pins the root `model` or `model_reasoning_effort`; the active Codex selection/config decides the root.

The root model is user-selectable, but it must be compatible with the active Codex multi-agent backend and able to spawn GPT-6 Luna subagents. Compatibility may change across Codex versions and model-catalog updates, so routing should be verified from actual child session metadata.

## Install

Requires Codex CLI 0.155.0+ and Python 3.11+.

```bash
python scripts/install.py plan
python scripts/install.py apply
python scripts/install.py status
```

The installer manages only the three profile files and five agent role files. It does not edit `$CODEX_HOME/config.toml`.

See [README.md](README.md) for the full Chinese documentation and [docs/INSTALL.md](docs/INSTALL.md) for installation details.

## License

MIT.
