# 安装与安全边界

需要 Python 3.11+（标准库 `tomllib`）和支持的 Codex CLI。默认安装到用户级 `CODEX_HOME`（通常是 `%USERPROFILE%\\.codex`）；可设置 `CODEX_HOME` 在临时目录测试。

## 日常使用

```powershell
python scripts/install.py apply
python scripts/install.py status
codex
```

以后直接运行 `codex`。Root model 与 reasoning 由你在 Codex 中选择；安装器不固定这两项，也不修改 MCP、providers、hooks、permissions 或项目设置。

## 管理

- `python scripts/install.py plan`：只读预览。
- `python scripts/install.py off`：只移除本工具管理的 Luna 角色注册与全局策略块；不关闭 Codex 全局 multi-agent，不删除角色文件。
- `python scripts/install.py on`：重新启用本工具的 Luna 角色与策略。
- `python scripts/install.py status`：检查安装和文件完整性。
- `python scripts/install.py rollback`：稍后撤销安装器托管块，保留安装后用户修改；写入失败由事务自动恢复精确操作前字节。
- `python scripts/install.py uninstall`：移除本工具管理的内容；检测到无法证明归属或文件漂移时停止。

安装前会备份涉及的文件。任何未知角色冲突、无效 TOML、符号链接或显式 multi-agent 禁用都会阻止 apply。工具优先在用户级 `AGENTS.override.md` 中维护策略；该文件不存在时才使用/创建用户级 `AGENTS.md`。只改标记区域，项目级 instructions 不属于安装范围。

## Advanced / compatibility profiles

日常 ON/OFF 使用安装器的 `on` / `off` 命令。安装器不会管理目标 `CODEX_HOME` 中的三个同名 profile；已有同名文件仅提示 `LEGACY_PROFILE_PRESENT / UNMANAGED`。普通 v0.3 用户不需要 profile。Profiles 仅供有意选择兼容行为的高级用户：

- `sol-luna`：session 启用 multi-agent，不固定 Root model、reasoning 或 tier。
- `sol-only`：该 session 关闭 Codex multi-agent；它不是推荐的 Luna OFF 方法。
- `sol-luna-fast`：整个 session 使用 Fast，不保证只有 Luna 使用 Fast。

Fast 跟随当前 Codex child tier 行为，不提供 Standard Root + Luna-only Fast 保证。
