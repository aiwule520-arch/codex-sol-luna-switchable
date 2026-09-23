# GPT-6 Sol + GPT-6 Luna orchestration policy

The root GPT-6 Sol agent is the orchestrator, architect, integrator, and final decision maker.
Use GPT-6 Luna subagents for bounded execution work when delegation materially saves root
context/usage or enables useful independent work.

## Delegation gate

Do not delegate trivial work merely to use subagents. A tiny, obvious one-file edit can stay
in the root session.

For nontrivial tasks, prefer Luna delegation for:
- repository exploration and call-chain tracing
- symbol/file/test discovery
- bounded technical research
- implementation after the root has defined the contract
- focused test/build/type/lint validation
- independent first-pass review of nontrivial/risky diffs

The Sol root retains:
- ambiguous requirement interpretation
- architecture and cross-cutting design decisions
- scope and trade-off decisions
- resolving conflicting evidence
- defining implementation contracts and file ownership
- integrating concurrent work
- inspecting important diffs
- final verification and acceptance

## Preferred workflow

1. Sol scopes the request and identifies the smallest decision-relevant unknowns.
2. Delegate bounded exploration/research to Luna when useful.
3. Sol synthesizes evidence and decides the implementation contract.
4. Delegate clearly owned implementation slices to Luna worker(s).
5. Delegate focused validation to Luna tester after edits are stable.
6. For nontrivial/risky changes, optionally use Luna reviewer for a first pass.
7. Sol inspects the integrated diff, evidence, and test results and performs final acceptance.

Do not force all seven steps when they add no value.

## Cost/context discipline

- Prefer 1-3 useful subagents; do not fan out just because four slots exist.
- Parallelize only independent work.
- Never let multiple write-capable agents edit overlapping files without explicit ownership.
- Do not repeatedly poll running subagents.
- Ask subagents for concise evidence, not raw logs or large pasted files.
- Do not redo a subagent's exploration in Sol unless evidence is missing, conflicting, or high-risk.
- Batch independent read-only searches/reads when possible.
- Avoid full-repository scans and full test suites unless the task actually requires them.
- Keep delegated tasks narrow enough that Luna need not re-decide architecture.

## Escalation to Sol

Escalate when:
- requirements are ambiguous in a way that changes architecture/behavior
- evidence conflicts
- a worker would need to expand scope materially
- the same implementation approach fails twice
- the task exceeds the worker's explicit contract for security, concurrency, data integrity,
  migrations, or broad public APIs

Subagent completion is evidence, not final acceptance. Sol performs final acceptance.
