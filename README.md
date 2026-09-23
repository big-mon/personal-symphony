# Personal Symphony

Personal Symphony is a fork of OpenAI's Symphony for running coding agents from an
issue tracker. It picks up eligible issues, gives each one a separate workspace,
and runs Codex to implement and validate the work.

This fork uses a human review workflow: Codex prepares the pull request and hands
work back for review; a person reviews, merges, and completes the issue.

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
4. You review the PR. Requested changes return to active work; accepted work is
   merged and completed by a person.

The Elixir service supports Linear, GitHub Issues, Jira Cloud, Asana, and GitLab.
The current deployment uses Linear, but the tracker is configurable. The workflow
controls which issues run, workspace setup, concurrency, and Codex's instructions.

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

### Configure the tracker and workflow

Copy `elixir/WORKFLOW.md` to a runtime location outside the checkout and choose a
separate workspace root. Use the guide for your selected tracker:
[Linear](elixir/README.md#linear-adapter-profile),
[GitHub Issues](elixir/README.md#github-issues-adapter),
[Jira Cloud](elixir/README.md#jira-cloud-adapter),
[Asana](elixir/README.md#asana-adapter), or
[GitLab](elixir/README.md#gitlab-adapter).

Configure both parts of the runtime workflow:

- **YAML front matter:** set `tracker.kind`, provider scope and credentials, and
  active/terminal states supported by that adapter. Supply credentials through
  the service environment or host-side secret references.
- **Markdown prompt:** replace the template's Linear tool requirements and skill
  references, workpad/comment operations, state transitions, and PR-linking
  procedures with equivalents for the selected tracker. Changing `tracker.kind`
  alone does not adapt the prompt.

Keep the human review policy across trackers: Codex implements, validates, and
opens the PR; humans merge and complete the issue. Replace the template's
`Merging` routes and `land` instructions accordingly. Pause dispatch during review
without making the issue terminal. Adapters limited to open/closed states need a
supported dispatch filter, such as `tracker.required_labels`, instead of a custom
review state. The cleanup hook below closes open PRs on terminal issues, so mark
accepted work complete after merging its PR.

### Linear example (current deployment)

Merge these settings into the copied workflow's YAML front matter. Use your
project's slug if different:

```yaml
tracker:
  kind: linear
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

Provide `LINEAR_API_KEY` through the service environment. In this example, use
`Human Review` for handoff, `Rework` for requested changes, and `Done` after merge.
Ensure these Linear states exist; keep `Human Review` outside active and terminal
states to preserve its workspace. Apply the human review prompt changes above.

### Start the service

From `elixir/`, pass the configured runtime file and the CLI's required
acknowledgement flag:

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
