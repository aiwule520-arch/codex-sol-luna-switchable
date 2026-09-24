from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from scripts import install as installer
from scripts import package_release


def _without_region(text: str, begin: str, end: str) -> str:
    if begin not in text:
        return text
    start = text.index(begin)
    finish = text.index(end, start) + len(end)
    if finish == len(text) and start and text[start - 1] == "\n":
        start -= 1
    return text[:start] + text[finish:]


class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "codex-home"
        self.home.mkdir()
        self.config = self.home / "config.toml"
        self.original_config = (
            b'# preserve this CRLF comment\r\n'
            b'model = "user-selected-root"\r\n'
            b'model_reasoning_effort = "medium"\r\n'
            b'service_tier = "fast"\r\n'
            b'approval_policy = "on-request"\r\n'
            b'sandbox_mode = "workspace-write"\r\n'
            b'\r\n[features]\r\nfast_mode = true\r\n'
            b'\r\n[agents]\r\n'
            b'default_subagent_model = "user-agent-choice"\r\n'
            b'default_subagent_reasoning_effort = "medium"\r\n'
            b'max_concurrent_threads_per_session = 9\r\n'
            b'\r\n[agents.custom]\r\ndescription = "keep custom role"\r\n'
            b'\r\n[mcp_servers.keep]\r\ncommand = "keep-mcp"\r\nargs = ["--keep"]\r\n'
            b'\r\n[model_providers.private]\nname = "private provider"\nbase_url = "https://local.invalid"\n'
            b'\n[hooks]\nnotify = ["keep-hook"]\n'
            b'\n[permissions]\ncustom_rule = "keep-permission"\n'
            b'\n[projects."C:\\\\work"]\ntrust_level = "trusted"\n'
        )
        self.config.write_bytes(self.original_config)
        self.override = self.home / "AGENTS.override.md"
        self.original_override = b"# User override\r\nkeep these bytes\r\n"
        self.override.write_bytes(self.original_override)
        self.agents = self.home / "agents"
        self.agents.mkdir()
        self.user_agent = self.agents / "my-agent.toml"
        self.user_agent_bytes = b'model = "user-agent-model"\n'
        self.user_agent.write_bytes(self.user_agent_bytes)
        self.env = mock.patch.dict(os.environ, {"CODEX_HOME": str(self.home)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def version(self, value: str = "codex-cli 0.155.0", triple: tuple[int, int, int] = (0, 155, 0), prerelease: bool = False):
        patcher = mock.patch.object(installer, "_version", return_value=(value, triple, prerelease))
        patcher.start()
        self.addCleanup(patcher.stop)
        schema_patcher = mock.patch.object(installer, "_schema_check", return_value="STRICT_CONFIG_ACCEPTED")
        schema_patcher.start()
        self.addCleanup(schema_patcher.stop)

    def run_cli(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = installer.main(list(args))
        return code, output.getvalue()

    def apply(self) -> None:
        self.version()
        code, output = self.run_cli("apply")
        self.assertEqual(code, 0, output)

    def test_apply_status_off_on_idempotence_and_exact_rollback(self) -> None:
        self.apply()
        installed_config = self.config.read_bytes()
        installed_guidance = self.override.read_bytes()
        manifest_path = self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME
        manifest_bytes = manifest_path.read_bytes()

        parsed = installer.tomllib.loads(installed_config.decode("utf-8"))
        self.assertEqual(parsed["model"], "user-selected-root")
        self.assertEqual(parsed["model_reasoning_effort"], "medium")
        self.assertEqual(parsed["service_tier"], "fast")
        self.assertEqual(parsed["approval_policy"], "on-request")
        self.assertEqual(parsed["sandbox_mode"], "workspace-write")
        self.assertTrue(parsed["features"]["fast_mode"])
        self.assertEqual(parsed["agents"]["default_subagent_model"], "user-agent-choice")
        self.assertEqual(parsed["agents"]["default_subagent_reasoning_effort"], "medium")
        self.assertEqual(parsed["agents"]["max_concurrent_threads_per_session"], 9)
        self.assertEqual(parsed["agents"]["custom"]["description"], "keep custom role")
        self.assertEqual(parsed["mcp_servers"]["keep"]["command"], "keep-mcp")
        self.assertEqual(parsed["model_providers"]["private"]["name"], "private provider")
        self.assertEqual(parsed["hooks"]["notify"], ["keep-hook"])
        self.assertEqual(parsed["permissions"]["custom_rule"], "keep-permission")
        self.assertEqual(parsed["projects"][r"C:\work"]["trust_level"], "trusted")
        self.assertEqual(self.user_agent.read_bytes(), self.user_agent_bytes)
        self.assertEqual(
            _without_region(installed_config.decode("utf-8"), installer.BEGIN, installer.END).encode("utf-8"),
            self.original_config,
        )
        self.assertEqual(
            _without_region(installed_guidance.decode("utf-8"), installer.POLICY_BEGIN, installer.POLICY_END).encode("utf-8"),
            self.original_override,
        )
        self.assertFalse((self.home / "AGENTS.md").exists())
        for name in installer.PROFILES:
            self.assertFalse((self.home / f"{name}.config.toml").exists())

        for role in installer.ROLES:
            role_id = f"csl_luna_{role}"
            self.assertEqual(parsed["agents"][role_id]["config_file"], f"{installer.PLUGIN_DIR}/agents/{role}.toml")
            self.assertTrue((self.home / installer.PLUGIN_DIR / "agents" / f"{role}.toml").is_file())
        for command in (("status",), ("off",), ("off",), ("on",), ("on",), ("status",)):
            code, output = self.run_cli(*command)
            self.assertEqual(code, 0, output)

        self.assertEqual(self.config.read_bytes(), installed_config)
        self.assertEqual(self.override.read_bytes(), installed_guidance)
        self.assertTrue(manifest_path.is_file())
        self.assertEqual(self.user_agent.read_bytes(), self.user_agent_bytes)
        code, output = self.run_cli("rollback")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertEqual(self.override.read_bytes(), self.original_override)
        self.assertFalse(manifest_path.exists())
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())
        self.assertEqual(self.user_agent.read_bytes(), self.user_agent_bytes)
        for name in installer.PROFILES:
            self.assertFalse((self.home / f"{name}.config.toml").exists())

    def test_legacy_profile_is_unmanaged_and_nonblocking(self) -> None:
        target = self.home / "sol-luna.config.toml"
        target.write_bytes(b'# existing user profile\n')
        before_config = self.config.read_bytes()
        before_guidance = self.override.read_bytes()
        self.version()
        code, output = self.run_cli("apply")
        self.assertEqual(code, 0, output)
        code, output = self.run_cli("status")
        self.assertEqual(code, 0, output)
        self.assertIn("LEGACY_PROFILE_PRESENT / UNMANAGED", output)
        self.assertEqual(target.read_bytes(), b'# existing user profile\n')
        self.assertEqual(_without_region(self.config.read_bytes().decode(), installer.BEGIN, installer.END).encode(), before_config)
        self.assertEqual(_without_region(self.override.read_bytes().decode(), installer.POLICY_BEGIN, installer.POLICY_END).encode(), before_guidance)

    def test_user_config_changes_remain_healthy_and_survive_uninstall(self) -> None:
        self.apply()
        text = self.config.read_bytes().decode("utf-8")
        text = text.replace('model = "user-selected-root"', 'model = "later-root"')
        text += '\n[mcp_servers.added_later]\ncommand = "later-mcp"\n'
        text += '\n[model_providers.added_later]\nname = "provider"\n'
        text += '\n[hooks.added_later]\ncommand = "hook"\n'
        text += '\n[permissions.added_later]\nvalue = "allowed"\n'
        text += '\n[projects.added_later]\ntrust_level = "trusted"\n'
        text += '\n[agents.unrelated_later]\ndescription = "custom"\n'
        self.config.write_bytes(text.encode("utf-8"))
        expected = installer._regions(text, installer.BEGIN, installer.END)[0].encode()
        code, output = self.run_cli("status")
        self.assertEqual(code, 0, output)
        code, output = self.run_cli("off")
        self.assertEqual(code, 0, output)
        code, output = self.run_cli("on")
        self.assertEqual(code, 0, output)
        code, output = self.run_cli("rollback")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.config.read_bytes(), expected)

    def test_guidance_change_outside_block_is_not_drift(self) -> None:
        self.apply()
        self.override.write_bytes(self.override.read_bytes() + b'\nUser later guidance.\n')
        code, output = self.run_cli("status")
        self.assertEqual(code, 0, output)
        code, output = self.run_cli("uninstall")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.override.read_bytes(), self.original_override + b'\nUser later guidance.\n')

    def test_managed_policy_change_is_drift(self) -> None:
        self.apply()
        self.override.write_bytes(self.override.read_bytes().replace(b'Root owns', b'Root no longer owns'))
        code, output = self.run_cli("status")
        self.assertEqual(code, 3, output)
        self.assertIn("DRIFT", output)

    def test_transition_write_failures_restore_exact_preimages(self) -> None:
        self.apply()
        manifest_path = self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME
        tracked = [self.config, self.override, manifest_path, *(self.home / installer.PLUGIN_DIR / "agents" / f"{r}.toml" for r in installer.ROLES)]
        original_atomic = installer._atomic
        for command, next_command in (("off", "off"), ("on", "on"), ("uninstall", None)):
            before = {path: path.read_bytes() if path.exists() else None for path in tracked}
            failed = False
            def fail_manifest(path: Path, data: bytes | None, expected: dict) -> None:
                nonlocal failed
                if path == manifest_path and not failed:
                    failed = True
                    original_atomic(path, data, expected)
                    raise OSError("injected manifest write failure")
                original_atomic(path, data, expected)
            with mock.patch.object(installer, "_atomic", side_effect=fail_manifest):
                code, _ = self.run_cli(command)
            self.assertNotEqual(code, 0, command)
            self.assertTrue(failed)
            self.assertEqual({path: path.read_bytes() if path.exists() else None for path in tracked}, before)
            if next_command:
                code, output = self.run_cli(next_command)
                self.assertEqual(code, 0, output)

    def test_recognized_v02_roles_migrate_with_private_namespace(self) -> None:
        tables = ["# prior user config\n[agents]\ndefault_subagent_model = \"keep\"\n"]
        legacy_hashes: dict[str, str] = {}
        for role in installer.ROLES:
            tables.extend((
                f"\n[agents.{role}]\n",
                f"description = {json.dumps(installer.LEGACY_DESCRIPTIONS[role])}\n",
                f"config_file = \"agents/{role}.toml\"\n",
            ))
            legacy_bytes = f"# exact known legacy fixture for {role}\n".encode("utf-8")
            (self.agents / f"{role}.toml").write_bytes(legacy_bytes)
            legacy_hashes[role] = installer._sha(legacy_bytes)
        self.config.write_text("".join(tables), encoding="utf-8")

        with mock.patch.dict(installer.LEGACY_AGENT_SHA256, legacy_hashes):
            self.apply()
        manifest = json.loads((self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertTrue(manifest["legacy_migrated"])
        self.assertIn("exact packaged source SHA256", manifest["legacy_evidence"])
        parsed = installer.tomllib.loads(self.config.read_text(encoding="utf-8"))
        for role in installer.ROLES:
            self.assertNotIn(role, parsed["agents"])
            self.assertIn(f"csl_luna_{role}", parsed["agents"])
            self.assertFalse((self.agents / f"{role}.toml").exists())
        self.assertEqual(parsed["agents"]["default_subagent_model"], "keep")
        self.assertEqual(self.user_agent.read_bytes(), self.user_agent_bytes)

    def test_ambiguous_generic_role_stops_without_mutation(self) -> None:
        self.config.write_bytes(b'[agents.explorer]\ndescription = "someone else"\nconfig_file = "agents/explorer.toml"\n')
        agent_path = self.agents / "explorer.toml"
        agent_path.write_bytes(b'model = "custom"\n')
        before_config = self.config.read_bytes()
        before_agent = agent_path.read_bytes()
        self.version()

        code, output = self.run_cli("apply")
        self.assertEqual(code, 2)
        self.assertIn("AMBIGUOUS_LEGACY_OWNERSHIP", output)
        self.assertEqual(self.config.read_bytes(), before_config)
        self.assertEqual(agent_path.read_bytes(), before_agent)
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())

    def test_explicit_multiagent_disable_and_malformed_toml_stop_cleanly(self) -> None:
        for config in (
            b'[features]\nmulti_agent = false\n',
            b'[agents]\nenabled = false\n',
        ):
            with self.subTest(config=config):
                self.config.write_bytes(config)
                before = self.config.read_bytes()
                self.version()
                code, output = self.run_cli("apply")
                self.assertEqual(code, 2)
                self.assertIn("USER_EXPLICIT_MULTI_AGENT_DISABLE", output)
                self.assertEqual(self.config.read_bytes(), before)
                self.assertFalse((self.home / installer.PLUGIN_DIR).exists())

        self.config.write_bytes(b"value = [not valid TOML\n")
        before = self.config.read_bytes()
        self.version()
        code, output = self.run_cli("apply")
        self.assertEqual(code, 2)
        self.assertIn("MALFORMED_TOML", output)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())

    def test_prerelease_is_warning_but_older_cli_is_refused(self) -> None:
        self.version("codex-cli 0.155.0-alpha.16", (0, 155, 0), True)
        code, output = self.run_cli("plan")
        self.assertEqual(code, 0, output)
        self.assertIn("WARNING_PRERELEASE", output)
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())
        self.assertEqual(self.config.read_bytes(), self.original_config)

        self.version("codex-cli 0.154.9", (0, 154, 9), False)
        code, output = self.run_cli("apply")
        self.assertEqual(code, 2)
        self.assertIn("UNSUPPORTED_CODEX_VERSION", output)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())

    def test_drift_guard_refuses_modified_managed_block_and_rollback(self) -> None:
        self.apply()
        installed = self.config.read_bytes()
        drifted = installed.replace(b"Read-only repository explorer", b"User-modified role description", 1)
        self.assertNotEqual(installed, drifted)
        self.config.write_bytes(drifted)
        code, output = self.run_cli("off")
        self.assertEqual(code, 2)
        self.assertTrue(any(marker in output for marker in ("USER_DRIFT_REFUSED", "MANAGED_ROLE_BLOCK_DRIFT")), output)
        self.assertEqual(self.config.read_bytes(), drifted)

        self.config.write_bytes(installed + b"# concurrent user edit\n")
        drifted_with_user_edit = self.config.read_bytes()
        code, output = self.run_cli("rollback")
        self.assertEqual(code, 2)
        self.assertIn("MANAGED", output)
        self.assertEqual(self.config.read_bytes(), drifted_with_user_edit)
        self.assertTrue((self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME).exists())

    def test_modified_manifest_cannot_escape_codex_home(self) -> None:
        self.apply()
        manifest_path = self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        outside = Path(self.temp.name) / "outside-guidance.md"
        outside.write_text("user-owned bytes\n", encoding="utf-8")
        manifest["active_global_guidance_file"] = str(outside)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        before_config = self.config.read_bytes()
        before_outside = outside.read_bytes()
        self.version()
        code, output = self.run_cli("uninstall")
        self.assertEqual(code, 2)
        self.assertIn("PATH_OUTSIDE_CODEX_HOME", output)
        self.assertEqual(self.config.read_bytes(), before_config)
        self.assertEqual(outside.read_bytes(), before_outside)

    def test_uninstall_removes_only_managed_content_and_preserves_backup(self) -> None:
        self.apply()
        manifest = json.loads((self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME).read_text(encoding="utf-8"))
        backup = Path(manifest["backup_path"])
        self.version()
        code, output = self.run_cli("uninstall")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertEqual(self.override.read_bytes(), self.original_override)
        self.assertEqual(self.user_agent.read_bytes(), self.user_agent_bytes)
        self.assertFalse((self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME).exists())
        self.assertFalse(any((self.home / installer.PLUGIN_DIR / "agents").glob("*.toml")))
        for name in installer.PROFILES:
            self.assertFalse((self.home / f"{name}.config.toml").exists())
        self.assertTrue((backup / "backup-manifest.json").is_file())

    def test_bom_and_missing_final_newline_are_byte_preserved(self) -> None:
        self.config.write_bytes(b'\xef\xbb\xbfmodel = "root-choice"')
        self.override.unlink()
        self.version()
        code, output = self.run_cli("apply")
        self.assertEqual(code, 0, output)
        installed = self.config.read_bytes()
        self.assertTrue(installed.startswith(b"\xef\xbb\xbf"))
        stripped = _without_region(installed.decode("utf-8-sig"), installer.BEGIN, installer.END)
        self.assertEqual(b"\xef\xbb\xbf" + stripped.encode("utf-8"), b'\xef\xbb\xbfmodel = "root-choice"')
        guide = (self.home / "AGENTS.md").read_bytes()
        self.assertIn(installer.POLICY_BEGIN.encode(), guide)
        self.assertFalse(self.override.exists())

    def test_private_namespace_collision_stops_without_changes(self) -> None:
        self.config.write_text('[agents.csl_luna_worker]\ndescription = "user role"\n', encoding="utf-8")
        before = self.config.read_bytes()
        self.version()
        code, output = self.run_cli("apply")
        self.assertEqual(code, 2)
        self.assertIn("PRIVATE_ROLE_COLLISION", output)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())

    def test_unknown_private_namespace_collision_stops_without_changes(self) -> None:
        self.config.write_text('[agents.csl_luna_custom]\ndescription = "another tool"\n', encoding="utf-8")
        before = self.config.read_bytes()
        self.version()
        code, output = self.run_cli("apply")
        self.assertEqual(code, 2)
        self.assertIn("PRIVATE_NAMESPACE_COLLISION", output)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())

    def test_user_drift_in_legacy_role_file_is_preserved(self) -> None:
        tables = ["[agents]\nenabled = true\n"]
        expected_hashes: dict[str, str] = {}
        for role in installer.ROLES:
            tables.extend((
                f"\n[agents.{role}]\n",
                f"description = {json.dumps(installer.LEGACY_DESCRIPTIONS[role])}\n",
                f"config_file = \"agents/{role}.toml\"\n",
            ))
            data = f"known pre-v0.2 package role: {role}\n".encode()
            expected_hashes[role] = installer._sha(data)
            (self.agents / f"{role}.toml").write_bytes(data)
        changed = self.agents / "worker.toml"
        changed.write_bytes(b"user edited legacy worker\n")
        before_roles = {role: (self.agents / f"{role}.toml").read_bytes() for role in installer.ROLES}
        self.config.write_text("".join(tables), encoding="utf-8")
        before_config = self.config.read_bytes()
        with mock.patch.dict(installer.LEGACY_AGENT_SHA256, expected_hashes):
            self.version()
            code, output = self.run_cli("apply")
        self.assertEqual(code, 2)
        self.assertIn("AMBIGUOUS_LEGACY_OWNERSHIP", output)
        self.assertEqual(self.config.read_bytes(), before_config)
        self.assertEqual(
            {role: (self.agents / f"{role}.toml").read_bytes() for role in installer.ROLES},
            before_roles,
        )
        self.assertFalse((self.home / installer.PLUGIN_DIR).exists())

    def test_dotted_quoted_agent_name_is_not_mistaken_for_legacy_table(self) -> None:
        text = '[agents."explorer.custom"]\ndescription = "keep"\nconfig_file = "agents/explorer.toml"\n'
        self.config.write_text(text, encoding="utf-8")
        self.version()
        code, output = self.run_cli("apply")
        self.assertEqual(code, 0, output)
        parsed = installer.tomllib.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(parsed["agents"]["explorer.custom"]["description"], "keep")
        self.assertEqual(_without_region(self.config.read_text(encoding="utf-8"), installer.BEGIN, installer.END), text)

    def test_failed_apply_write_restores_all_preimages(self) -> None:
        self.version()
        original_atomic = installer._atomic
        failed = False
        def fail_on_worker(path: Path, data: bytes | None, expected: dict) -> None:
            nonlocal failed
            if path.resolve() == (self.home / installer.PLUGIN_DIR / "agents" / "worker.toml").resolve() and not failed:
                failed = True
                original_atomic(path, data, expected)
                raise OSError("injected write failure")
            original_atomic(path, data, expected)
        with mock.patch.object(installer, "_atomic", side_effect=fail_on_worker):
            code, output = self.run_cli("apply")
        self.assertEqual(code, 3)
        self.assertTrue(failed)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertEqual(self.override.read_bytes(), self.original_override)
        self.assertFalse((self.home / installer.PLUGIN_DIR / installer.MANIFEST_NAME).exists())

    def test_managed_marker_in_value_is_not_treated_as_a_block(self) -> None:
        marker_text = f'model = "{installer.BEGIN}"\n'
        remainder, found = installer._regions(marker_text, installer.BEGIN, installer.END)
        self.assertEqual(remainder, marker_text)
        self.assertIsNone(found)

    def test_managed_orchestration_update_preserves_outside_bytes(self) -> None:
        before = (
            b"# leading user bytes\r\n"
            + b"<!-- BEGIN codex-sol-luna-switchable managed orchestration -->\r\n"
            + b"old owned policy\r\n"
            + b"<!-- END codex-sol-luna-switchable managed orchestration -->\r\n"
            + b"# trailing user bytes\r\n"
        )
        text = before.decode("utf-8")
        updated, action = installer._replace_region(text, installer.POLICY_BEGIN, installer.POLICY_END, installer._policy())
        remaining, block = installer._regions(updated, installer.POLICY_BEGIN, installer.POLICY_END)
        original_outside, _ = installer._regions(text, installer.POLICY_BEGIN, installer.POLICY_END)
        self.assertEqual(action, "UPDATE")
        self.assertEqual(block, installer._policy())
        self.assertEqual(remaining.encode("utf-8"), original_outside.encode("utf-8"))

    def test_package_release_writes_verified_assets_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            digest, _, sums = package_release.build_and_verify(package_release.ROOT, "0.3.0", output)
            archive = output / "codex-sol-luna-switchable-v0.3.0.zip"
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), digest)
            self.assertEqual((output / "SHA256SUMS.txt").read_text(encoding="utf-8"), sums)
            with zipfile.ZipFile(archive) as zf:
                self.assertIsNone(zf.testzip())

    def test_package_release_dry_run_reopens_and_audits_zip(self) -> None:
        digest, count, sums = package_release.build_and_verify(package_release.ROOT, "0.3.0")
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertGreaterEqual(count, 20)
        self.assertIn(digest, sums)
        self.assertIn("codex-sol-luna-switchable-v0.3.0.zip", sums)


if __name__ == "__main__":
    unittest.main()
