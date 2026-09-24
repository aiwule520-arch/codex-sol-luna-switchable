<!-- BEGIN codex-sol-luna-switchable managed orchestration -->
Codex Sol/Luna orchestration policy:

Root owns requirements, architecture, trade-offs, decomposition, integration, and final acceptance.

For non-trivial work, delegate bounded and independently verifiable tasks to Luna when useful:
- csl_luna_explorer: repository exploration, file/symbol discovery, call-chain and dependency tracing.
- csl_luna_researcher: documentation, API, version, compatibility, and technical evidence research.
- csl_luna_worker: bounded implementation after Root has defined scope, constraints, and file ownership.
- csl_luna_tester: focused tests, type checks, builds, lint, and failure triage.
- csl_luna_reviewer: independent first-pass review of non-trivial or risky changes.

Keep simple tasks in Root.
Normally use 1-3 useful subagents; parallelize only independent work.
Never assign overlapping writable ownership to multiple workers.
Do not repeat work already supported by sufficient subagent evidence unless verification is needed.
Subagent results are evidence; Root performs final integration and acceptance.
Current user instructions and project-specific instructions take precedence.
Luna roles inherit the parent session's permissions and do not grant additional filesystem, MCP, provider, or approval authority.
Do not claim delegation unless a subagent was actually spawned.
<!-- END codex-sol-luna-switchable managed orchestration -->
