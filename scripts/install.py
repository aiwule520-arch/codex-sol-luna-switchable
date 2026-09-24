#!/usr/bin/env python3
"""Install and manage the non-interfering Sol/Luna orchestration layer."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Any


VERSION = "0.3.0"
MIN_VERSION = (0, 155, 0)
BEGIN = "# BEGIN codex-sol-luna-switchable managed roles"
END = "# END codex-sol-luna-switchable managed roles"
POLICY_BEGIN = "<!-- BEGIN codex-sol-luna-switchable managed orchestration -->"
POLICY_END = "<!-- END codex-sol-luna-switchable managed orchestration -->"
PLUGIN_DIR = "codex-sol-luna-switchable"
MANIFEST_NAME = "manifest.json"
BACKUP_ROOT = Path("backups") / "codex-sol-luna-switchable"
ROLES = ("explorer", "researcher", "worker", "tester", "reviewer")
ROLE_IDS = {name: f"csl_luna_{name}" for name in ROLES}
PROFILES = ("sol-luna", "sol-only", "sol-luna-fast")
REASONING = {"explorer": "high", "researcher": "high", "worker": "xhigh", "tester": "high", "reviewer": "xhigh"}
LEGACY_DESCRIPTIONS = {
    "explorer": "Fast read-only repository explorer for bounded code-path, symbol, dependency, and test discovery.",
    "researcher": "Read-only technical researcher for repository evidence, docs, APIs, compatibility, and constraints.",
    "worker": "Implementation worker for a clearly specified, bounded change with explicit file ownership.",
    "tester": "Focused validation agent for tests, type checks, builds, lint, and failure triage.",
    "reviewer": "Independent read-only first-pass code reviewer for nontrivial or risky diffs before root acceptance.",
}
LEGACY_AGENT_SHA256 = {
    "explorer": "8794d6d72524f3e4743357c0930504fc9a52650a5d9906bc2ad3e9538a68bdf7",
    "researcher": "0e3b717f9ee319c3c2e9ff660d2af04fd76eaf8dfdf4994a5c57495e39c94534",
    "worker": "9af7aff824761796ba9d50eb8fd24ce53f3cf7899866779b053f2011b56cbbc8",
    "tester": "de5363ee3369d2ed1f1aa69f39f83f66a4983e2e76ac39dd9a487f8fa908e67e",
    "reviewer": "abfe0e3f24f9a63e7ab523383c9f93fb13b31bd205812ab715123fe2d6133686",
}
ROLE_DESCRIPTIONS = {
    "explorer": "Read-only repository explorer for bounded source and test discovery.",
    "researcher": "Read-only technical researcher for focused evidence gathering.",
    "worker": "Bounded implementation worker with explicit file ownership.",
    "tester": "Focused validation agent for tests and failure triage.",
    "reviewer": "Independent read-only first-pass reviewer for risky changes.",
}


class InstallError(Exception):
    pass


def _home() -> Path:
    raw = os.environ.get("CODEX_HOME")
    if raw is not None and not raw.strip():
        raise InstallError("EMPTY_CODEX_HOME_REFUSED")
    return Path(raw if raw is not None else Path.home() / ".codex").expanduser().resolve()


def _refuse_links(path: Path, home: Path) -> None:
    path = path.resolve(strict=False)
    home = home.resolve()
    try:
        path.relative_to(home)
    except ValueError as exc:
        raise InstallError(f"PATH_OUTSIDE_CODEX_HOME: {path}") from exc
    cursor = path
    while cursor != home:
        if cursor.is_symlink():
            raise InstallError(f"SYMLINK_PATH_REFUSED: {cursor}")
        cursor = cursor.parent


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


def _decode(data: bytes | None) -> str:
    return data.decode("utf-8-sig") if data else ""


def _encode_like(original: bytes | None, text: str) -> bytes:
    encoded = text.encode("utf-8")
    return b"\xef\xbb\xbf" + encoded if original and original.startswith(b"\xef\xbb\xbf") else encoded


def _toml(data: bytes, path: Path) -> dict[str, Any]:
    try:
        value = tomllib.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise InstallError(f"MALFORMED_TOML: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InstallError(f"INVALID_TOML_ROOT: {path}")
    return value


def _version() -> tuple[str, tuple[int, int, int], bool]:
    exe = shutil.which("codex") or shutil.which("codex.cmd")
    if not exe:
        raise InstallError("CODEX_NOT_FOUND")
    try:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallError(f"CODEX_VERSION_FAILED: {exc}") from exc
    output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    match = re.search(r"(?:codex(?:-cli)?\s+)?v?(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?", output, re.I)
    if result.returncode or not match:
        raise InstallError(f"CODEX_VERSION_UNREADABLE: {output}")
    return output, tuple(int(match.group(i)) for i in (1, 2, 3)), bool(match.group(4))


def _source() -> Path:
    return Path(__file__).resolve().parents[1]


def _role_source(role: str) -> Path:
    return _source() / "agents" / f"{role}.toml"


def _schema_check(config_bytes: bytes) -> str:
    """Check local CLI capabilities plus TOML and config_file compatibility without a session."""
    exe = shutil.which("codex") or shutil.which("codex.cmd")
    if not exe:
        raise InstallError("CODEX_NOT_FOUND")
    try:
        result = subprocess.run([exe, "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise InstallError(f"CLI_CAPABILITY_CHECK_FAILED: {exc}") from exc
    help_text = (result.stdout or "") + (result.stderr or "")
    if result.returncode or not all(option in help_text for option in ("--model", "--strict-config")):
        raise InstallError("CLI_REQUIRED_OPTIONS_UNAVAILABLE")
    parsed = _toml(config_bytes, Path("proposed config.toml"))
    for role in ROLES:
        role_data = _source_role_data(role)
        registration = parsed.get("agents", {}).get(ROLE_IDS[role], {})
        if registration.get("config_file") != _config_file(role):
            raise InstallError(f"CLI_CONFIG_FILE_SCHEMA_MISMATCH: {ROLE_IDS[role]}")
    return "CLI_HELP_AND_LOCAL_TOML_SCHEMA_COMPATIBLE"


def _config_path(home: Path) -> Path:
    return home / "config.toml"


def _manifest_path(home: Path) -> Path:
    return home / PLUGIN_DIR / MANIFEST_NAME


def _guidance_path(home: Path) -> Path:
    override = home / "AGENTS.override.md"
    return override if override.exists() else home / "AGENTS.md"


def _role_target(home: Path, role: str) -> Path:
    return home / PLUGIN_DIR / "agents" / f"{role}.toml"


def _profile_source(name: str) -> Path:
    return _source() / "profiles" / f"{name}.config.toml"


def _profile_target(home: Path, name: str) -> Path:
    return home / f"{name}.config.toml"


def _config_file(role: str) -> str:
    return f"{PLUGIN_DIR}/agents/{role}.toml"


def _table_name(line: str) -> tuple[str, ...] | None:
    content = line.rstrip("\r\n")
    quote = ""
    escaped = False
    for i, char in enumerate(content):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = ""
        elif quote == "'":
            if char == "'":
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == "#":
            content = content[:i]
            break
    content = content.strip()
    if not content.startswith("[") or not content.endswith("]") or content.startswith("[["):
        return None
    raw = content[1:-1].strip()
    parts: list[str] = []
    start = 0
    quote = ""
    escaped = False
    for index, char in enumerate(raw):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = ""
        elif quote == "'":
            if char == "'":
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == ".":
            parts.append(raw[start:index].strip())
            start = index + 1
    parts.append(raw[start:].strip())
    decoded: list[str] = []
    for part in parts:
        if part.startswith('"') and part.endswith('"'):
            try:
                decoded.append(json.loads(part))
            except json.JSONDecodeError:
                return None
        elif part.startswith("'") and part.endswith("'"):
            decoded.append(part[1:-1])
        elif re.fullmatch(r"[A-Za-z0-9_-]+", part):
            decoded.append(part)
        else:
            return None
    return tuple(decoded)


def _table_spans(text: str) -> dict[tuple[str, ...], tuple[int, int]]:
    lines = text.splitlines(keepends=True)
    headers: list[tuple[int, tuple[str, ...]]] = []
    for i, line in enumerate(lines):
        name = _table_name(line)
        if name is not None:
            headers.append((i, name))
    spans: dict[str, tuple[int, int]] = {}
    for index, (start, name) in enumerate(headers):
        end = len(lines)
        for next_start, next_name in headers[index + 1 :]:
            if next_name[:len(name)] != name:
                end = next_start
                break
        spans[name] = (start, end)
    return spans


def _remove_tables(text: str, names: set[tuple[str, ...]]) -> str:
    lines = text.splitlines(keepends=True)
    spans = _table_spans(text)
    remove: set[int] = set()
    for table, (start, end) in spans.items():
        if any(table[:len(name)] == name for name in names):
            remove.update(range(start, end))
    return "".join(line for i, line in enumerate(lines) if i not in remove)


def _region_offsets(text: str, begin: str, end: str) -> tuple[int, int] | None:
    lines = text.splitlines(keepends=True)
    starts: list[tuple[int, int, str]] = []
    offset = 0
    for line in lines:
        content = line.rstrip("\r\n")
        if content == begin or content == end:
            starts.append((offset, offset + len(content), content))
        offset += len(line)
    begins = [(start, finish) for start, finish, marker in starts if marker == begin]
    ends = [(start, finish) for start, finish, marker in starts if marker == end]
    if len(begins) != len(ends) or len(begins) > 1:
        raise InstallError(f"MALFORMED_MANAGED_MARKERS: {begin}")
    if not begins:
        return None
    start, _ = begins[0]
    end_start, finish = ends[0]
    if end_start < start:
        raise InstallError(f"MALFORMED_MANAGED_MARKERS: {begin}")
    return start, finish


def _regions(text: str, begin: str, end: str) -> tuple[str, str | None]:
    offsets = _region_offsets(text, begin, end)
    if offsets is None:
        return text, None
    start, finish = offsets
    region_start = start
    # Managed regions are appended with one separator newline at EOF.
    if start > 0 and text[start - 1] == "\n":
        region_start -= 1
    return text[:region_start] + text[finish:], text[start:finish]


def _role_block(home: Path) -> str:
    lines = [BEGIN]
    for role in ROLES:
        role_id = ROLE_IDS[role]
        description = ROLE_DESCRIPTIONS[role]
        lines.extend((f"[agents.{role_id}]", f"description = {json.dumps(description, ensure_ascii=False)}", f"config_file = {json.dumps(_config_file(role))}", ""))
    lines.append(END)
    return "\n".join(lines)


def _source_role_data(role: str) -> dict[str, Any]:
    path = _role_source(role)
    data = path.read_bytes()
    parsed = _toml(data, path)
    if parsed.get("model") != "gpt-6-luna" or parsed.get("model_reasoning_effort") != REASONING[role]:
        raise InstallError(f"SOURCE_ROLE_POLICY_MISMATCH: {role}")
    expected_keys = {"model", "model_reasoning_effort", "model_context_window", "model_auto_compact_token_limit", "developer_instructions"}
    if set(parsed) != expected_keys:
        raise InstallError(f"SOURCE_ROLE_FIELDS_MISMATCH: {role}: {sorted(set(parsed) ^ expected_keys)}")
    return parsed


def _policy() -> str:
    template = _source() / "templates" / "AGENTS.md"
    try:
        text = template.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise InstallError(f"GLOBAL_POLICY_TEMPLATE_MISSING: {template}") from exc
    remainder, block = _regions(text, POLICY_BEGIN, POLICY_END)
    if block is None or remainder.strip():
        raise InstallError(f"GLOBAL_POLICY_TEMPLATE_INVALID: {template}")
    return block


def _replace_region(text: str, begin: str, end: str, body: str | None) -> tuple[str, str]:
    remainder, found = _regions(text, begin, end)
    if body is None:
        return remainder, "REMOVE" if found else "KEEP"
    if found == body:
        return text, "KEEP"
    if found is not None:
        # Replace only a block whose contents are the known prior managed version.
        offsets = _region_offsets(text, begin, end)
        assert offsets is not None
        start, finish = offsets
        return text[:start] + body + text[finish:], "UPDATE"
    return text + "\n" + body, "ADD"


def _managed_config(text: str) -> tuple[str, str | None]:
    return _regions(text, BEGIN, END)


def _block_matches(actual: str | None, expected: str) -> bool:
    return actual is not None and actual.replace("\r\n", "\n") == expected.replace("\r\n", "\n")


def _known_legacy(home: Path, config: dict[str, Any]) -> tuple[bool, list[str]]:
    agents = config.get("agents", {})
    if not isinstance(agents, dict):
        raise InstallError("INVALID_AGENTS_TABLE")
    present = [role for role in ROLES if role in agents]
    if not present:
        return False, []
    if len(present) != len(ROLES):
        raise InstallError("AMBIGUOUS_LEGACY_OWNERSHIP: partial generic role set")
    for role in ROLES:
        item = agents[role]
        if not isinstance(item, dict):
            raise InstallError(f"AMBIGUOUS_LEGACY_OWNERSHIP: agents.{role} shape")
        if item.get("description") != LEGACY_DESCRIPTIONS[role] or item.get("config_file") != f"agents/{role}.toml":
            raise InstallError(f"AMBIGUOUS_LEGACY_OWNERSHIP: agents.{role} metadata mismatch")
        installed = home / "agents" / f"{role}.toml"
        if (home / "agents").is_symlink() or installed.is_symlink():
            raise InstallError(f"AMBIGUOUS_LEGACY_OWNERSHIP: symlink at {installed}")
        if not installed.is_file() or installed.is_symlink() or _sha(installed.read_bytes()) != LEGACY_AGENT_SHA256[role]:
            raise InstallError(f"AMBIGUOUS_LEGACY_OWNERSHIP: agents/{role}.toml source hash mismatch")
    return True, present


def _preflight(home: Path, *, require_version: bool = True) -> dict[str, Any]:
    if require_version:
        output, version, prerelease = _version()
        if version < MIN_VERSION:
            raise InstallError(f"UNSUPPORTED_CODEX_VERSION: {output}; requires >= 0.155.0")
    else:
        output, version, prerelease = "test", MIN_VERSION, False
    config_path = _config_path(home)
    config_bytes = _read(config_path)
    config = _toml(config_bytes, config_path) if config_bytes is not None else {}
    root_agents = config.get("agents", {})
    if isinstance(root_agents, dict) and root_agents.get("enabled") is False:
        raise InstallError("USER_EXPLICIT_MULTI_AGENT_DISABLE: agents.enabled=false")
    features = config.get("features", {})
    if isinstance(features, dict) and features.get("multi_agent") is False:
        raise InstallError("USER_EXPLICIT_MULTI_AGENT_DISABLE: features.multi_agent=false")
    legacy, legacy_roles = _known_legacy(home, config)
    config_text = config_bytes.decode("utf-8-sig") if config_bytes else ""
    remainder, block = _managed_config(config_text)
    del remainder
    manifest_path = _manifest_path(home)
    _refuse_links(manifest_path, home)
    has_manifest = manifest_path.is_file()
    if block is not None and not has_manifest:
        raise InstallError("UNOWNED_MANAGED_ROLE_BLOCK")
    private_ids = [ROLE_IDS[r] for r in ROLES]
    unknown_private_ids = sorted(
        key for key in (root_agents or {})
        if isinstance(key, str) and key.startswith("csl_luna_") and key not in private_ids
    ) if isinstance(root_agents, dict) else []
    if unknown_private_ids:
        raise InstallError(f"PRIVATE_NAMESPACE_COLLISION: {unknown_private_ids}")
    for role_id in private_ids:
        item = (root_agents or {}).get(role_id) if isinstance(root_agents, dict) else None
        if item is not None and block is None:
            raise InstallError(f"PRIVATE_ROLE_COLLISION: agents.{role_id} is outside managed block")
    policy_path = _guidance_path(home)
    _refuse_links(policy_path, home)
    guidance = _read(policy_path)
    policy_text = guidance.decode("utf-8-sig") if guidance else ""
    _, existing_policy = _regions(policy_text, POLICY_BEGIN, POLICY_END)
    if existing_policy is not None and not has_manifest:
        raise InstallError("UNOWNED_MANAGED_ORCHESTRATION_BLOCK")
    plugin_dir = home / PLUGIN_DIR
    _refuse_links(plugin_dir, home)
    manifest = manifest_path
    for role in ROLES:
        target = _role_target(home, role)
        _refuse_links(target, home)
        if target.exists() and not manifest.exists() and target.read_bytes() != _role_source(role).read_bytes():
            raise InstallError(f"ROLE_TARGET_COLLISION: {target}")
    for name in PROFILES:
        _toml(_profile_source(name).read_bytes(), _profile_source(name))
    return {
        "version_output": output,
        "version": version,
        "prerelease": prerelease,
        "config_path": config_path,
        "config_bytes": config_bytes,
        "config": config,
        "legacy": legacy,
        "legacy_roles": legacy_roles,
        "config_text": config_text,
        "managed_block": block,
        "guidance_path": policy_path,
        "guidance_bytes": guidance,
        "plugin_dir": plugin_dir,
        "manifest_path": manifest,
    }


def _snapshot(paths: list[Path]) -> dict[str, dict[str, Any]]:
    result = {}
    for path in paths:
        if path.is_symlink():
            raise InstallError(f"SYMLINK_TARGET_REFUSED: {path}")
        data = _read(path)
        result[str(path)] = {"exists": data is not None, "sha256": _sha(data) if data is not None else None, "data": data}
    return result


def _atomic(path: Path, data: bytes | None, expected: dict[str, Any]) -> None:
    current = _read(path)
    if (current is not None) != expected["exists"] or (current is not None and _sha(current) != expected["sha256"]):
        raise InstallError(f"CONCURRENT_CHANGE: {path}")
    if data is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _backup(home: Path, snapshot: dict[str, dict[str, Any]], nonce: str) -> Path:
    backup_dir = home / BACKUP_ROOT / nonce
    _refuse_links(backup_dir, home)
    if backup_dir.exists() or backup_dir.is_symlink():
        raise InstallError(f"BACKUP_PATH_EXISTS: {backup_dir}")
    backup_dir.mkdir(parents=True)
    files = {}
    for index, (path_string, item) in enumerate(snapshot.items()):
        entry = {"exists": item["exists"], "sha256": item["sha256"]}
        if item["exists"]:
            relative = f"files/{index:02d}.bin"
            backup_file = backup_dir / relative
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            backup_file.write_bytes(item["data"])
            entry["backup_file"] = relative
        files[path_string] = entry
    meta = {"format": 1, "codex_home": str(home), "backup_path": str(backup_dir), "files": files}
    backup_manifest = backup_dir / "backup-manifest.json"
    if backup_manifest.is_symlink():
        raise InstallError("BACKUP_MANIFEST_SYMLINK_REFUSED")
    backup_manifest.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return backup_dir


def _transition(home: Path, manifest: dict[str, Any], writes: dict[Path, bytes | None]) -> None:
    manifest_path = _manifest_path(home)
    expected_current = manifest.get("expected_current")
    if not isinstance(expected_current, dict):
        raise InstallError("EXPECTED_CURRENT_MANIFEST_INVALID")
    _expected_matches(home, {key: value for key, value in expected_current.items() if key != str(manifest_path)})
    for path in [*writes, manifest_path]:
        _refuse_links(path, home)
    snapshot = _snapshot([*writes, manifest_path])
    if snapshot[str(manifest_path)]["sha256"] != manifest.get("_self_sha256"):
        raise InstallError("INSTALL_MANIFEST_CHANGED")
    updated = json.loads(json.dumps(manifest))
    updated.pop("_self_sha256", None)
    for path, data in writes.items():
        if path in {_role_target(home, role) for role in ROLES}:
            updated["expected_current"][str(path)] = {"exists": data is not None, "sha256": _sha(data) if data is not None else None}
    config_path = _config_path(home)
    guidance_path = Path(manifest["active_global_guidance_file"])
    for path, begin, end in ((config_path, BEGIN, END), (guidance_path, POLICY_BEGIN, POLICY_END)):
        before = snapshot[str(path)]["data"]
        after = writes[path]
        if _regions(_decode(before), begin, end)[0] != _regions(_decode(after), begin, end)[0]:
            raise InstallError(f"UNRELATED_BYTES_CHANGED: {path}")
    updated["last_operation_unrelated_config_preserved"] = True
    updated["managed_role_block_sha256"] = _sha(_role_block(home).encode())
    updated["orchestration_block_sha256"] = _sha(_policy().encode())
    updated["historical_config_sha256"] = _sha(writes[config_path])
    updated["historical_guidance_sha256"] = _sha(writes[guidance_path])
    manifest_bytes = (json.dumps(updated, indent=2, sort_keys=True) + "\n").encode()
    for name in PROFILES:
        updated["expected_current"].pop(str(_profile_target(home, name)), None)
    updated["expected_current"].pop(str(config_path), None)
    updated["expected_current"].pop(str(guidance_path), None)
    updated["expected_current"].pop(str(manifest_path), None)
    committed: list[Path] = []
    try:
        for path, data in writes.items():
            active = path
            _atomic(path, data, snapshot[str(path)])
            committed.append(path)
        active = manifest_path
        _atomic(manifest_path, manifest_bytes, snapshot[str(manifest_path)])
        committed.append(manifest_path)
    except Exception:
        _undo_attempted(snapshot, [*committed, active] if active not in committed else committed)
        raise


def _capture_post(paths: list[Path]) -> dict[str, dict[str, Any]]:
    return {str(path): {"exists": (data := _read(path)) is not None, "sha256": _sha(data) if data is not None else None} for path in paths}


def _undo_attempted(snapshot: dict[str, dict[str, Any]], attempted: list[Path]) -> None:
    failures = []
    for path in reversed(attempted):
        before = snapshot[str(path)]["data"]
        current = _read(path)
        if current == before:
            continue
        state = {"exists": current is not None, "sha256": _sha(current) if current is not None else None}
        try:
            _atomic(path, before, state)
        except Exception as exc:
            failures.append(f"{path}: {exc}")
    if failures:
        raise InstallError("TRANSACTION_RESTORE_FAILED: " + "; ".join(failures))


def _expected_matches(home: Path, expected: dict[str, dict[str, Any]]) -> None:
    for path_text, state in expected.items():
        path = Path(path_text)
        if path in (_manifest_path(home), _config_path(home), _guidance_path(home)) or path in {_profile_target(home, n) for n in PROFILES} or path in {home / "agents" / f"{r}.toml" for r in ROLES}:
            continue
        try:
            path.resolve(strict=False).relative_to(home.resolve())
        except ValueError as exc:
            raise InstallError(f"MANIFEST_PATH_OUTSIDE_CODEX_HOME: {path}") from exc
        _refuse_links(path, home)
        data = _read(path)
        if (data is not None) != state.get("exists") or (data is not None and _sha(data) != state.get("sha256")):
            raise InstallError(f"USER_DRIFT_REFUSED: {path}")


def _load_manifest(home: Path) -> dict[str, Any]:
    path = _manifest_path(home)
    _refuse_links(path, home)
    if not path.is_file() or path.is_symlink():
        raise InstallError("INSTALL_MANIFEST_MISSING")
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw.decode("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"INSTALL_MANIFEST_INVALID: {exc}") from exc
    if not isinstance(manifest, dict):
        raise InstallError("INSTALL_MANIFEST_SHAPE_INVALID")
    if manifest.get("format") != 1 or manifest.get("codex_home") != str(home):
        raise InstallError("INSTALL_MANIFEST_IDENTITY_MISMATCH")
    if not isinstance(manifest.get("expected_current"), dict) or not isinstance(manifest.get("backup_path"), str) or not isinstance(manifest.get("active_global_guidance_file"), str):
        raise InstallError("INSTALL_MANIFEST_SHAPE_INVALID")
    if not isinstance(manifest.get("legacy_migrated"), bool):
        raise InstallError("INSTALL_MANIFEST_SHAPE_INVALID")
    guidance = Path(manifest["active_global_guidance_file"])
    _refuse_links(guidance, home)
    base_paths = {str(_config_path(home)), str(guidance), *(str(_role_target(home, role)) for role in ROLES)}
    legacy_paths = {str(home / "agents" / f"{role}.toml") for role in ROLES}
    profile_paths = {str(_profile_target(home, name)) for name in PROFILES}
    observed_paths = set(manifest["expected_current"])
    without_profiles = base_paths
    if manifest["legacy_migrated"]:
        without_profiles |= legacy_paths
    role_paths = {str(_role_target(home, role)) for role in ROLES}
    if observed_paths not in (role_paths, role_paths | legacy_paths, without_profiles, without_profiles | profile_paths, without_profiles | {str(path)}, without_profiles | profile_paths | {str(path)}):
        raise InstallError("INSTALL_MANIFEST_PATH_ALLOWLIST_MISMATCH")
    manifest["_self_sha256"] = _sha(raw)
    return manifest


def _managed_integrity(home: Path, manifest: dict[str, Any]) -> None:
    config_path = _config_path(home)
    data = config_path.read_bytes()
    _toml(data, config_path)
    _, block = _regions(_decode(data), BEGIN, END)
    guide = Path(manifest["active_global_guidance_file"])
    _, policy = _regions(_decode(_read(guide)), POLICY_BEGIN, POLICY_END)
    if manifest.get("managed_role_block_sha256", _sha(_role_block(home).encode())) != _sha(_role_block(home).encode()):
        raise InstallError("MANIFEST_ROLE_BLOCK_HASH_DRIFT")
    if manifest.get("orchestration_block_sha256", _sha(_policy().encode())) != _sha(_policy().encode()):
        raise InstallError("MANIFEST_ORCHESTRATION_HASH_DRIFT")
    if manifest.get("state") == "ON":
        if not _block_matches(block, _role_block(home)):
            raise InstallError("MANAGED_ROLE_BLOCK_DRIFT")
        if not _block_matches(policy, _policy()):
            raise InstallError("MANAGED_GUIDANCE_BLOCK_DRIFT")
    elif block is not None or policy is not None:
        raise InstallError("MANAGED_BLOCK_PRESENT_WHILE_OFF")
    _expected_matches(home, manifest["expected_current"])
    for role in ROLES:
        target = _role_target(home, role)
        if not target.is_file() or _sha(target.read_bytes()) != _sha(_role_source(role).read_bytes()):
            raise InstallError(f"PLUGIN_ROLE_FILE_DRIFT: {role}")


def _plan(home: Path, *, require_version: bool = True) -> dict[str, Any]:
    state = _preflight(home, require_version=require_version)
    legacy_block = _remove_tables(state["config_text"], {("agents", role) for role in ROLES}) if state["legacy"] else state["config_text"]
    proposed, action = _replace_region(legacy_block, BEGIN, END, _role_block(home))
    parsed = _toml(proposed.encode(), state["config_path"])
    for role in ROLES:
        _source_role_data(role)
        role_config = parsed.get("agents", {}).get(ROLE_IDS[role], {})
        if role_config.get("config_file") != _config_file(role):
            raise InstallError(f"PROPOSED_CONFIG_INVALID: {ROLE_IDS[role]}")
    guidance_original = state["guidance_bytes"].decode("utf-8-sig") if state["guidance_bytes"] else ""
    guidance, guidance_action = _replace_region(guidance_original, POLICY_BEGIN, POLICY_END, _policy())
    schema_config = ("[features]\nmulti_agent = true\n\n" + _role_block(home) + "\n").encode("utf-8")
    schema_result = _schema_check(schema_config) if require_version else "MOCKED"
    return {**state, "normalized_config_pre": legacy_block,
            "proposed_config": _encode_like(state["config_bytes"], proposed), "config_action": action,
            "proposed_guidance": _encode_like(state["guidance_bytes"], guidance), "guidance_action": guidance_action,
            "schema_result": schema_result}


def _print_plan(home: Path) -> int:
    try:
        plan = _plan(home)
    except (InstallError, OSError) as exc:
        print(f"STOP: {exc}")
        return 2
    warning = "WARNING_PRERELEASE" if plan["prerelease"] else "PASS"
    print(f"Codex CLI: {plan['version_output']} {warning}")
    print("Root model/reasoning/tier/fast: unchanged")
    print("MCP/provider/hooks/permissions/projects: unchanged")
    print(f"Legacy generic roles: {'OWNED_V0.2_MIGRATION' if plan['legacy'] else 'NONE'}")
    print(f"Private registrations: {plan['config_action']}")
    print(f"Global orchestration: {plan['guidance_action']} ({plan['guidance_path']})")
    print(f"Dedicated role files: {PLUGIN_DIR}/agents/{'{role}'}.toml")
    print("Legacy profiles: UNMANAGED (retained if present)")
    print("Global agent defaults/concurrency/feature switches: unchanged")
    print(f"CLI strict role-schema check: {plan['schema_result']}")
    print("Plan only; no files changed.")
    return 0


def _initial_apply(home: Path, plan: dict[str, Any]) -> int:
    manifest_path: Path = plan["manifest_path"]
    if manifest_path.exists():
        return _turn_on(home)
    if plan["plugin_dir"].exists():
        # Existing non-role files are retained; role target collision was preflighted.
        pass
    config_path: Path = plan["config_path"]
    guidance_path: Path = plan["guidance_path"]
    paths = [config_path, guidance_path, manifest_path, *(_role_target(home, r) for r in ROLES)]
    if plan["legacy"]:
        paths.extend(home / "agents" / f"{role}.toml" for role in ROLES)
    snapshot = _snapshot(paths)
    if snapshot[str(config_path)]["data"] != plan["config_bytes"] or snapshot[str(guidance_path)]["data"] != plan["guidance_bytes"]:
        raise InstallError("CONCURRENT_CHANGE_BEFORE_BACKUP")
    if snapshot[str(manifest_path)]["exists"]:
        raise InstallError("INSTALL_MANIFEST_APPEARED_DURING_PLAN")
    for role in ROLES:
        target_state = snapshot[str(_role_target(home, role))]
        source_bytes = _role_source(role).read_bytes()
        if target_state["exists"] and target_state["data"] != source_bytes:
            raise InstallError(f"ROLE_TARGET_CHANGED_DURING_PLAN: {role}")
        if plan["legacy"]:
            legacy_state = snapshot[str(home / "agents" / f"{role}.toml")]
            if not legacy_state["exists"] or _sha(legacy_state["data"]) != LEGACY_AGENT_SHA256[role]:
                raise InstallError(f"LEGACY_AGENT_CHANGED_DURING_PLAN: {role}")
    nonce = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = _backup(home, snapshot, nonce)
    writes: dict[Path, bytes | None] = {config_path: plan["proposed_config"], guidance_path: plan["proposed_guidance"]}
    for role in ROLES:
        writes[_role_target(home, role)] = _role_source(role).read_bytes()
    if plan["legacy"]:
        for role in ROLES:
            writes[home / "agents" / f"{role}.toml"] = None
    # Manifest is committed last after all managed writes and post-validation.
    changed: list[Path] = []
    try:
        for path, data in writes.items():
            active = path
            _atomic(path, data, snapshot[str(path)])
            changed.append(path)
        post_config = config_path.read_bytes()
        _toml(post_config, config_path)
        if plan["guidance_path"].read_bytes() != plan["proposed_guidance"]:
            raise InstallError("POST_WRITE_GUIDANCE_MISMATCH")
        post_unmanaged, _ = _regions(_decode(post_config), BEGIN, END)
        if _sha(_encode_like(plan["config_bytes"], post_unmanaged)) != _sha(_encode_like(plan["config_bytes"], plan["normalized_config_pre"])):
            raise InstallError("UNRELATED_CONFIG_BYTE_EQUIVALENCE_FAILED")
        managed_paths = [*(_role_target(home, r) for r in ROLES)]
        backup_manifest_data = (backup_path / "backup-manifest.json").read_bytes()
        config_before = _toml(plan["config_bytes"], config_path) if plan["config_bytes"] is not None else {}
        config_after = _toml(plan["proposed_config"], config_path)
        preserve_keys = ("model", "model_reasoning_effort", "service_tier", "approval_policy", "sandbox_mode", "mcp_servers", "model_providers", "hooks", "plugins", "skills", "projects")
        if any(config_before.get(key) != config_after.get(key) for key in preserve_keys):
            raise InstallError("PROTECTED_CONFIG_SEMANTICS_CHANGED")
        fingerprints = {
            key: _sha(json.dumps(config_before.get(key), sort_keys=True, separators=(",", ":")).encode())
            for key in ("mcp_servers", "model_providers", "hooks", "permissions", "projects")
        }
        post_fingerprints = {
            key: _sha(json.dumps(config_after.get(key), sort_keys=True, separators=(",", ":")).encode())
            for key in fingerprints
        }
        if fingerprints != post_fingerprints:
            raise InstallError("PROTECTED_CONFIG_FINGERPRINT_CHANGED")
        manifest = {
            "format": 1,
            "version": VERSION,
            "codex_home": str(home),
            "backup_path": str(backup_path),
            "backup_manifest_sha256": _sha(backup_manifest_data),
            "legacy_migrated": bool(plan["legacy"]),
            "legacy_evidence": "all five known descriptions + config_file paths + exact packaged source SHA256" if plan["legacy"] else None,
            "initial_snapshot": {path: {"exists": item["exists"], "sha256": item["sha256"]} for path, item in snapshot.items()},
            "expected_current": _capture_post(managed_paths),
            "managed_role_block_sha256": _sha(_role_block(home).encode()),
            "orchestration_block_sha256": _sha(_policy().encode()),
            "last_operation_unrelated_config_preserved": True,
            "historical_config_sha256": _sha(post_config),
            "historical_guidance_sha256": _sha(plan["proposed_guidance"]),
            "active_global_guidance_file": str(guidance_path),
            "state": "ON",
        }
        data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        active = manifest_path
        _atomic(manifest_path, data, snapshot[str(manifest_path)])
        changed.append(manifest_path)
    except Exception as exc:
        _undo_attempted(snapshot, [*changed, active] if active not in changed else changed)
        print(f"APPLY_FAILED: {exc}; transaction backup retained at {backup_path}")
        return 3
    print(f"INSTALLED: {PLUGIN_DIR}; backup={backup_path}; manifest={manifest_path}")
    return 0


def _turn_on(home: Path) -> int:
    try:
        manifest = _load_manifest(home)
        _managed_integrity(home, manifest)
        config_path = _config_path(home)
        guidance_path = Path(manifest["active_global_guidance_file"])
        config_data = config_path.read_bytes()
        guidance_data = _read(guidance_path)
        config_text = _decode(config_data)
        _, old_block = _regions(config_text, BEGIN, END)
        if old_block is not None and not _block_matches(old_block, _role_block(home)):
            raise InstallError("MANAGED_ROLE_BLOCK_DRIFT")
        new_config, _ = _replace_region(config_text, BEGIN, END, _role_block(home))
        guide_text = _decode(guidance_data)
        _, old_policy = _regions(guide_text, POLICY_BEGIN, POLICY_END)
        if old_policy is not None and not _block_matches(old_policy, _policy()):
            raise InstallError("MANAGED_GUIDANCE_BLOCK_DRIFT")
        new_guidance, _ = _replace_region(guide_text, POLICY_BEGIN, POLICY_END, _policy())
        writes = {config_path: _encode_like(config_data, new_config), guidance_path: _encode_like(guidance_data, new_guidance)}
        if writes[config_path] == config_data and writes[guidance_path] == guidance_data and manifest.get("state") == "ON":
            print("ON: already enabled")
            return 0
        manifest["state"] = "ON"
        _transition(home, manifest, writes)
        print("ON: private Luna roles and orchestration policy enabled")
        return 0
    except (InstallError, OSError, KeyError, TypeError) as exc:
        print(f"ON_FAILED: {exc}")
        return 2


def _turn_off(home: Path) -> int:
    try:
        manifest = _load_manifest(home)
        _managed_integrity(home, manifest)
        config_path = _config_path(home)
        guidance_path = Path(manifest["active_global_guidance_file"])
        config_data = config_path.read_bytes()
        guidance_data = _read(guidance_path)
        config_text = _decode(config_data)
        remainder, block = _regions(config_text, BEGIN, END)
        if block is not None and not _block_matches(block, _role_block(home)):
            raise InstallError("MANAGED_ROLE_BLOCK_DRIFT")
        guide_text = _decode(guidance_data)
        _, policy = _regions(guide_text, POLICY_BEGIN, POLICY_END)
        if policy is not None and not _block_matches(policy, _policy()):
            raise InstallError("MANAGED_GUIDANCE_BLOCK_DRIFT")
        new_guidance, _ = _replace_region(guide_text, POLICY_BEGIN, POLICY_END, None)
        writes = {config_path: _encode_like(config_data, remainder), guidance_path: _encode_like(guidance_data, new_guidance)}
        if writes[config_path] == config_data and writes[guidance_path] == guidance_data and manifest.get("state") == "OFF":
            print("OFF: already disabled")
            return 0
        manifest["state"] = "OFF"
        _transition(home, manifest, writes)
        print("OFF: removed only Sol/Luna managed registration and policy blocks")
        return 0
    except (InstallError, OSError, KeyError, TypeError) as exc:
        print(f"OFF_FAILED: {exc}")
        return 2


def _apply(home: Path) -> int:
    try:
        plan = _plan(home)
        return _initial_apply(home, plan)
    except (InstallError, OSError) as exc:
        print(f"APPLY_STOP: {exc}")
        return 2


def _load_backup(manifest: dict[str, Any], home: Path) -> tuple[Path, dict[str, Any]]:
    backup_input = Path(manifest["backup_path"])
    _refuse_links(backup_input, home)
    if backup_input.is_symlink():
        raise InstallError("BACKUP_SYMLINK_REFUSED")
    backup = backup_input.resolve(strict=True)
    try:
        backup.relative_to((home / BACKUP_ROOT).resolve(strict=True))
    except ValueError as exc:
        raise InstallError("BACKUP_PATH_OUTSIDE_ALLOWED_ROOT") from exc
    path = backup / "backup-manifest.json"
    if path.is_symlink() or _sha(path.read_bytes()) != manifest.get("backup_manifest_sha256"):
        raise InstallError("BACKUP_MANIFEST_HASH_MISMATCH")
    meta = json.loads(path.read_text(encoding="utf-8"))
    if meta.get("codex_home") != str(home) or Path(meta.get("backup_path", "")).resolve() != backup:
        raise InstallError("BACKUP_MANIFEST_IDENTITY_MISMATCH")
    return backup, meta


def _remove_empty(*dirs: Path) -> None:
    for directory in dirs:
        try:
            directory.rmdir()
        except OSError:
            pass


def _rollback(home: Path) -> int:
    try:
        return _uninstall(home)
    except (InstallError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ROLLBACK_STOP: {exc}")
        return 2


def _uninstall(home: Path) -> int:
    try:
        manifest = _load_manifest(home)
        _managed_integrity(home, manifest)
        config_path = _config_path(home)
        guidance_path = Path(manifest["active_global_guidance_file"])
        config_data = config_path.read_bytes()
        config_text = _decode(config_data)
        new_config, _ = _replace_region(config_text, BEGIN, END, None)
        guidance_data = _read(guidance_path)
        guide_text = _decode(guidance_data)
        new_guidance, _ = _replace_region(guide_text, POLICY_BEGIN, POLICY_END, None)
        writes: dict[Path, bytes | None] = {config_path: _encode_like(config_data, new_config), guidance_path: _encode_like(guidance_data, new_guidance)}
        for role in ROLES:
            writes[_role_target(home, role)] = None
        backup, meta = _load_backup(manifest, home)
        if manifest.get("legacy_migrated"):
            for role in ROLES:
                legacy = home / "agents" / f"{role}.toml"
                if not legacy.exists():
                    entry = meta["files"][str(legacy)]
                    writes[legacy] = (backup / entry["backup_file"]).read_bytes()
        manifest_path = _manifest_path(home)
        _refuse_links(manifest_path, home)
        if _regions(_decode(config_data), BEGIN, END)[0] != _regions(_decode(writes[config_path]), BEGIN, END)[0]:
            raise InstallError("UNRELATED_CONFIG_BYTES_CHANGED")
        if _regions(_decode(guidance_data), POLICY_BEGIN, POLICY_END)[0] != _regions(_decode(writes[guidance_path]), POLICY_BEGIN, POLICY_END)[0]:
            raise InstallError("UNRELATED_GUIDANCE_BYTES_CHANGED")
        snapshot = _snapshot([*writes, manifest_path])
        if snapshot[str(manifest_path)]["sha256"] != manifest["_self_sha256"]:
            raise InstallError("INSTALL_MANIFEST_CHANGED")
        committed: list[Path] = []
        try:
            for path, data in writes.items():
                active = path
                _atomic(path, data, snapshot[str(path)])
                committed.append(path)
            active = manifest_path
            _atomic(manifest_path, None, snapshot[str(manifest_path)])
            committed.append(manifest_path)
        except Exception:
            _undo_attempted(snapshot, [*committed, active] if active not in committed else committed)
            raise
        _remove_empty(home / PLUGIN_DIR / "agents", home / PLUGIN_DIR)
        print("UNINSTALLED: removed only managed role/policy blocks and dedicated role files")
        print(f"Migration backup retained at {manifest['backup_path']}")
        return 0
    except (InstallError, OSError, KeyError, TypeError) as exc:
        print(f"UNINSTALL_STOP: {exc}")
        return 2


def _status(home: Path) -> int:
    try:
        manifest = _load_manifest(home)
        config_data = _config_path(home).read_bytes()
        _toml(config_data, _config_path(home))
        text = _decode(config_data)
        _, block = _regions(text, BEGIN, END)
        guide_path = Path(manifest["active_global_guidance_file"])
        guide_data = _read(guide_path)
        _, policy = _regions(_decode(guide_data), POLICY_BEGIN, POLICY_END)
        unrelated_ok = manifest.get("last_operation_unrelated_config_preserved") is True
        files_ok = all(_role_target(home, role).is_file() and _sha(_role_target(home, role).read_bytes()) == _sha(_role_source(role).read_bytes()) for role in ROLES)
        legacy_profiles = [name for name in PROFILES if _profile_target(home, name).exists()]
        on = _block_matches(block, _role_block(home)) and _block_matches(policy, _policy())
        cli = _version()[0]
        try:
            _managed_integrity(home, manifest)
            integrity = "OK"
        except InstallError as exc:
            integrity = "DRIFT"
            print(f"Managed integrity detail: {exc}")
        print(f"Luna runtime roles: {'ON' if on else 'OFF' if block is None and policy is None else 'PARTIAL'}")
        print(f"Global orchestration: {'ON' if _block_matches(policy, _policy()) else 'OFF' if policy is None else 'DRIFT'}")
        print(f"Role files: {'OK' if files_ok else 'DRIFT/MISSING'}")
        print(f"Legacy profiles: {'LEGACY_PROFILE_PRESENT / UNMANAGED: ' + ', '.join(legacy_profiles) if legacy_profiles else 'NONE'}")
        print(f"Legacy installation: {'MIGRATED' if manifest.get('legacy_migrated') else 'NONE'}")
        print(f"Codex CLI: {cli}")
        print(f"Config integrity: {integrity}")
        print(f"Last operation unrelated config preserved: {'YES' if unrelated_ok else 'UNKNOWN'}")
        print(f"Historical whole config SHA changed: {'YES' if _sha(config_data) != manifest.get('historical_config_sha256', manifest.get('expected_current', {}).get(str(_config_path(home)), {}).get('sha256')) else 'NO'} (audit only)")
        return 0 if integrity == "OK" and files_ok else 3
    except (InstallError, OSError, KeyError, TypeError) as exc:
        print(f"STATUS_FAILED: {exc}")
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "on", "off", "status", "rollback", "uninstall"))
    args = parser.parse_args(argv)
    try:
        home = _home()
        if args.command == "plan":
            return _print_plan(home)
        if args.command == "apply":
            return _apply(home)
        if args.command == "on":
            return _turn_on(home)
        if args.command == "off":
            return _turn_off(home)
        if args.command == "status":
            return _status(home)
        if args.command == "rollback":
            return _rollback(home)
        return _uninstall(home)
    except InstallError as exc:
        print(f"STOP: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
