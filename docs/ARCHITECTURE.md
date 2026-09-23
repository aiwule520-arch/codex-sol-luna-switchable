# Architecture

```text
GPT-6 Sol XHigh
  ├─ Luna High  : explorer
  ├─ Luna High  : researcher
  ├─ Luna XHigh : worker
  ├─ Luna High  : tester
  └─ Luna XHigh : reviewer
       ↓
GPT-6 Sol XHigh final integration and acceptance
```

The root owns ambiguity, architecture, trade-offs, cross-cutting decisions, integration, and final acceptance.

Luna roles are leaf workers. They do not spawn more agents. Tasks should be bounded, evidence-oriented, and sized so Luna does not need to re-decide the architecture.

The concurrency cap is four, but the policy prefers one to three useful agents for normal work.
