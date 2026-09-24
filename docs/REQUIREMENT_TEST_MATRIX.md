# v0.3.0 Requirement-to-test coverage matrix

The 30 acceptance scenarios below map to executable tests, static validation, or the recorded real-install/runtime checks. This is a coverage map, not a claim that every environment-dependent scenario is a unit test.

| ID | Acceptance scenario | Evidence |
|---|---|---|
| R01 | Root model and reasoning remain unchanged | `test_apply_status_off_on_idempotence_and_exact_rollback`; PRE/POST config fingerprints |
| R02 | Root tier, Fast, approval, and sandbox settings are preserved | `test_apply_status_off_on_idempotence_and_exact_rollback` |
| R03 | MCP, providers, hooks, permissions, and projects are preserved | `test_apply_status_off_on_idempotence_and_exact_rollback`; PRE/POST semantic fingerprints |
| R04 | Unrelated user agent config remains byte-equivalent | `test_apply_status_off_on_idempotence_and_exact_rollback` |
| R05 | Repeated apply is idempotent | `test_apply_status_off_on_idempotence_and_exact_rollback` |
| R06 | Repeated ON is idempotent | `test_apply_status_off_on_idempotence_and_exact_rollback` |
| R07 | Repeated OFF is idempotent | `test_apply_status_off_on_idempotence_and_exact_rollback` |
| R08 | OFF does not disable Codex global multi-agent or remove custom agents | `test_apply_status_off_on_idempotence_and_exact_rollback` |
| R09 | Later rollback removes managed content and preserves later user edits | `test_user_config_changes_remain_healthy_and_survive_uninstall` |
| R10 | Uninstall removes only managed content and retains backup | `test_uninstall_removes_only_managed_content_and_preserves_backup` |
| R11 | Malformed TOML fails closed without mutation | `test_explicit_multiagent_disable_and_malformed_toml_stop_cleanly` |
| R12 | Explicit multi-agent disable fails closed | `test_explicit_multiagent_disable_and_malformed_toml_stop_cleanly` |
| R13 | Proven legacy roles migrate into private IDs | `test_recognized_v02_roles_migrate_with_private_namespace` |
| R14 | Ambiguous legacy role ownership fails closed | `test_ambiguous_generic_role_stops_without_mutation` |
| R15 | User-drifted legacy role files are preserved | `test_user_drift_in_legacy_role_file_is_preserved` |
| R16 | Role model, reasoning, context, compact, and key allowlist are exact | `scripts/validate.py` |
| R17 | Collision on a registered private role ID fails closed | `test_private_namespace_collision_stops_without_changes` |
| R18 | Unknown `csl_luna_*` namespace collision fails closed | `test_unknown_private_namespace_collision_stops_without_changes` |
| R19 | Quoted dotted user agent names are not mistaken for legacy tables | `test_dotted_quoted_agent_name_is_not_mistaken_for_legacy_table` |
| R20 | BOM, CRLF, and missing-final-newline content is preserved | `test_bom_and_missing_final_newline_are_byte_preserved`; primary lifecycle test |
| R21 | A marker-like string value is not treated as a managed block | `test_managed_marker_in_value_is_not_treated_as_a_block` |
| R22 | Failed apply/on/off/uninstall transaction restores exact pre-operation bytes | `test_failed_apply_write_restores_all_preimages`; `test_transition_write_failures_restore_exact_preimages` |
| R23 | Installed `config_file` paths resolve under `CODEX_HOME` | `scripts/validate.py`; isolated lifecycle; real install status |
| R24 | Roles contain no MCP/provider/hooks/permission/sandbox overrides | `scripts/validate.py` |
| R25 | Advanced profiles do not pin Root or alter global subagent defaults; installer leaves user profiles unmanaged | `scripts/validate.py`; `test_legacy_profile_is_unmanaged_and_nonblocking` |
| R26 | OFF, `sol-only`, and whole-session Fast guidance is accurate | README and docs review; `scripts/validate.py`; legacy `SWITCH.md` replaced by profile-v2 pointer |
| R27 | `templates/AGENTS.md` matches the installer policy source | `scripts/validate.py` |
| R28 | Updating orchestration changes only the managed region | `test_managed_orchestration_update_preserves_outside_bytes`; real POST byte comparison |
| R29 | ZIP paths, duplicates, CRC, version, SHA256SUMS, secrets, and local paths are audited | `test_package_release_dry_run_reopens_and_audits_zip`; `scripts/package_release.py --version 0.3.0` |
| R30 | Minimum CLI version is enforced and prerelease is surfaced | `test_prerelease_is_warning_but_older_cli_is_refused` |

The source directory is not a Git repository, so Git diff/staging checks are not applicable. Real child routing is validated separately from these static/package scenarios using each child rollout's effective `turn_context` metadata.

## Shared-config ownership closure (A-J)

| Gate | Evidence |
|---|---|
| A-D: later Root, MCP, provider, hooks, permissions, projects, and unrelated agent edits keep status OK | `test_user_config_changes_remain_healthy_and_survive_uninstall` |
| E: managed role block edit reports DRIFT | `test_drift_guard_refuses_modified_managed_block_and_rollback` |
| F: managed orchestration block edit reports DRIFT | `test_managed_policy_change_is_drift` |
| G-H: later user edits survive uninstall/rollback | `test_user_config_changes_remain_healthy_and_survive_uninstall`; `test_guidance_change_outside_block_is_not_drift` |
| I: existing different legacy profile is warning only | `test_legacy_profile_is_unmanaged_and_nonblocking` |
| J: apply/on/off/uninstall write failure restores exact PRE bytes | `test_failed_apply_write_restores_all_preimages`; `test_transition_write_failures_restore_exact_preimages` |
