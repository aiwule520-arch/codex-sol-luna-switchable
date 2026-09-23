# Architecture

```text
User-selected Root model / reasoning
  ├─ GPT-6 Luna High  : explorer
  ├─ GPT-6 Luna High  : researcher
  ├─ GPT-6 Luna XHigh : worker
  ├─ GPT-6 Luna High  : tester
  └─ GPT-6 Luna XHigh : reviewer
       ↓
User-selected Root performs final integration and acceptance
```

The root profile intentionally does **not** set `model` or `model_reasoning_effort`.
The active Codex model selection (plus any lower/higher-precedence user/project configuration)
determines the root.

The root owns ambiguity, architecture, trade-offs, cross-cutting decisions, integration,
and final acceptance.

Luna roles are leaf workers. They do not spawn more agents. Tasks should be bounded,
evidence-oriented, and sized so Luna does not need to re-decide the architecture.

The concurrency cap is four, but the policy prefers one to three useful agents for normal work.

## Compatibility naming

The profile names `sol-luna`, `sol-only`, and `sol-luna-fast` are retained in v0.2.0 so
existing installs and launchers do not break. The names are historical: they no longer
force the root to GPT-6 Sol.
