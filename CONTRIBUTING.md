# Contributing

Contributions are welcome when they improve compatibility, safety, installation, documentation, or measured orchestration behavior.

Before opening a pull request:

1. Keep changes narrowly scoped.
2. Do not add credentials, private logs, or proprietary repository content.
3. Run `python scripts/validate.py`.
4. Run `git diff --check`.
5. Update `CHANGELOG.md` when the change is user-visible.
6. Update `docs/COMPATIBILITY.md` when an upstream Codex assumption changes.

Configuration claims should be backed by current OpenAI Codex source/docs or a reproducible Codex CLI observation.

Please avoid claiming token, cost, speed, or quality savings as guaranteed unless a reproducible benchmark is included.
