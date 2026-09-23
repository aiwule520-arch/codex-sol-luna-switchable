# Changelog

All notable changes are documented here.

## [0.1.0] - 2026-09-23

### Added

- GPT-6 Sol XHigh root profile with GPT-6 Luna role delegation.
- Separate `sol-luna`, `sol-only`, and `sol-luna-fast` Codex profile files.
- Five Luna roles: explorer, researcher, worker, tester, reviewer.
- Role-specific Codex-visible context windows and compact thresholds.
- Cross-platform safe installer with preview, backups, manifest, and status checks.
- One-switch launchers for on/off/fast modes.
- Public-repository documentation, contribution, security, and release policy.
- CI validation and tag-driven GitHub Release workflow.

### Corrected before public release

- Removed the legacy base-config `profile = "..."` switching approach.
- Documented that current Codex child agents inherit the root service tier, so Luna-only Fast is not claimed.
