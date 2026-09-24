# Codex Sol/Luna Switchable

**Root: you choose the model and reasoning. Luna: it takes on execution work suited to delegation.**

Install once, then run Codex normally. Ordinary v0.3 users need no profile:

```powershell
python scripts/install.py apply
codex
```

```powershell
python scripts/install.py off      # disable this tool's Luna orchestration
python scripts/install.py on       # enable it again
python scripts/install.py status   # inspect status
```

This tool does not pin the Root model or reasoning. It preserves MCP, providers, hooks, permissions, and project configuration. It requires no API key and sends no telemetry. It manages only its own Luna roles and global orchestration managed block.

## Advanced usage

- `sol-luna`, `sol-only`, and `sol-luna-fast` in `profiles/` are Advanced / Legacy Compatibility sources. The installer never installs, overwrites, validates, or removes same-named user profiles. Existing ones only produce a `LEGACY_PROFILE_PRESENT / UNMANAGED` notice. Use `python scripts/install.py off` to disable Luna orchestration; do not disable Codex multi-agent globally.
- Status checks the current TOML, managed blocks, and plugin role files. Later valid Root, MCP, provider, hooks, permissions, or project edits do not trigger plugin drift. Uninstall and later rollback retain those user edits. Failed transactions restore the exact pre-operation bytes.
- Use `sol-luna-fast` only when you explicitly want whole-session Fast. Luna follows Codex child-tier behavior; Standard Root + Luna-only Fast is not supported as a guarantee.
- Luna context-window and auto-compact values are **configured overrides**. Independent runtime context-window telemetry is not currently available.

See [Installation](docs/INSTALL.md), [Switching](docs/SWITCHING.md), [Architecture](docs/ARCHITECTURE.md), and [Compatibility](docs/COMPATIBILITY.md) for details.
