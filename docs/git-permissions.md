# Git permissions in the installed Symphony

The runtime WORKFLOW is `/Users/agents/.config/symphony/WORKFLOW.md`.
`elixir/WORKFLOW.md` is a template; changing it does not update the running service.
Keep permission-denial instructions aligned with `.codex/skills/push/SKILL.md`:
record the command/error and effective policy in the workpad, then hand off to
Human Review. Existing authorized authentication checks and ordinary Git sync
remain allowed. Never bypass a denial with API-created commits, another remote,
credentials, relocated Git metadata, or disabled sandboxing.

## Verified compatibility

On 2026-09-23 the host runs macOS arm64 as standard user `agents` (uid 502),
official Symphony v0.0.3 and Codex CLI 0.154.0 with ChatGPT login. The installed
Burrito executable SHA-256 is
`b85d78b25cd5cacff92424416f6a3af7cafee5d675f56b5cd26d22d601c2026d`.
Its release App Server/config implementation matches the inspected source.

The live policy uses `approval_policy: never`, `thread_sandbox: workspace-write`,
and turn policy `{type: workspaceWrite, networkAccess: true}`. The user Codex
configuration also selects workspace-write/never. User-owned, mode 0755 `.git`
directories do not overcome the sandbox's protected-path rule.

A dedicated clone reproduced this via the installed Codex App Server's
`command/exec` using that exact turn policy:

```text
fatal: Unable to create '.../.git/index.lock': Operation not permitted
```

Adding only the clone and its absolute `.git` directory to `writableRoots`
allowed `git add`. This distinguishes local protected-path denial from GitHub
credentials or networking. A relative root `.git` was rejected with
`AbsolutePathBuf deserialized without a base path`.

Symphony sends `sandbox` on every `thread/start` and `sandboxPolicy` on every
`turn/start`. An explicit WORKFLOW turn-policy map is passed unchanged; Liquid
renders the prompt body, not this map. Omitting the map synthesizes the workspace
root but does not add its `.git`. Do not use relative paths, `$PWD` or Liquid
placeholders as writable roots, or assume CLI defaults override turn policy.

Codex 0.154.0 exposes named `permissions` in its generated thread/turn schemas,
mutually exclusive with `sandbox`/`sandboxPolicy`. Symphony v0.0.3 does not send
those fields. Merely adding a permission profile to Codex config does not migrate
this integration away from explicit legacy sandbox settings.

## Scope of an explicit grant

For a **single admitted issue only**, the legacy turn policy can explicitly grant
its Git directory without disabling sandboxing:

```yaml
codex:
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite
    networkAccess: true
    writableRoots:
      - /Users/agents/code/symphony-workspaces/DEV-321
      - /Users/agents/code/symphony-workspaces/DEV-321/.git
```

This is a fixed path, **not** a reusable per-issue template. Never deploy a list
of all issue Git directories to the three-agent runtime: every new session would
receive all those grants. Lowering concurrency alone does not restrict admission
or stop existing sessions. A linked worktree also requires inspecting its resolved
Git directory and common directory; do not grant a shared repository's metadata
as though it belonged exclusively to one issue. Prefer Symphony's ordinary clone.

Before a bounded operational test:

1. Observe no running/retrying/blocked work and coordinate any queued issues.
2. Save the live WORKFLOW, restrict admission to the one validation issue, then
   add only its canonical clone/gitdir paths. Do not change auth, model, billing,
   or human merge policy. Do not grant the workspace parent or credential paths.
3. Start a fresh session through the same installed Symphony. Verify branch
   creation, add, commit, push and PR creation, then a second commit/push. Compare
   local HEAD/branch and `git ls-remote` results. Check that sibling workspace and
   credential-directory canary writes are denied without touching credentials.
4. Once the session stops, remove the fixed grant and restore admission. Verify
   the YAML diff, health API and effective policy of a fresh session. A hot reload
   does not revoke permissions already captured by an existing session.

For rollback, restore only this task's changed policy/admission fields and prompt
block from the saved WORKFLOW, preserving unrelated concurrent edits. Keep the
permission-denial guidance unless explicitly reverting that procedure too.

## DEV-321 native Git proof

On 2026-09-23, the bounded DEV-321 session created branch
`codex/dev-321-git-permissions`, ran native `git add`, committed locally, pushed
with `git push -u origin HEAD`, and opened PR #6 using the existing authorized
GitHub authentication. The first native commit was
`1e37328d7c7467e65b63dd7168f4688c82062ff1`.

This proves only the explicit DEV-321 clone/gitdir grant used for this isolated
session. It does not prove a reusable issue-relative Git grant for the standard
three-agent runtime.

The standard three-agent configuration has no verified issue-relative Git grant
in this release. A successful isolated test must not be described as a fix for
all future issues. Until an official compatible per-thread/turn configuration is
available, use the blocked Human Review path; engine changes or broader access
require a separately reviewed scope.

Official references: [protected paths](https://learn.chatgpt.com/docs/agent-approvals-security#protected-paths-in-writable-roots),
[permission profiles and legacy precedence](https://learn.chatgpt.com/docs/permissions),
[App Server](https://developers.openai.com/codex/app-server).
