# Validation by change scope

Use the same scope locally and in the `make-all` workflow. The allowlist in
[`validation-paths.yml`](../.github/validation-paths.yml) is authoritative; anything
outside it requires full validation. Never classify by file extension alone.

| Changes | Required validation |
| --- | --- |
| README, SPEC, guides under `docs/` or `elixir/docs/`, license/notice, PNG/JPG/MP4 under `.github/media/` | Review content, links/media and `git diff --check` |
| `elixir/AGENTS.md`, `.codex/skills/**/SKILL.md`, PR template | Diff check, review syntax and walk through the affected procedure; validate PR bodies with the [standalone command](../elixir/AGENTS.md#pr-requirements) when applicable |
| `elixir/WORKFLOW.md` | Diff check, review YAML front matter, prompt and changed hook/agent procedure; `cd elixir && mix deps.get && mix test test/symphony_elixir/core_test.exs` |
| Everything else, including `elixir/lib/`, `test/` (even Markdown fixtures), `priv/`, dependencies, tool/build/test config, hooks/scripts, GitHub Actions and the scope filter itself | `make -C elixir all`, plus syntax/behavior checks for changed scripts or Actions |

For Actions use `actionlint`; for shell use the matching interpreter's syntax
check (for example `bash -n .codex/worktree_init.sh`) and a focused exercise of the
changed behavior. Skill Markdown is an executable instruction: review its front
matter, commands, paths and the affected procedure, not just its formatting.
Full Elixir tests do not replace these checks. If a newly changed document becomes
a runtime/test input, remove it from the allowlist or add its consuming test to CI.

For changes to the scope rules/workflow, run
`bash .github/tests/validation-paths.sh`. This uses Node, Git and curl to exercise
the pinned paths-filter action with document, implementation, mixed, procedure,
WORKFLOW, configuration, fixture, unknown and deletion cases; full CI runs it too.

After fetching `origin`, inspect the entire PR diff with
`git diff --name-status --no-renames origin/main...HEAD`, plus staged/unstaged and
untracked files. Include upstream merges and all changed inputs since the last
validation when deciding whether previous results remain valid. Mixed changes use
the strongest applicable gate. Unknown paths require full validation; a failed
diff/classification is a failure to resolve, never evidence for a document-only skip.

Run targeted checks while editing, then the applicable gate once before pushing.
Full `make all` already includes the WORKFLOW tests: do not rerun them separately.
Do not repeat a passed local gate for the same inputs merely for commit, push or
handoff. Revalidate when code, test/config inputs, dependencies or the merged base
change, or when a failure leaves uncertainty. Record commands and results in the
workpad and PR; mark a non-applicable gate as such with its scope reason.

## CI and checks

The workflow always starts on pull requests and pushes to `main`; the existing
`make-all` job name stays unchanged. It always checks the diff and reports the
selected scope in the run summary, then conditionally installs Elixir and runs
the applicable checks. A classification/check failure fails that same job. Only
non-applicable steps are skipped. The separate PR description check loads the
existing validator directly with Elixir. It still needs the Elixir/Erlang runtime
from `elixir/mise.toml`, but does not install Hex, Rebar or Symphony dependencies,
or build the project.

`workflow_dispatch` forces the full gate without path classification. Use the
Actions **Run workflow** control or:

```sh
gh workflow run make-all.yml --ref <branch>
```

Check results on the current PR head: `make-all` must finish successfully, with the
expected scope in its summary, and `validate-pr-description` must pass. Do not
wait for separate build/test/Dialyzer checks: they are steps of `make-all`.
Non-applicable steps are different from missing, queued, cancelled or failed jobs;
none of those job states is proof of successful validation. A missing check means
inspect its trigger/permissions, not wait indefinitely or assume success.

Keep the workflow trigger unfiltered so required checks cannot remain pending due
to path filtering. See [GitHub's required-check guidance](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
and [paths-filter behavior](https://github.com/dorny/paths-filter/tree/v3).

## Runtime workflow

`elixir/WORKFLOW.md` is a template. After human review and merge, apply validation
instruction changes to the installed binary's external WORKFLOW using the issue
checkout's policy. Review the live prompt diff and validate YAML/rendering with
the normal operational procedure. Preserve tracker settings, workspace/hooks,
model, billing, concurrency, and human merge policy. Repository edits alone do
not update the running service.
