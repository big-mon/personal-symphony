---
name: commit
description: Create a commit or prepare its message from the staged changes and session rationale.
---

# Commit

1. Inspect `git status`, `git diff`, and `git diff --staged`; use session history
   for intent. Stage only the intended files, excluding artifacts and unrelated
   work. Preserve unrelated staged changes rather than including them silently.
2. Write an imperative subject, `type(scope): summary`, at most 72 characters
   with no trailing period. Scope is optional.
3. In the body, explain the changes, rationale/trade-offs, and validation results
   (or why checks were not run). Wrap at 72 characters. Append
   `Co-authored-by: Codex <codex@openai.com>` unless the user requests otherwise.
4. Compare the message with the staged diff, then commit using
   `git commit -F <message-file>` with literal newlines. Confirm the resulting
   commit contains only the intended work.

For a Git write denial, follow the [push failure procedure](../push/SKILL.md#failures).
