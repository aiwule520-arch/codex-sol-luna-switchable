#!/usr/bin/env python3
from pathlib import Path
import sys, tomllib

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    with path.open("rb") as f:
        return tomllib.load(f)

errors = []

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "0.2.1":
    errors.append(f"unexpected VERSION: {version}")

profiles = {
    p.name: load(p) for p in (ROOT / "profiles").glob("*.config.toml")
}
agents = {
    p.name: load(p) for p in (ROOT / "agents").glob("*.toml")
}

required_profiles = {"sol-luna.config.toml", "sol-only.config.toml", "sol-luna-fast.config.toml"}
if set(profiles) != required_profiles:
    errors.append(f"profile set mismatch: {sorted(profiles)}")

required_agents = {"explorer.toml","researcher.toml","worker.toml","tester.toml","reviewer.toml"}
if set(agents) != required_agents:
    errors.append(f"agent set mismatch: {sorted(agents)}")

daily = profiles.get("sol-luna.config.toml", {})
if daily.get("service_tier") != "default":
    errors.append("daily root service tier must be default")

for profile_name, cfg in profiles.items():
    if "model" in cfg:
        errors.append(f"{profile_name}: root model must remain user-selectable (remove model)")
    if "model_reasoning_effort" in cfg:
        errors.append(f"{profile_name}: root reasoning must remain user-selectable (remove model_reasoning_effort)")

fast = profiles.get("sol-luna-fast.config.toml", {})
if fast.get("service_tier") != "fast":
    errors.append("fast profile must request fast service tier")

off = profiles.get("sol-only.config.toml", {})
if off.get("agents", {}).get("enabled") is not False:
    errors.append("sol-only must disable agents")

for name, cfg in agents.items():
    if cfg.get("model") != "gpt-6-luna":
        errors.append(f"{name}: model must be gpt-6-luna")
    if cfg.get("model_context_window") != 872000:
        errors.append(f"{name}: context must be 872000")
    if "service_tier" in cfg:
        errors.append(f"{name}: role-level service_tier must remain unset while upstream inheritance applies")

expected_effort = {
    "explorer.toml": "high",
    "researcher.toml": "high",
    "worker.toml": "xhigh",
    "tester.toml": "high",
    "reviewer.toml": "xhigh",
}
for name, effort in expected_effort.items():
    if agents.get(name, {}).get("model_reasoning_effort") != effort:
        errors.append(f"{name}: expected reasoning {effort}")

expected_compact = {
    "explorer.toml": 200000,
    "researcher.toml": 200000,
    "worker.toml": 240000,
    "tester.toml": 180000,
    "reviewer.toml": 220000,
}
expected_sandbox = {
    "explorer.toml": "read-only",
    "researcher.toml": "read-only",
    "worker.toml": "workspace-write",
    "tester.toml": "workspace-write",
    "reviewer.toml": "read-only",
}
for name in required_agents:
    if agents.get(name, {}).get("model_auto_compact_token_limit") != expected_compact[name]:
        errors.append(f"{name}: unexpected auto compact threshold")
    if agents.get(name, {}).get("sandbox_mode") != expected_sandbox[name]:
        errors.append(f"{name}: unexpected sandbox mode")

forbidden_root_phrases = [
    "GPT-6 Sol root",
    "GPT-6 Sol root orchestrator",
    "the GPT-6 Sol root",
]
prompt_files = list((ROOT / "agents").glob("*.toml")) + [ROOT / "templates" / "AGENTS.md"]
for path in prompt_files:
    text = path.read_text(encoding="utf-8").lower()
    for phrase in forbidden_root_phrases:
        if phrase.lower() in text:
            errors.append(f"{path.relative_to(ROOT)} contains forbidden root-model phrase: {phrase}")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "dist" in path.parts:
        continue
    if path.suffix.lower() in {".md",".toml",".py",".sh",".ps1",".yml",".yaml",".txt"} or path.name in {"LICENSE","VERSION",".gitignore",".gitattributes"}:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # Construct signatures so this validator does not flag its own source.
        forbidden = [
            "s" + "k-",
            "OPENAI_" + "API_KEY=",
            "g" + "hp_",
        ]
        for token in forbidden:
            if token in text:
                errors.append(f"{path.relative_to(ROOT)} contains forbidden secret-like token {token}")

if errors:
    print("VALIDATION FAILED")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("VALIDATION OK")
print(f"profiles={len(profiles)} agents={len(agents)} version={version}")
