# Agent routing

Fork work is scoped outside `elixir/`. For explicitly requested Elixir changes,
follow [elixir/AGENTS.md](elixir/AGENTS.md) instead of this router.

Read the matching guide when its task applies:

| Task | Guide |
| --- | --- |
| Set up the fork or change its runtime workflow | [Fork setup and human review policy](README.md#running-this-fork) |
| Select validation before editing or verify handoff | [Validation](docs/validation.md) |
| Change the service contract | [Specification](SPEC.md) |
| Diagnose stalled, retrying, or failed runs | [Debug](.codex/skills/debug/SKILL.md) |
| Investigate Git denial or deploy permission changes | [Git permissions](docs/git-permissions.md) |
| Commit, sync, or publish a PR | [Commit](.codex/skills/commit/SKILL.md), [pull](.codex/skills/pull/SKILL.md), [push](.codex/skills/push/SKILL.md), as applicable |
| Prepare merge handoff or an explicitly requested merge | [Land](.codex/skills/land/SKILL.md) |
| Cut an explicitly requested release | [Release](.codex/skills/release/SKILL.md) |
| Use Symphony's injected `linear_graphql` tool | [Linear](.codex/skills/linear/SKILL.md) |
