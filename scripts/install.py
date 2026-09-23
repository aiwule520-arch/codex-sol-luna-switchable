#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

PROJECT = "codex-sol-luna-switchable"
MIN_CODEX = (0, 155, 0)

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "profiles"
AGENT_DIR = ROOT / "agents"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

MANAGED = [
    *(("profile", p) for p in sorted(PROFILE_DIR.glob("*.config.toml"))),
    *(("agent", p) for p in sorted(AGENT_DIR.glob("*.toml"))),
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def validate_sources() -> None:
    for _, path in MANAGED:
        with path.open("rb") as f:
            tomllib.load(f)

def codex_version():
    try:
        proc = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=10)
    except (FileNotFoundError, subprocess.SubprocessError):
        return None, "Codex CLI not found"
    text = (proc.stdout or proc.stderr).strip()
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if not m:
        return None, text
    return tuple(map(int, m.groups())), text

def target_for(kind: str, source: Path, home: Path) -> Path:
    if kind == "profile":
        return home / source.name
    return home / "agents" / source.name

def build_plan(home: Path):
    rows = []
    for kind, src in MANAGED:
        dst = target_for(kind, src, home)
        if not dst.exists():
            state = "CREATE"
        elif sha256(src) == sha256(dst):
            state = "KEEP"
        else:
            state = "BACKUP+REPLACE"
        rows.append((state, src, dst))
    return rows

def print_plan(home: Path):
    print(f"CODEX_HOME: {home}")
    for state, src, dst in build_plan(home):
        print(f"{state:14} {dst}")

def apply(home: Path):
    validate_sources()
    version, raw = codex_version()
    if version is None:
        raise SystemExit(f"Cannot verify Codex CLI version: {raw}")
    if version < MIN_CODEX:
        raise SystemExit(
            f"Codex CLI {version[0]}.{version[1]}.{version[2]} is below required 0.155.0"
        )

    home.mkdir(parents=True, exist_ok=True)
    (home / "agents").mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = home / "backups" / PROJECT / stamp
    backed_up = []

    rows = build_plan(home)
    for state, src, dst in rows:
        if state == "BACKUP+REPLACE":
            rel = dst.relative_to(home)
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, backup)
            backed_up.append(str(backup))

    installed = []
    for state, src, dst in rows:
        if state == "KEEP":
            installed.append({"path": str(dst), "sha256": sha256(dst)})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
        installed.append({"path": str(dst), "sha256": sha256(dst)})

    manifest = {
        "project": PROJECT,
        "version": VERSION,
        "installed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "codex_version": raw,
        "backup_root": str(backup_root) if backed_up else None,
        "backups": backed_up,
        "files": installed,
    }
    manifest_path = home / f"{PROJECT}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {PROJECT} {VERSION}")
    print(f"Manifest: {manifest_path}")
    if backed_up:
        print(f"Backups: {backup_root}")
    print("Start with: codex --profile sol-luna")

def status(home: Path):
    manifest_path = home / f"{PROJECT}.manifest.json"
    if not manifest_path.exists():
        print("Status: not installed (manifest missing)")
        return 1
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    bad = 0
    print(f"Installed version: {data.get('version')}")
    for item in data.get("files", []):
        p = Path(item["path"])
        if not p.exists():
            print(f"MISSING  {p}")
            bad += 1
            continue
        actual = sha256(p)
        if actual == item["sha256"]:
            print(f"OK       {p}")
        else:
            print(f"DRIFT    {p}")
            bad += 1
    return 1 if bad else 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["plan", "apply", "status"])
    ap.add_argument("--codex-home", type=Path)
    args = ap.parse_args()

    home = args.codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    home = home.expanduser().resolve()

    validate_sources()

    if args.action == "plan":
        version, raw = codex_version()
        print(f"Codex CLI: {raw}")
        if version is not None and version < MIN_CODEX:
            print("WARNING: Codex CLI is below required 0.155.0")
        print_plan(home)
        return 0
    if args.action == "apply":
        apply(home)
        return 0
    if args.action == "status":
        return status(home)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
