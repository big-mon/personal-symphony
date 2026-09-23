# Working on Personal Symphony

## Scope

These work rules apply only outside `elixir/`: the fork's root documentation,
`docs/`, `.codex/`, and `.github/`. The Elixir implementation and its local
instructions are maintained upstream; leave `elixir/` unchanged unless the task
explicitly requires an Elixir-side change. For that work, follow
[elixir/AGENTS.md](elixir/AGENTS.md); the work rules below do not apply there.

## Before editing

1. Inspect the working tree, branch, and existing changes; preserve unrelated work.
2. Read the affected procedure, configuration, and its consumers. Keep fork
   operations consistent with the existing service contract in [SPEC.md](SPEC.md).
3. Choose checks from [docs/validation.md](docs/validation.md) using the whole PR
   diff, including uncommitted and untracked files. Its path allowlist determines
   the gate; an unknown path requires full validation.

Keep fork changes small and give each policy one authoritative document. Link to
upstream implementation documentation instead of maintaining a second copy here.

## Task-specific procedures

Read the linked procedure when its condition applies:

| Task | Procedure |
| --- | --- |
| Set up or run this fork | [Fork setup](README.md#running-this-fork) |
| Diagnose a stalled, retrying, or failed run | [Debug skill](.codex/skills/debug/SKILL.md) |
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
- Keep fork documentation with its audience: root `README.md` owns the human
  overview and fork setup; this file owns agent rules for work outside `elixir/`.
  Put task-specific operational details in `docs/` or the relevant skill and link
  to them instead of repeating procedures.
