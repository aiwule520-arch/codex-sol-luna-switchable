# Changelog

## 0.3.0

- Root model and reasoning remain selected by the user; normal launch is plain `codex`.
- Added private `csl_luna_*` roles, dedicated role files, and scoped managed orchestration.
- Preserved configured Luna model, reasoning, context-window overrides, and auto-compact limits.
- Added guarded plan/apply/on/off/status/rollback/uninstall behavior and non-interference checks.
- Clarified that OFF uses the installer, `sol-only` is legacy/advanced compatibility, and Fast is whole-session.
- Added local release packaging dry-run and requirement-to-test coverage matrix.

## [0.2.1] - 2026-09-23

### Fixed

- Removed hard-coded GPT-6 Sol root references from Luna agent prompts.
- Made the orchestration template fully root-model-agnostic.
- Documented multi-agent compatibility requirements for user-selected root models.
- Strengthened validation against future root-model hard-coding.
- Updated GitHub Actions runtime dependencies to actions/checkout@v7 and actions/setup-python@v7.

## [0.2.0] - 2026-09-23

### Changed

- Root model and reasoning are no longer pinned by any project profile.
- The active Codex model selection/config now determines the root model and reasoning.
- GPT-6 Luna named agents remain pinned to the same High/XHigh role configuration.
- Existing `sol-luna`, `sol-only`, and `sol-luna-fast` profile names are retained for backward compatibility.
- Documentation now distinguishes root model selection from Luna worker routing.

### Compatibility

- Existing launch commands continue to work.
- Users with explicit `model` / `model_reasoning_effort` in other Codex config layers may still see picker-precedence behavior from Codex itself.

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
