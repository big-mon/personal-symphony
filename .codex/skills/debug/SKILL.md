---
name: debug
description: Trace issue/session logs when Symphony runs stall, retry repeatedly, or fail.
---

# Debug

1. Confirm the affected ticket and runtime log directory. The default is `log/`;
   include rotated `symphony.log*` segments. Follow the
   [logging guide](../../../elixir/docs/logging.md) for correlation fields and
   focused searches.
2. Find the ticket slice, then select one session from those matching lines:

   ```sh
   rg -nFw -- 'issue_identifier=<KEY>' '<LOG_DIR>'/symphony.log*
   rg -nFw -- 'session_id=<THREAD>-<TURN>' '<LOG_DIR>'/symphony.log*
   ```

   Cross-check `issue_id`, `issue_identifier`, and `session_id` so concurrent
   attempts and retries stay separate.
3. Trace that session from `Codex session started` through its terminal event.
   Identify the failing stage:

   | Signal | Stage |
   | --- | --- |
   | `Codex session failed` before stream events | App-server startup |
   | `turn_failed`, `turn_cancelled`, `turn_timeout`, `ended with error` | Turn execution |
   | `Issue stalled ... restarting with backoff` | Stall recovery |
   | `Agent task exited ... reason=...` | Worker exit |

4. Compare other attempts only after establishing this timeline; determine
   whether the failure is isolated or repeats across issues.
5. Report the failing stage, probable cause, and minimal timestamped evidence
   with the three correlation IDs. Redact secrets; never paste full logs.
