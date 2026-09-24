# 架构

## Root 与 Luna

Root 使用用户当前选择的 model 与 reasoning，负责需求、架构、取舍、拆分、整合和最终验收。只有能提供有用的独立证据或 bounded execution 时才委派；简单任务留在 Root。通常使用 1–3 个子代理，且仅并行独立工作。

## 私有角色

安装器使用私有 ID，避免覆盖 Codex built-in 或用户同名 agent：

- `csl_luna_explorer`
- `csl_luna_researcher`
- `csl_luna_worker`
- `csl_luna_tester`
- `csl_luna_reviewer`

角色映射如下：

| Role | Model | Reasoning | Context window | Auto compact |
|---|---|---:|---:|---:|
| Explorer | gpt-6-luna | high | 872000 | 200000 |
| Researcher | gpt-6-luna | high | 872000 | 200000 |
| Worker | gpt-6-luna | xhigh | 872000 | 240000 |
| Tester | gpt-6-luna | high | 872000 | 180000 |
| Reviewer | gpt-6-luna | xhigh | 872000 | 220000 |

Context-window 数值是配置的 **configured override**；没有独立 runtime context-window telemetry，不能描述为独立运行态验证。

角色文件只配置 model、reasoning、context window、auto compact limit 与 developer instructions。没有单独 sandbox、MCP、provider、hooks、approval 或 permissions。只读角色用 instructions 约束行为；所有角色的真实权限继承 parent session。

## Managed state

安装器只管理 config 中标记的私有角色注册、用户级生效 instructions 文件中的 orchestration block、专属角色目录、manifest 和备份。用户级全局 instructions 优先使用 `AGENTS.override.md`，否则使用 `AGENTS.md`。项目级 `AGENTS.md`、Root 设置及所有 managed block 外文本都不属于其写入范围。

ON/OFF 只管理本工具，不更改 Codex 全局 multi-agent。Profiles 是 Advanced / compatibility 入口；Fast profile 作用于整个 session。
