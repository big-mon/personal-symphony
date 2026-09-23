# Codex permissions for trusted Symphony runs

This fork's `elixir/WORKFLOW.md` explicitly selects full access for trusted,
unattended work. Codex can update Git metadata and repository `.codex` files
without the protected-path failures of `workspace-write`.

```yaml
codex:
  # Keep the existing command and other Codex settings.
  approval_policy: never
  thread_sandbox: danger-full-access
  turn_sandbox_policy:
    type: dangerFullAccess
```

This removes Codex filesystem and network sandbox isolation. The process retains
the host user's OS permissions and can access other workspaces and user-readable
files. Separate issue directories organize work; they are not security boundaries.
GitHub authorization and the human merge decision still apply.

Symphony sends `thread_sandbox` on `thread/start` and `turn_sandbox_policy` on
`turn/start`; set both as shown. Remove `networkAccess` and `writableRoots` from
the full-access turn policy. An explicit policy is passed through unchanged, so
this requires no Symphony engine change, rebuild or Codex user-config change.
Omitting these fields restores the engine's sandboxed defaults, not this profile.

## Apply after human merge

The installed service reads `/Users/agents/.config/symphony/WORKFLOW.md`.
Changing the repository template does not change that file or deploy the policy.

1. Wait for active sessions to finish and coordinate queued work before rollout.
2. Save a copy of the runtime WORKFLOW. Replace only the three policy fields above;
   preserve its command/model, tracker, credentials, hooks, workspace root,
   concurrency and human merge policy. Do not copy the entire repository template
   over the runtime file.
3. Validate the YAML and confirm the diff contains only the intended policy change.
   Symphony reloads the file, but existing Codex sessions retain their captured
   policies. Verify the effective policy in a fresh session.
4. In a disposable issue workspace, verify branch creation, staging, commit and
   an edit under `.codex/skills`. Then complete an ordinary issue through push and
   PR creation using the configured remote and existing authentication. Check
   the local/remote commit and leave the PR for human review.

The rollout is complete only after the fresh-session checks succeed. Unit tests
and a successful PR do not prove that the installed service adopted this policy.

For rollback, restore the saved policy fields while preserving unrelated edits.
Do not assume a reload revokes access from existing sessions; finish or explicitly
stop those sessions before verifying a new sandboxed session.

## Permission failures

If a command is still denied, inspect the fresh session's effective policy first.
Then distinguish an outer sandbox or OS denial from GitHub auth/network failures.
Keep `.codex/skills/push/SKILL.md` and the workflow's blocked-access procedure:
record the exact command/error, workspace/gitdir and effective policy, then hand
off to Human Review. Agents must not change their permissions, credentials,
remote/protocol or Git metadata location to bypass a denial. This profile is an
operator-authorized deployment choice, not an agent recovery action.

If per-issue sandbox isolation is required, do not use this profile. The installed
Symphony does not render issue-relative paths in explicit policy maps; hardcoding
all issue Git directories would grant each session access to the whole list.

References: [protected paths](https://learn.chatgpt.com/docs/agent-approvals-security#protected-paths-in-writable-roots),
[App Server policies](https://learn.chatgpt.com/docs/app-server#command-execution).
