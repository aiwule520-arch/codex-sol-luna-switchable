# Codex Sol/Luna Switchable

一个面向 Codex CLI 的社区配置：保留 **GPT-6 Sol XHigh** 作为主代理，把边界明确的探索、研究、实现、测试和首轮 Review 下放给 **GPT-6 Luna**。

> 独立社区项目，与 OpenAI 无隶属或官方背书关系。模型与 Codex 可用性取决于你的账号、计划、地区和客户端版本。

## 设计目标

默认模式 `sol-luna`：

| 角色 | 模型 | Reasoning | Codex context override | Auto compact |
|---|---|---:|---:|---:|
| Root | GPT-6 Sol | XHigh | Codex 默认 | Codex 默认 |
| Explorer | GPT-6 Luna | High | 872K | 200K |
| Researcher | GPT-6 Luna | High | 872K | 200K |
| Worker | GPT-6 Luna | XHigh | 872K | 240K |
| Tester | GPT-6 Luna | High | 872K | 180K |
| Reviewer | GPT-6 Luna | XHigh | 872K | 220K |

当前 OpenAI Codex 模型目录把 GPT-6 Luna 的默认 context 记为 272K、允许的最大 override 记为 872K，并要求 Codex CLI 0.155.0+。Fast tier 在模型目录中标注为 `1.5x speed`。这些值可能随 Codex 更新而变化，发布前应重新核对上游模型目录。

## 三个模式

```bash
codex --profile sol-luna
codex --profile sol-only
codex --profile sol-luna-fast
```

也可以使用仓库自带的一键启动器：

```bash
codex-mode on
codex-mode off
codex-mode fast
```

`on` 是推荐日常模式；`off` 禁用多代理；`fast` 是当前 Codex 能实际生效的整会话 Fast。由于当前 Codex 会让 child 继承 root 的 service tier，仓库不会声称可以稳定做到 “Sol Standard + Luna-only Fast”。

## 安装

要求：Codex CLI 0.155.0+、Python 3.11+。

先预览：

```bash
python scripts/install.py plan
```

确认后安装：

```bash
python scripts/install.py apply
```

安装器只管理：

```text
$CODEX_HOME/
├── sol-luna.config.toml
├── sol-only.config.toml
├── sol-luna-fast.config.toml
└── agents/
    ├── explorer.toml
    ├── researcher.toml
    ├── worker.toml
    ├── tester.toml
    └── reviewer.toml
```

它**不会修改**现有 `$CODEX_HOME/config.toml`，因此不会碰你的 MCP、provider、permissions、hooks 或其他自定义设置。已有同名文件会先备份。

如果希望某个项目采用仓库里的编排规则，把 `templates/AGENTS.md` 合并到该项目根目录的 `AGENTS.md`。

完整安装说明见 [docs/INSTALL.md](docs/INSTALL.md)，模式切换见 [docs/SWITCHING.md](docs/SWITCHING.md)。

## 验证

```bash
python scripts/install.py status
python scripts/validate.py
```

然后运行：

```bash
codex --profile sol-luna
```

实际 spawn `explorer` 和 `worker`，检查 child session/turn context，确认真正生效的是：

```text
explorer -> gpt-6-luna / high
worker   -> gpt-6-luna / xhigh
root     -> gpt-6-sol  / xhigh
```

不要只根据父代理文字描述判断路由是否生效。

## 为什么不把所有 Luna 都设 Max

这套配置优化的是“把昂贵的 Sol token 留给架构、取舍和最终验收”。Explorer、Researcher、Tester 主要是边界明确的执行工作，High 通常更合适；Worker 和 Reviewer 给 XHigh，以保留较强的实现与审查能力。并发上限设为 4，但正常任务优先使用 1–3 个真正有价值的子代理。

## Fast 的当前限制

Codex CLI 0.153.0 起有已记录行为：自定义 agent 的 `service_tier` 不再独立覆盖 root，child 会跟随 root tier。相关上游 issue：

- openai/codex#42612
- openai/codex#42665

因此：

```text
sol-luna      = Sol Standard + Luna Standard
sol-luna-fast = Sol Fast + Luna Fast
```

当上游恢复 per-child tier override 后，再考虑给 Explorer / Worker / Tester 单独启用 Fast。

## 发布状态

当前公共版本：`v0.1.0`

`0.x` 表示配置仍跟随 Codex 快速演进。发布规则见 [RELEASE_POLICY.md](RELEASE_POLICY.md)，兼容性说明见 [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)。

## 安全与隐私

仓库不需要 API key，也不包含遥测服务。不要把 token、私有代码、客户数据、真实日志或本地配置上传到 issue。安全问题请按 [SECURITY.md](SECURITY.md) 报告。

## License

MIT。详见 [LICENSE](LICENSE)。
