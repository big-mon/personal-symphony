# Working on Personal Symphony

These instructions apply across the repository. For changes under `elixir/`, also
read [elixir/AGENTS.md](elixir/AGENTS.md).

## Before editing

1. Inspect the working tree, branch, and existing changes; preserve unrelated work.
2. Read the affected implementation and its callers. For behavior changes, consult
   the relevant section of [SPEC.md](SPEC.md); extensions may add behavior without
   contradicting the contract. Update the spec when the intended contract changes.
3. Choose checks from [docs/validation.md](docs/validation.md) using the whole PR
   diff, including uncommitted and untracked files. Its path allowlist determines
   the gate; an unknown path requires full validation.

Prefer the smallest coherent change with one owner for each policy. For stateful
changes, trace startup, reload, restart, and failure recovery before editing.
Challenge unnecessary abstractions and surface material trade-offs early.

## Task-specific procedures

Read the linked procedure when its condition applies:

| Task | Procedure |
| --- | --- |
| Set up or run the service | [Elixir setup](elixir/README.md#how-to-use-it) |
| Diagnose a stalled, retrying, or failed run | [Debug skill](.codex/skills/debug/SKILL.md) |
| Change logging or token accounting | [Logging](elixir/docs/logging.md), [token accounting](elixir/docs/token_accounting.md) |
| Investigate a Git write denial or deploy a permission change | [Git permissions](docs/git-permissions.md) |
| Commit, sync, or publish a PR | [Commit](.codex/skills/commit/SKILL.md), [pull](.codex/skills/pull/SKILL.md), [push](.codex/skills/push/SKILL.md), as applicable |
| Use Symphony's injected `linear_graphql` tool | [Linear skill](.codex/skills/linear/SKILL.md) |

## Operational boundaries

- Run Symphony-managed Codex sessions in the issue workspace under the configured
  workspace root, never in the service's source checkout.
- Keep credentials in environment variables or host-side secret references, out
  of tracked files and command output.
- Treat `elixir/WORKFLOW.md` as a template. Live workflow changes require a separate
  deployment request; a repository edit or passing CI does not prove deployment.
- This fork hands validated PRs to `Human Review`. Humans own merging and
  post-merge completion. The template's `Merging` flow and bundled `land`/`release`
  skills do not authorize an agent to merge; follow the fork setup guide when
  preparing a runtime workflow.

## Before handoff

- Run the applicable validation and record commands and results. Reuse passed
  checks while their inputs remain unchanged; investigate every failed check.
- Use the [PR template](.github/pull_request_template.md) and the
  [PR body validator](elixir/AGENTS.md#pr-requirements). Verify current-head CI as
  described in the validation policy before reporting the PR ready for review.
- Keep documentation with its audience: root `README.md` explains the project and
  routes human readers; `elixir/README.md` owns setup and configuration; `AGENTS.md`
  files own repository work rules; `elixir/WORKFLOW.md` owns the runtime prompt
  template. Update the affected document in the same PR and link to existing
  procedures instead of repeating them.
