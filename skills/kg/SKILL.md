---
name: kg
description: "Keep going — audit open work, pick the highest-leverage task, implement it end-to-end, verify, and report the next action. Do not pause for routine confirmation."
disable-model-invocation: true
argument-hint: "[optional focus]"
---

# Keep going (`/kg`)

Autonomous continuation. `$ARGUMENTS` is optional extra focus; otherwise pick from open work.

Do not pause for "does this look right?" on routine steps. Hand off only a secret, a GUI login, or a decision you cannot make from repo evidence.

## Hard gates

- Stay in the current workspace. Do not hop repos.
- Do not invent product rules, betting thresholds, or deploy steps. Point at the file that already owns them.
- Ship only through **this repo's** documented ship path (`AGENTS.md`, `CLAUDE.md`, a `/safe-ship` skill). Never bare `build` + wrangler. No ship path → verify and stop; do not invent a deploy.
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
2. Handoff **Next** #1, if still open.
3. `tasks/todo.md` top open item.
4. A failing test / broken verify path.

Skip taste, drive-by refactors, and parked live-work unless that is the named item.

## 3. Implement

Complete, production-ready work. Prefer TDD when the repo already tests that seam: failing characterization or unit test first, then the change, then green.

Do not leave a half-applied refactor. If the slice is too large, land one complete vertical and say what remains.

## 4. Verify and ship

- Run the tests / verify command that actually covers the change.
- If the work is complete **and** this repo documents a safe-ship / deploy pipeline, follow that pipeline. Otherwise commit (and push the working branch if this session already pushes) and stop.
- Version bumps only when this repo's ship docs say a complete change must bump them — never as decoration.

## 5. Output

Strict and short (under two minutes to read):

```
KG
==
Did: [one sentence]
Proof: [test command + result, or why not]
Next: [the single next action, <2 min to start]
```

Then stop, or loop once more only if the next item is already in scope and still the highest leverage.
