---
name: land
description: Resolve PR conflicts, checks, and reviews; land after a human moves the issue to Merging or explicitly requests a merge.
---

# Land

Under the [fork policy](../../../README.md#running-this-fork), a human moving the
issue to `Merging` or explicitly requesting a merge authorizes landing. Without
that authorization, prepare the PR and hand off at `Human Review`. Never move
an issue to `Merging` yourself. After merging a workflow issue, follow the
WORKFLOW completion procedure to update it to `Done`.

## Procedure

1. Confirm authenticated `gh`, the intended PR branch, and a clean working tree.
   Publish intended outstanding changes with [commit](../commit/SKILL.md) and
   [push](../push/SKILL.md), preserving unrelated work.
2. Inspect `gh pr view --json number,url,headRefOid,mergeable,mergeStateStatus`.
   Resolve conflicts with [pull](../pull/SKILL.md), then push. Recheck `UNKNOWN`
   mergeability before proceeding.
3. Address review feedback below and verify current-head checks according to
   [validation](../../../docs/validation.md). On failure, inspect
   `gh pr checks` and `gh run view <run-id> --log`, fix, commit, and push.
   A flaky failure still requires a successful rerun of the applicable gate.
4. After each head change, sync and reassess validation/review for that head.
   If checks are missing, inspect their trigger and permissions; do not manufacture
   commits or rewrite history merely to trigger CI.
5. Once conflicts, checks, and reviews are clear, hand off the PR URL and validation
   evidence for `Human Review` if merge authorization has not been given. With
   authorization as defined above, squash-merge the validated head using the PR
   title/body, then verify merged state:

   ```sh
   pr_title=$(gh pr view --json title -q .title)
   pr_body=$(gh pr view --json body -q .body)
   gh pr merge --squash --subject "$pr_title" --body "$pr_body"
   gh pr view --json state,mergeCommit,url
   ```

   Keep working until the authorized merge completes or a blocker is recorded.
   Leave remote branch cleanup to the repository; do not enable auto-merge.

## Review feedback

- Inspect both inline reviews and top-level discussion:

  ```sh
  gh api --paginate 'repos/{owner}/{repo}/pulls/<pr_number>/comments'
  gh api --paginate 'repos/{owner}/{repo}/issues/<pr_number>/comments'
  gh api --paginate 'repos/{owner}/{repo}/pulls/<pr_number>/reviews'
  ```

- For each finding, accept, clarify, or decline/defer with a reason. Check the
  task's intent before changing code; ask when an unresolved conflict with that
  intent blocks a safe decision. Validate correctness concerns before dismissing
  them; keep documentation consistent with behavior.
- Prefix agent comments with `[codex]`. Reply with intended action before pushing
  changes, then with fix details, commit SHA, and validation. Answer each reviewer
  in the original thread; resolve addressed threads and read back their state.
- Reply to inline feedback using the numeric comment ID, not its GraphQL node ID:

  ```sh
  gh api -X POST 'repos/{owner}/{repo}/pulls/<pr_number>/comments' \
    -f body='[codex] <response>' -F in_reply_to='<comment_id>'
  ```

  Verify endpoint/permissions on a 404. Reply to `## Codex Review` issue comments
  in the issue discussion instead; ordinary inline Codex reviews stay inline.
- After a batch of fixes, keep the PR title/body aligned with the full diff and
  post one summary of changes, commits, checks, and justified deferrals. Request
  a rerun only after new commits and after addressing existing feedback; verify
  its completion rather than assuming a push automatically triggers review.
- Outstanding review feedback blocks merge. A reply, a resolved thread, passing
  CI, and completed review are separate conditions.

## Optional watcher

`python3 .codex/skills/land/land_watch.py` monitors comments, checks, conflicts,
and head changes. Exit codes: `2` feedback, `3` failed/missing checks, `4` changed
head, `5` conflicts. Handle the reported condition above and rerun as needed.
Its success is a polling result, not proof of review completion or thread
resolution; the current-head validation and review gates still apply.
