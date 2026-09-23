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

Follow the [Elixir setup guide](elixir/README.md#how-to-use-it) to build or install
Symphony, prepare a workflow for this fork, and start the service. The optional
[web dashboard](elixir/README.md#web-dashboard) shows running and blocked work.

`elixir/WORKFLOW.md` is a template. The running service reads the workflow path
passed at startup; changing this repository does not deploy changes to that file.
Keep credentials in environment variables or host-side secret references.

## Work on this repository

- [Agent instructions](AGENTS.md): repository rules and task-specific procedures.
- [Validation](docs/validation.md): local checks and the required PR checks.
- [Elixir guide](elixir/README.md): configuration, tracker adapters, and live tests.
- [Service specification](SPEC.md): the language-independent behavior contract.
- [Git permissions](docs/git-permissions.md): deployment checks and permission failures.

## License

[Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution.
