#!/usr/bin/env python3
"""Audit a release ZIP in memory; optionally write verified release assets."""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
FIXED_FILES = (
    "VERSION",
    "README.md",
    "README.en.md",
    "SWITCH.md",
    "CHANGELOG.md",
    "CONFIG_SWITCH_SNIPPET.toml",
    "templates/AGENTS.md",
    "scripts/install.py",
    "scripts/easy_install.py",
    "scripts/validate.py",
    "scripts/package_release.py",
    "scripts/switch-mode.ps1",
    "scripts/switch-mode.sh",
    "docs/INSTALL.md",
    "docs/SWITCHING.md",
    "docs/ARCHITECTURE.md",
    "docs/COMPATIBILITY.md",
    "docs/REQUIREMENT_TEST_MATRIX.md",
)
SECRET_LIKE = re.compile(
    rb"(?i)(?:\bsk-[a-z0-9]{16,}\b|\bgh[pousr]_[a-z0-9]{20,}\b|"
    rb"\bxox[baprs]-[a-z0-9-]{20,}\b|\bBearer\s+[A-Za-z0-9._~+/-]{20,})"
)
LOCAL_USER_PATH = re.compile(rb"(?i)[A-Z]:\\Users\\[^\s\"'<>]+")
REQUIRED = {
    "VERSION", "README.md", "README.en.md", "SWITCH.md", "CHANGELOG.md",
    "templates/AGENTS.md", "scripts/install.py", "scripts/validate.py",
    "scripts/package_release.py", "docs/REQUIREMENT_TEST_MATRIX.md",
}


def _file_list(root: Path) -> list[tuple[str, bytes]]:
    paths = [root / name for name in FIXED_FILES]
    for directory, pattern in (("agents", "*.toml"), ("profiles", "*.config.toml"), ("tests", "test_*.py")):
        paths.extend(sorted((root / directory).glob(pattern)))
    entries: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"required package file missing or unsafe: {path.relative_to(root)}")
        name = path.relative_to(root).as_posix()
        safe = PurePosixPath(name)
        if name in seen or safe.is_absolute() or ".." in safe.parts or "\\" in name:
            raise ValueError(f"unsafe or duplicate package path: {name}")
        if any(part.lower() in {"backups", ".git", ".codex", "__pycache__"} for part in safe.parts):
            raise ValueError(f"private path in package allowlist: {name}")
        content = path.read_bytes()
        if SECRET_LIKE.search(content) or LOCAL_USER_PATH.search(content):
            raise ValueError(f"secret or machine-local path pattern in {name}")
        if path.suffix in {".md", ".py", ".toml", ".sh", ".ps1"}:
            content.decode("utf-8")
        seen.add(name)
        entries.append((name, content))
    missing = REQUIRED - seen
    if missing:
        raise ValueError(f"required package entries missing: {sorted(missing)}")
    return sorted(entries)


def build_and_verify(root: Path, version: str, output_dir: Path | None = None) -> tuple[str, int, str]:
    declared = (root / "VERSION").read_text(encoding="utf-8").strip()
    if version != declared:
        raise ValueError(f"requested version {version} does not match VERSION {declared}")
    entries = _file_list(root)
    if dict(entries)["VERSION"].decode().strip() != version:
        raise ValueError("VERSION package entry mismatch")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, content in entries:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, content)
    archive_bytes = archive.getvalue()
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    archive_name = f"codex-sol-luna-switchable-v{version}.zip"
    sums = f"{archive_hash}  {archive_name}\n"
    parsed_sum, parsed_name = sums.split()
    if parsed_name != archive_name or parsed_sum != hashlib.sha256(archive_bytes).hexdigest():
        raise ValueError("SHA256SUMS validation failed")
    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP entry")
        if zf.testzip() is not None:
            raise ValueError("ZIP CRC validation failed")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                raise ValueError(f"unsafe ZIP entry: {name}")
        contents = {name: zf.read(name) for name in names}
        if contents["VERSION"].decode().strip() != version:
            raise ValueError("VERSION in ZIP is incorrect")
        if set(contents) != {name for name, _ in entries}:
            raise ValueError("ZIP entry list changed during packaging")
        if any(SECRET_LIKE.search(data) or LOCAL_USER_PATH.search(data) for data in contents.values()):
            raise ValueError("secret or machine-local path found after ZIP reopen")
        if any("backup" in name.lower() or "rollout" in name.lower() or "config.toml" == name.lower() for name in contents):
            raise ValueError("private backup, rollout, or user config included")
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / archive_name).write_bytes(archive_bytes)
        (output_dir / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    return archive_hash, len(entries), sums


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-dir", type=Path, help="write the verified ZIP and SHA256SUMS.txt to this directory")
    args = parser.parse_args(argv)
    try:
        digest, count, sums = build_and_verify(ROOT, args.version, args.output_dir)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"PACKAGE_DRY_RUN: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PACKAGE_DRY_RUN: PASS version={args.version} entries={count}")
    print(f"ZIP_SHA256={digest}")
    print(f"SHA256SUMS_VERIFIED={sums.strip()}")
    print("ZIP_REOPEN_CRC_PATH_SECRET_AUDIT=PASS")
    if args.output_dir is None:
        print("No archive or checksum file retained.")
    else:
        print(f"RELEASE_ASSETS_WRITTEN={args.output_dir / f'codex-sol-luna-switchable-v{args.version}.zip'}, {args.output_dir / 'SHA256SUMS.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
