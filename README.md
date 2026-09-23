# Personal Symphony

Personal Symphony is a fork of OpenAI's Symphony for running coding agents from an
issue tracker. It picks up eligible issues, gives each one a separate workspace,
and runs Codex to implement and validate the work.

This fork uses a human review workflow: Codex prepares the pull request and hands
it off to `Human Review`; a person reviews, merges, and completes the issue.

> [!WARNING]
> This is experimental software for trusted environments. The supplied workflow
> gives Codex the host user's filesystem and network access. Separate workspaces
> are not security boundaries. Review the [permissions guide](docs/git-permissions.md)
> before running it.

## How work moves through the system

1. You put a well-defined issue into an active tracker state.
2. Symphony polls the tracker and creates or reuses that issue's workspace.
3. Codex reads the workflow and repository instructions, implements the change,
   runs checks, and opens a PR with validation evidence.
4. You review the PR. Requested changes return to `Rework`; accepted work is
   merged and completed by a person.

The Elixir service supports Linear, GitHub Issues, Jira Cloud, Asana, and GitLab.
This fork's setup guide uses Linear. The workflow controls which issues run,
workspace setup, concurrency, and the instructions given to Codex.

[![Symphony demo video preview](.github/media/symphony-demo-poster.jpg)](https://player.vimeo.com/video/1186371009?h=5626e4b899)

The demo shows agents taking work from a Linear board and producing PRs.

## Running this fork

You need Git, an authenticated Codex CLI, and credentials for the selected tracker.
The supplied hooks also use GitHub CLI (`gh`) and the Elixir toolchain managed by
`mise`.

The [Elixir guide](elixir/README.md) describes the upstream implementation and
configuration. Use this fork's source and [releases](https://github.com/big-mon/personal-symphony/releases).
For a source build:

```bash
git clone https://github.com/big-mon/personal-symphony
cd personal-symphony/elixir
mise trust
mise install
mise exec -- mix setup
mise exec -- mix build
```

Copy `elixir/WORKFLOW.md` to a runtime location outside the checkout. Retain
`tracker.kind: linear`, choose a separate workspace root, and merge these fork
settings into its YAML front matter. Use your project's slug if different:

```yaml
tracker:
  provider:
    project_slug: personal-symphony-506ccfb1912c
  active_states:
    - Todo
    - In Progress
    - Rework
hooks:
  after_create: |
    git clone --depth 1 https://github.com/big-mon/personal-symphony .
    if command -v mise >/dev/null 2>&1; then
      cd elixir && mise trust && mise exec -- mix deps.get
    fi
  before_remove: |
    cd elixir && mise exec -- mix workspace.before_remove --repo big-mon/personal-symphony
agent:
  max_concurrent_agents: 1
```

Also replace the template prompt's `Merging` routes and `land` instructions with
this fork's policy: Codex implements, validates, opens the PR, and hands the issue
to `Human Review`; humans merge and complete it. Ensure these Linear states exist.
Keep `Human Review` outside active and terminal states to preserve its workspace.
The cleanup hook closes open PRs on terminal issues, so mark accepted work `Done`
after merging its PR.

Provide `LINEAR_API_KEY` through the service environment. Start from `elixir/`
with the configured file and the CLI's required acknowledgement flag:

```bash
mise exec -- ./bin/symphony /absolute/path/to/WORKFLOW.md \
  --i-understand-that-this-will-be-running-without-the-usual-guardrails
```

A downloaded binary accepts the same path and flag. The supplied workspace hooks
still require the Elixir toolchain and `gh` on the worker host. The optional
[web dashboard](elixir/README.md#web-dashboard) shows running and blocked work.

`elixir/WORKFLOW.md` is a template. The running service reads the workflow path
passed at startup; changing this repository does not deploy changes to that file.
Keep credentials in environment variables or host-side secret references.

## Work on this repository

The `elixir/` tree is maintained upstream. Fork-specific documentation,
operations, skills, and CI live outside it; keep Elixir changes limited to tasks
that explicitly require them.

- [Agent instructions](AGENTS.md): rules for fork work outside `elixir/`.
- [Validation](docs/validation.md): local checks and the required PR checks.
- [Elixir guide](elixir/README.md): configuration, tracker adapters, and live tests.
- [Service specification](SPEC.md): the language-independent behavior contract.
- [Git permissions](docs/git-permissions.md): deployment checks and permission failures.

## License

[Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution.
