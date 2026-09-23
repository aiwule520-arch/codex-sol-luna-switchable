# Compatibility

This document records upstream assumptions that must be checked before each release.

## GPT-6 Luna

At the time `v0.1.0` was prepared, the OpenAI Codex model catalog reported:

- slug: `gpt-6-luna`
- default context window: `272000`
- maximum context-window override: `872000`
- minimum client version: `0.155.0`
- Fast tier description: `1.5x speed`

Source of truth:

- https://github.com/openai/codex/blob/main/codex-rs/models-manager/models.json
- https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json

The API model may advertise a larger total model context than Codex exposes as its maximum config override. This project uses the Codex-visible maximum because Codex owns the runtime context budgeter.

## Profiles

Current Codex profile layering supports:

```text
$CODEX_HOME/config.toml
+ $CODEX_HOME/<name>.config.toml selected by --profile <name>
```

This project does not write a legacy `profile = "..."` selector into the base config.

## Child service tier

Current Codex behavior makes children follow the root service tier. Track:

- https://github.com/openai/codex/issues/42612
- https://github.com/openai/codex/issues/42665

Release maintainers must re-test this behavior before claiming independent Luna Fast support.

## Release compatibility gate

Before a release:

1. Check the current OpenAI Codex model catalog.
2. Check the current config schema for `[agents]`, `config_file`, model and context keys.
3. Check whether the child service-tier issues are still applicable.
4. Run the repository validation workflow.
5. Test at least one real `explorer` and `worker` child on a current Codex CLI.


## Root model selection

From v0.2.0, this project intentionally omits `model` and `model_reasoning_effort` from all
three root profiles. In current Codex source, both are optional configuration overrides.

This avoids the profile itself locking the root model. Actual picker behavior can still be
affected by other configuration layers. Upstream issues have documented cases where
project-scoped explicit model/reasoning values prevent or override picker choices.

Relevant upstream references:

- https://github.com/openai/codex/blob/main/codex-rs/config/src/config_toml.rs
- https://github.com/openai/codex/blob/main/codex-rs/config/src/profile_toml.rs
- https://github.com/openai/codex/issues/36163
- https://github.com/openai/codex/issues/34535

## Root multi-agent compatibility

The root model is user-selectable, but it must be compatible with the active Codex
multi-agent backend and able to spawn GPT-6 Luna subagents. Compatibility can change
across Codex versions and model-catalog updates. When routing fails, check the current
Codex model catalog and inspect actual child session metadata; do not assume that every
available root model can spawn Luna.
