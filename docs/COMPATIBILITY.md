# 兼容性与限制

## CLI 与 Python

角色路由必须由实际 Codex child rollout 的 `turn_context.payload.model` 和 `payload.effort` 验证；版本字符串或 TOML 本身不能证明路由。CLI 低于安装器支持基线时，安装应停止。预发行版本会明确标记 warning。Python 需要 3.11+ 的标准库 `tomllib`。

## Root、permissions 与非干涉

Root model、reasoning、tier、approval、sandbox 和 permissions 都由用户/会话控制。角色文件不配置 sandbox 或权限；Explorer、Researcher、Reviewer 通过 developer instructions 约束为只读，Worker 和 Tester 继承 parent session 权限。

安装器只维护自己的私有 Luna role registrations、专属 role 文件、用户级全局 orchestration managed block、manifest 和备份。必须保留其他 MCP、providers、hooks、permissions、projects、agents 和所有 managed block 外原文。所有权不明确或检测到 drift 时应停止，绝不覆盖。

安装不需要 API key，不启动 telemetry 服务，也不发送 telemetry。

## Profiles 与 Fast

Installer leaves same-named files in `CODEX_HOME` unmanaged and reports them as `LEGACY_PROFILE_PRESENT / UNMANAGED`. Profiles 是 Advanced / Legacy Compatibility 功能，不是日常开关；普通 v0.3 用户不需要 profile：

- 日常使用 `python scripts/install.py apply` 后运行普通 `codex`。
- 使用 `python scripts/install.py off/on` 管理本工具的 Luna 策略。
- `sol-only` 是关闭整个 session multi-agent 的 legacy/advanced profile；不要将其推荐为 Luna OFF。
- `sol-luna-fast` 只表示 whole-session Fast。
- Luna 遵循当前 Codex child tier 行为；不宣传 Standard Root + Luna-only Fast，也不使用未文档化 per-child tier hack。

## Context telemetry

各角色提供 context window 与 auto-compact 配置覆盖（见 Architecture）。如果 rollout 没有提供 context-window runtime telemetry，只能称为 configured override，不能称为 runtime independently verified。
