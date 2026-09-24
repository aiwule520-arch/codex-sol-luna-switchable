# 开启、关闭与检查

安装后日常直接启动：

```powershell
codex
```

使用安装器控制本工具的 Luna 编排：

```powershell
python scripts/install.py status
python scripts/install.py off
python scripts/install.py on
```

`off` 只关闭本工具的五个 `csl_luna_*` 注册与全局策略块；它不关闭 Codex 全局 multi-agent，也不删除角色文件。重新运行 `on` 即可恢复。不要用 `sol-only` profile 代替 OFF，因为它会关闭整个 session 的 Codex multi-agent。

## Advanced profiles

Installer 不管理 `CODEX_HOME` 中的同名 profile。`profiles/` 仅提供 Advanced / Legacy Compatibility 源文件；用户自行配置后，显式运行 `codex --profile <name>` 才会使用：

- `sol-luna`：multi-agent session，不固定 Root model、reasoning 或 tier。
- `sol-only`：legacy/advanced compatibility；整个 session 禁用 multi-agent。
- `sol-luna-fast`：整个 session Fast。当前 Luna 遵循 Codex child tier 行为，不是 Luna-only Fast。

profiles 不取代安装器日常开关。开启 Fast 前确认你希望整个 session 使用 Fast。
