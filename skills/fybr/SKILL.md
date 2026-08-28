---
name: fybr
description: "Follow your best recommendation — pick one course, execute it, do not interview. Hand off only secrets, GUI login, or a decision you cannot make."
disable-model-invocation: true
argument-hint: "[optional constraint]"
---

# Follow your best recommendation (`/fybr`)

The user asked you to choose. Choose **one** course and execute it.

`$ARGUMENTS` is an optional constraint (path, deadline, "don't ship"). Honor it. Do not turn it into a questionnaire.

## Hard gates

- One recommendation, then action. Do not list three options and wait.
- Do not interview. Missing a secret, a GUI login, or a decision you cannot make from evidence → hand that one thing off and keep going around it.
- Stay in the current workspace. Do not hop repos.
- Do not invent product rules or deploy steps. Use the file that already owns them.
- Always-on context is rent: skip preambles, skip "here's my plan for approval," skip restating the ask.

## 1. Pick

In one short internal pass, name:

- **Course** — the single best next move given the repo, the message, and hard rules
- **Why** — one sentence of evidence (file, failing test, handoff next, user wording)
- **Won't** — the tempting alternative you are not doing

If two courses are truly tied on evidence, pick the smaller reversible one.

## 2. Tell, then do

Lead with the course in one sentence, then execute immediately. Do not wait for a thumbs-up.

## 3. Execute

Same bar as any other change: production-ready, tested when the seam has tests, no drive-by extras.

If the recommendation is "do nothing / don't merge / don't ship," say that and stop — that still counts as following the recommendation.

## 4. Done

What you did, proof it ran, what you deliberately did not do. No option menu at the end.
