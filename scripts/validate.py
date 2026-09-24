#!/usr/bin/env python3
"""Validate the local Sol/Luna candidate without reading or changing CODEX_HOME."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

from install import REASONING, ROLES, VERSION, _policy, _role_block, _source_role_data


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COMPACT = {"explorer": 200000, "researcher": 200000, "worker": 240000, "tester": 180000, "reviewer": 220000}
ALLOWED_ROLE_KEYS = {"model", "model_reasoning_effort", "model_context_window", "model_auto_compact_token_limit", "developer_instructions"}
FORBIDDEN_ROOT_MODEL_PHRASES = ("gpt-6 sol root", "sol root orchestrator")
SECRET_LIKE = re.compile(r"(?i)(?:\bsk-[a-z0-9]{16,}\b|\bgh[pousr]_[a-z0-9]{20,}\b|\bxox[baprs]-[a-z0-9-]{20,}\b)")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    check((ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION == "0.3.0", "VERSION mismatch")
    check((ROOT / "CHANGELOG.md").is_file(), "CHANGELOG.md missing")
    policy_files = [*(ROOT / "agents" / f"{role}.toml" for role in ROLES), ROOT / "templates" / "AGENTS.md"]
    for path in policy_files:
        policy_text = path.read_text(encoding="utf-8-sig").lower()
        for phrase in FORBIDDEN_ROOT_MODEL_PHRASES:
            check(phrase not in policy_text, f"{path.relative_to(ROOT)}: Root model is hard-coded as Sol")
    for role in ROLES:
        data = _source_role_data(role)
        check(set(data) == ALLOWED_ROLE_KEYS, f"{role}: unexpected role fields")
        check(data["model"] == "gpt-6-luna", f"{role}: wrong model")
        check(data["model_reasoning_effort"] == REASONING[role], f"{role}: wrong reasoning")
        check(data["model_context_window"] == 872000, f"{role}: context changed")
        check(data["model_auto_compact_token_limit"] == EXPECTED_COMPACT[role], f"{role}: compact limit changed")
        if role in {"explorer", "researcher", "reviewer"}:
            check("Do not edit files." in data["developer_instructions"], f"{role}: missing read-only instruction")
    block = _role_block(ROOT)
    parsed = tomllib.loads("\n".join(("[agents]", "enabled = true", block.replace("# BEGIN codex-sol-luna-switchable managed roles\n", "").replace("# END codex-sol-luna-switchable managed roles", ""))))
    for role in ROLES:
        role_id = f"csl_luna_{role}"
        check(parsed["agents"][role_id]["config_file"] == f"codex-sol-luna-switchable/agents/{role}.toml", f"{role}: invalid config_file")

    profiles = {
        "sol-luna": "profiles/sol-luna.config.toml",
        "sol-only": "profiles/sol-only.config.toml",
        "sol-luna-fast": "profiles/sol-luna-fast.config.toml",
    }
    for name, relative in profiles.items():
        profile = tomllib.loads((ROOT / relative).read_text(encoding="utf-8"))
        check("model" not in profile and "model_reasoning_effort" not in profile, f"{name}: Root model is pinned")
        agents = profile.get("agents", {})
        check(not isinstance(agents, dict) or not any(k in agents for k in ("default_subagent_model", "default_subagent_reasoning_effort", "max_concurrent_threads_per_session")), f"{name}: global agent defaults changed")
        check(profile.get("features", {}).get("multi_agent") is (name != "sol-only"), f"{name}: unexpected advanced multi-agent setting")
        if name == "sol-luna":
            check("service_tier" not in profile and profile.get("features", {}).get("fast_mode") is not True, "daily profile enables tier/Fast")
        if name == "sol-luna-fast":
            check(profile.get("service_tier") == "fast", "fast profile must be whole-session Fast")

    docs = [ROOT / "README.md", ROOT / "README.en.md", ROOT / "SWITCH.md", *(ROOT / "docs" / f for f in ("INSTALL.md", "SWITCHING.md", "ARCHITECTURE.md", "COMPATIBILITY.md", "REQUIREMENT_TEST_MATRIX.md"))]
    for path in docs:
        check(path.is_file(), f"missing documentation: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        check("codex" in text.lower(), f"{path.name}: Codex launch guidance missing")
    for path in (ROOT / "README.md", ROOT / "README.en.md", ROOT / "docs" / "INSTALL.md"):
        text = path.read_text(encoding="utf-8")
        check("scripts/install.py apply" in text, f"{path.name}: install command missing")
    for path in (ROOT / "README.md", ROOT / "README.en.md", ROOT / "docs" / "ARCHITECTURE.md", ROOT / "docs" / "COMPATIBILITY.md"):
        check("configured override" in path.read_text(encoding="utf-8"), f"{path.name}: context telemetry wording missing")
    switch = (ROOT / "SWITCH.md").read_text(encoding="utf-8")
    check("[docs/SWITCHING.md]" in switch and "profile-v2" in switch, "SWITCH.md must point to profile-v2 guidance")
    template = (ROOT / "templates" / "AGENTS.md").read_text(encoding="utf-8-sig")
    check(template.strip() == _policy(), "managed policy template differs from installer policy")
    matrix = (ROOT / "docs" / "REQUIREMENT_TEST_MATRIX.md").read_text(encoding="utf-8")
    check(len(re.findall(r"(?m)^\| R\d{2} \|", matrix)) == 30, "requirement-to-test matrix must define 30 scenarios")
    check((ROOT / "scripts" / "package_release.py").is_file(), "release dry-run tool missing")
    all_text = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".py", ".toml", ".md"})
    check(not SECRET_LIKE.search(all_text), "secret-like token detected")
    check(POLICY_BEGIN in _policy() and POLICY_END in _policy(), "managed policy marker mismatch")
    print("V030 static validation: PASS")
    print("- Root model/reasoning not pinned by profiles")
    print("- Luna roles, reasoning, context, and compact values: PASS")
    print("- Private config_file paths and role field allowlist: PASS")
    print("- Global defaults/concurrency omitted from profiles: PASS")
    print("- Daily profile has no tier/Fast override; Fast profile is whole-session: PASS")
    print("- Documentation and secret-like scan: PASS")
    return 0


POLICY_BEGIN = "<!-- BEGIN codex-sol-luna-switchable managed orchestration -->"
POLICY_END = "<!-- END codex-sol-luna-switchable managed orchestration -->"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"V030 validation: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
