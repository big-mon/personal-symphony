# Working on the Elixir service

Apply the [repository instructions](../AGENTS.md) together with these Elixir-specific rules.
Run commands below from `elixir/`; use `mise exec --` when the pinned tools are not
already on `PATH`. Tool versions live in [mise.toml](mise.toml).

## Implementation boundaries

- `Workflow` parses the workflow file; `WorkflowStore` owns reloads and the last
  known good workflow; `Config` exposes validated settings. Add configuration
  access through `Config` rather than ad-hoc environment reads.
- `Orchestrator` owns scheduling, claims, retries, reconciliation, and worker
  selection. Preserve their concurrency and cleanup semantics together.
- `Workspace` owns issue directories and hooks; `AgentRunner` owns a worker
  attempt; `Codex.AppServer` owns the Codex session and turn protocol. Preserve
  workspace path checks and cleanup on failure.
- `Tracker` is the boundary for tracker reads and provider-native tools. Keep
  provider details in the adapters and preserve session-bound tool credentials.

## Code and tests

- Follow the existing module/style patterns in `lib/symphony_elixir/`.
- Public functions (`def`) in `lib/` need an adjacent `@spec`; `@impl` callbacks
  are exempt and `defp` specs are optional. `mix specs.check` verifies this rule.
- Prefer focused tests with real OTP processes and observable behavior. Prove
  health with a synchronous call or stable effect, not only a PID.
- For non-trivial changes, review adversarially early: challenge complexity and
  try adjacent lifecycle paths. A reproducible failure blocks handoff.
- If tests require repeated global restarts or bespoke cleanup, first inspect
  the shared harness or ownership boundary.

## Validation

Use [the shared validation policy](../docs/validation.md) to select the gate.
`mix setup` installs project dependencies; `make all` runs the full gate. Read
[the live-test instructions](README.md#testing) before running opt-in E2E tests:
these launch real agents and mutate external tracker resources.

## PR Requirements

Use [the PR template](../.github/pull_request_template.md). Validate the body from
`elixir/` with the standalone command:

```bash
mise exec -- elixir -r lib/mix/tasks/pr_body.check.ex -e 'Mix.start(); Mix.Task.run("pr_body.check", System.argv())' -- --file /path/to/pr_body.md
```

This needs the Elixir/Erlang runtime from `mise.toml`, but no Hex, Rebar, project
dependencies, or build. The distributed Symphony binary does not supply that runtime.
