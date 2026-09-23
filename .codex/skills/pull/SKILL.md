---
name: pull
description: Merge origin/main into the current branch and resolve conflicts without rebasing; use for update-branch or push synchronization failures.
---

# Pull

1. Confirm the current branch and `origin`. Commit or stash intended local work
   before merging; preserve unrelated changes.
2. Enable local conflict reuse with `git config rerere.enabled true` and
   `git config rerere.autoupdate true`, then `git fetch origin`.
3. If the remote feature branch exists, sync it first with
   `git pull --ff-only origin "$(git branch --show-current)"`. Inspect divergence
   on failure instead of overwriting history.
4. Merge main with `git -c merge.conflictstyle=zdiff3 merge origin/main`.
5. Resolve conflicts by comparing base, ours, and theirs with
   `git diff :1:path :2:path` and `git diff :1:path :3:path`. Preserve both
   changes' intent and public contracts; use whole-file ours/theirs only when
   one side should win entirely. Resolve source before regenerating artifacts.
6. Stage resolved files and finish with `git merge --continue`. Run
   `git diff --check` and the applicable [validation](../../../docs/validation.md)
   for the merged inputs. Report significant resolutions and check results.

Ask only when product intent, incompatible contracts, data loss, or an unknown
branch/remote leaves no safe resolution inferable from code, tests, or context.
For Git write/auth denial, use the [push failure procedure](../push/SKILL.md#failures).
