---
name: kg
description: "Keep going — audit open work, pick the highest-leverage task, implement it end-to-end, verify, then immediately take the next highest-leverage step. Do not pause for routine confirmation. Do not stop because one commit, push, or PR landed."
disable-model-invocation: true
argument-hint: "[optional focus]"
---

# Keep going (`/kg`)

Autonomous continuation. `$ARGUMENTS` is optional extra focus; otherwise pick from open work.

Do not pause for "does this look right?" on routine steps. Hand off only a secret, a GUI login,
or a decision you cannot make from repo evidence.

**Do not stop after one unit.** A commit, a push, a merged PR, or a green test run is not the
end of `/kg`. Take the next highest-leverage step in the same turn. Repeat until the next
step is actually blocked. The `Next:` line is the instruction for the following loop
iteration, not a handoff.

## Hard gates

- Stay in the current workspace. Do not hop repos unless the user named that repo as the work.
- Do not invent product rules, betting thresholds, or deploy steps. Point at the file that already owns them.
- Ship only through **this repo's** documented ship path (`AGENTS.md`, `CLAUDE.md`, a `/safe-ship` skill). Never bare `build` + wrangler. No ship path → skip deploy and take the next in-scope step (commit, push, PR). Do not invent a deploy.
- One logical change per commit. Do not batch unrelated work.

## 1. State audit

Read, do not guess:

1. `tasks/todo.md` if it exists (open vs done).
2. Git status, current branch, last few commits.
3. Latest `handoffs/` file if present (pickup / blocked / next).
4. Recent test health if a test command is obvious from `package.json` / docs — run it only if cheap; otherwise note last known status.

Write a 5-line internal picture: where we are, what is blocked, what is already shipped.

## 2. Prioritize

Pick **one** highest-leverage item:

1. User's current message, if it named work.
2. The next step you already named in this thread.
3. Handoff **Next** #1, if still open.
4. `tasks/todo.md` top open item.
5. A failing test / broken verify path.

Skip taste, drive-by refactors, and parked live-work unless that is the named item.

## 3. Implement

Complete, production-ready work. Prefer TDD when the repo already tests that seam: failing characterization or unit test first, then the change, then green.

Do not leave a half-applied refactor. If the slice is too large, land one complete vertical and continue to the next.

## 4. Verify and ship

- Run the tests / verify command that actually covers the change.
- If the work is complete **and** this repo documents a safe-ship / deploy pipeline this host is allowed to run, follow that pipeline. Otherwise commit. Then immediately push the working branch, open or merge the PR, or start the next in-scope unit — whichever is the next highest-leverage step.
- A push, a PR, and a merge of the standing change are continuation. Do not treat them as a stop.
- Version bumps only when this repo's ship docs say a complete change must bump them — never as decoration.

## 5. Output

Strict and short (under two minutes to read):

```
KG
==
Did: [one sentence]
Proof: [test command + result, or why not]
Next: [the single next action, already executed in this turn if it was unblocked]
```

Then take `Next` in the same turn if it is still the highest leverage and not blocked. Repeat.
Stopping after one unit is the failure this skill exists to prevent.

Stop only for a secret, a GUI login, owner judgement, or a production action this host must not take. State that blocker in one line.
