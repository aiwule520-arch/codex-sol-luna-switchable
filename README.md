# Codex Sol/Luna Switchable

Root 模型和 reasoning 由用户在当前 Codex 会话选择；Luna 承担适合委派的执行任务。

普通 v0.3 用户安装一次后直接启动 Codex，**不需要选择 profile**：

```powershell
python scripts/install.py apply
codex
```

```powershell
python scripts/install.py off      # 关闭本工具的 Luna 编排
python scripts/install.py on       # 重新开启
python scripts/install.py status   # 检查状态
```

安装器只管理 `config.toml` 中标记的角色块、全局 AGENTS 文件中标记的编排块，以及插件目录中的角色文件。它不固定 Root model/reasoning，不需要 API key，也不发送 telemetry。MCP、provider、hooks、permissions、projects 和其他用户设置保留。安装后用户对这些设置的有效修改不会触发插件 DRIFT；稍后卸载或 rollback 也会保留这些修改。事务写入失败会恢复该次操作开始前的原始字节。

`profiles/` 中的 `sol-luna`、`sol-only`、`sol-luna-fast` 是 Advanced / Legacy Compatibility 源文件。安装器不会安装、覆盖、校验或卸载用户 `~/.codex/` 中的同名 profile。已有 profile 仅显示 `LEGACY_PROFILE_PRESENT / UNMANAGED` 提醒。日常关闭 Luna 使用 `off`，不要禁用 Codex 全局 multi-agent。

`sol-luna-fast` 是整个 session 的 Fast 选项。当前不保证 Standard Root + Luna-only Fast。Luna context window 和 auto compact 参数是 **configured override**；当前没有独立的运行态 context-window telemetry。

详情：[安装](docs/INSTALL.md)、[切换](docs/SWITCHING.md)、[架构](docs/ARCHITECTURE.md)、[兼容性](docs/COMPATIBILITY.md)。
