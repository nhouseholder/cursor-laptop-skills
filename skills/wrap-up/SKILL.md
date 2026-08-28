---
name: wrap-up
description: "Session end. Write a lean handoff in this project's handoffs/, commit it on the current branch. Do not auto-ship. Default do not save Engram."
disable-model-invocation: true
---

# Wrap up (`/wrap-up`)

Last thing before ending a session. Write a lean handoff **in this project's** `handoffs/`. Then stop.

## Hard gates

- Header matches **this** git root. Never a different repo's name.
- Do **not** auto-ship / deploy / `/safe-ship`. Wrap-up documents; it does not go live.
- Engram: **default don't save.** Promote only a binding policy/architecture change with a stable `topic_key`. Mid-task chatter stays out.
- Do not `git pull`, merge, or switch branches.
- Do not invent anti-pattern IDs. Do not assume `~/.claude/anti-patterns.md` exists here.
- Do **not** auto-archive this repo's dated notes unless it already uses `handoffs/_archived/` **and** `handoff_*.md` names. Repos that keep `YYYY-MM-DD_*.md` as history (sharp-oracle) keep them.

## 1. Detect convention

Look at existing `handoffs/`:

| What you see | New filename |
|---|---|
| `YYYY-MM-DD_*.md` | `handoffs/YYYY-MM-DD_<short-kebab>.md` (today's date, one-line topic) |
| `handoff_*.md` | `handoffs/handoff_YYYY-MM-DD_HHMM.md` |
| neither | `handoffs/YYYY-MM-DD_wrap-up.md` |

Create `handoffs/` if missing.

## 2. Gather facts

From **this** repo only: branch, `HEAD` short + subject, version if present, `git status --short`, commits on this branch since it diverged from its upstream (or last 12 hours if no upstream).

## 3. Write

Match this repo's existing handoff shape if one is sitting there. If none, use:

```markdown
# Handoff YYYY-MM-DD — <short title>
HEAD: <sha>  Version: <version or "n/a">

## Shipped
- [real bullets, files + outcome]

## State
[where things stand. Learning / topics / todo / branches if this repo uses those lines]

## Next
1. [...]
2. [...]
3. [...]
```

Every section is real sentences. No placeholders, no "N/A" unless it is truly not applicable.

## 4. Commit (do not ship)

```
git add handoffs/<the-new-file>
git commit -m "handoff: YYYY-MM-DD — <one-line summary>"
```

Push the **current** branch if this session already pushes to origin. Do not open a PR unless the session already uses PRs for this branch.

Uncommitted other work: leave it uncommitted unless it was already meant to land; mention it under State.

## 5. Output

```
WRAP-UP
=======
File: handoffs/<file>
HEAD: <sha>
Pushed: yes|no
Engram: none saved | <topic_key if one binding save>
Next agent: /get-ready
```
