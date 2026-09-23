# Symphony

Symphony turns project work into isolated, autonomous implementation runs, allowing teams to manage
work instead of supervising coding agents.

[![Symphony demo video preview](.github/media/symphony-demo-poster.jpg)](https://player.vimeo.com/video/1186371009?h=5626e4b899)

The demo shows agents taking work from a Linear board and producing PRs with
validation evidence.

> [!WARNING]
> Symphony is a low-key engineering preview for testing in trusted environments.

## Running this fork

Follow the [Elixir setup](elixir/README.md), then use these `big-mon/personal-symphony`
values in your runtime copy of `WORKFLOW.md`. The repository's `elixir/WORKFLOW.md`
is a template; editing it does not update the running service.

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

Pass auth through environment variables or host-side secret references; do not commit secret values
to docs or the repository. In this fork's runtime workflow body, replace the inherited `Merging`
and `land` instructions with the fork policy: Codex owns implementation, validation, PR creation,
and handoff to `Human Review`; humans own PR merges and post-merge completion.

## Project guides

- [Validation](docs/validation.md): select local checks and verify current-head CI.
- [Git permissions](docs/git-permissions.md): diagnose write denials and scope an authorized runtime test.
- [Service specification](SPEC.md): language-independent contract for implementations.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
