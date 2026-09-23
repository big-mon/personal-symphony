---
name: push
description: Push the current branch and create or update its pull request; use for publishing changes or opening a PR.
---

# Push

1. Confirm the branch, configured `origin`, and existing authorized GitHub auth
   (`gh auth status`). Follow [validation](../../../docs/validation.md) for the
   entire PR scope, including local changes; record commands, results, and any
   non-applicable gate. Reuse passed checks while their inputs remain unchanged.
2. Push with `git push -u origin HEAD`. Handle failures below before retrying.
3. Inspect the branch's PR with `gh pr view`. Update an open PR; create one if
   absent. A closed/merged PR requires a new branch and PR. Treat API/auth errors
   as failures, not evidence that no PR exists.
4. Write the title and body for the full current diff, using
   [the PR template](../../../.github/pull_request_template.md). Fill all sections,
   replace placeholders, and preserve required bullets/checkboxes. Reconsider
   both title and body after scope changes.
5. Validate the body file before publication:

   ```sh
   (cd elixir && mix pr_body.check --file '<absolute-body-file>')
   ```

   Use `gh pr create --title <title> --body-file <file>` or
   `gh pr edit --title <title> --body-file <file>`. Read back the published body
   and validate it again if it differs. Return the URL from
   `gh pr view --json url -q .url`.

## Failures

- Non-fast-forward or stale branch: use [pull](../pull/SKILL.md), validate changed
  inputs, then retry the normal push. Use `--force-with-lease` only as a last
  resort after an authorized history rewrite; never use `--force`.
- Auth, permissions, workflow restrictions, or local Git metadata write denial:
  stop the failed operation and report the exact error. For local denial, inspect
  the workspace and `git rev-parse --absolute-git-dir` read-only to distinguish
  sandbox/OS policy from auth/network failures.
- Record the command, error, workspace/gitdir, effective permissions, and
  diagnostics in the existing workpad; hand off to `Human Review` as blocked.
  Report commit/push/PR creation only when confirmed successful.
- Existing authorized auth checks and ordinary Git synchronization remain
  allowed. Never bypass denial by changing remotes/protocols/credentials,
  relocating `.git`, disabling sandboxing, or creating commits through the API.
  For an explicitly authorized runtime permissions investigation, read
  [Git permissions](../../../docs/git-permissions.md).
