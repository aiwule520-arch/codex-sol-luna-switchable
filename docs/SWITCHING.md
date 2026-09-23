# Switching modes

Recent Codex releases use profile files under `$CODEX_HOME` and select them with `--profile`.

Use:

```bash
codex --profile sol-luna
codex --profile sol-only
codex --profile sol-luna-fast
```

The old pattern of putting `profile = "..."` or `[profiles.*]` in the base `config.toml` is legacy in current Codex and is not used by this project.

## One-switch launcher

Unix/macOS:

```bash
./bin/codex-mode on
./bin/codex-mode off
./bin/codex-mode fast
```

PowerShell:

```powershell
.\bin\codex-mode.ps1 on
.\bin\codex-mode.ps1 off
.\bin\codex-mode.ps1 fast
```

Any extra arguments are forwarded to Codex.

Examples:

```bash
./bin/codex-mode on --search
./bin/codex-mode off -C /path/to/repo
```

## Fast semantics

At the time of this release, child agents follow the root service tier in current Codex multi-agent builds. Therefore `fast` is a whole-session choice.

The project will only advertise Luna-only Fast after upstream Codex supports a verified per-child tier override again.
