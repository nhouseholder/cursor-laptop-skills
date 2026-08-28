---
name: get-ready
description: "Session start, read-only. Orient from Engram standing decisions plus recent handoffs, git status, and open todos. Never write a handoff."
disable-model-invocation: true
---

# Get ready (`/get-ready`)

Session start. **Read-only.** Orient, then stop. Do not start the work until the summary is printed — unless the user's message already named work; still orient first, then continue into that work in the same turn.

**Never write a handoff. Never invoke `/wrap-up`.**

## Hard gates

- Stay in the current workspace (`pwd` / git root). All reads and later edits stay there.
- Do **not** treat `CURRENT_STATE.md` as live decision memory. Prefer Engram standing decisions + recent `handoffs/`.
- Do **not** `git pull` / rebase / checkout another branch. Cloud sessions sit on a working branch; fetching for comparison is fine, mutating HEAD is not.
- A failed lookup is not a missing record. Prove the search can find something before reporting nothing.
- Do not invent product rules. Point at `AGENTS.md` / `CLAUDE.md` / the owning file.

## 1. Anchor

```
Project: [basename of git root]
Repo:    [origin remote, or "none"]
Branch:  [current]
HEAD:    [short sha + subject]
Path:    [workspace root]
```

## 2. Handoff

Find the newest file in this repo's `handoffs/`. Match whatever naming this repo already uses (`YYYY-MM-DD_*.md`, `handoff_*.md`, `HANDOFF.md`). Read that file fully.

No handoff → say "No previous handoff. First session or none committed." Skip to §3.

## 3. Standing decisions (≤5)

If Engram MCP is available: pull at most **five** standing `decision` / `architecture` / `preference` memories for the **open topic** (prefer `topic_key` hits from the handoff or the user's message).

If Engram is down or empty: say so and continue. Do not stall.

Do not save anything.

## 4. Git and todos

- `git status --short` and whether this branch has unpushed commits (compare to its upstream if it has one — do not update it).
- Version file if this repo has one (`VERSION`, `package.json` version, `frontend/public/data/meta.json`).
- Open items from `tasks/todo.md` if present.

## 5. Present

```
GET READY
=========
Project: [name]  Branch: [branch]  HEAD: [sha] [subject]

PREVIOUS: [1–2 sentences from the handoff, or "none"]
PICKUP:   [in progress, or "clean"]
BLOCKED:  [blocked, or "none"]
DECISIONS:[≤5 topic_key lines, or "Engram unavailable / none"]
TODO:     [open count + top item, or "no tasks/todo.md"]

NEXT:
  1. [...]
  2. [...]
  3. [...]
```

Ready. If the user already named work, continue into it. Otherwise wait for the ask.
