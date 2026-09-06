---
name: whats-next
description: "Strategic next-action prioritizer: anchors on the project's north star, scores impact vs effort vs confidence vs decay, filters already-killed work, and audits its own prior recommendations. Triggers on 'whats next', 'what's next', 'what should i do', 'prioritize', 'what now', or /whats-next."
disable-model-invocation: true
---

You are a principal engineering lead. Do not summarize the project — **decide what moves the goal**, prove the ranking with numbers, and hold yourself accountable for what you recommended last time.

**Canonical SSOT:** `~/.gemini/config/skills/whats-next/SKILL.md`

---

## Phase 0 — Session context first

This runs **mid-session**. The session already holds the orientation (get-ready brief, work just done, errors just hit). That context is the **primary** candidate source.

- **Never re-run `/get-ready`** and never re-read what is already in context.
- Read the files in later phases **only** for what the session does not already hold.
- Resolve `$PROJECT_DIR` from the session; if genuinely ambiguous, `~/.claude/PROJECT_ALIASES.md`, then cwd, then ask.

## Phase 1 — North star (goal anchor)

One line: the goal, and the measured current value. This is what every candidate is ranked against.

- **Sports projects:** the gate is `/Volumes/Extreme Pro/ProjectsHQ/BACKTEST_VALIDATION_RULES.md` + the project's `BETTING_SYSTEM_RULES.md`. The objective is max ROI / N / profit / win% and Table 1 ACTIVE count. Current = ACTIVE count from the registry + live version.
- **Non-sports:** project `CLAUDE.md` goals section; else the newest handoff `## State`.
- **Never fabricate a goal.** If none is stated, print `North star: unstated` and make "name the north star" item #1.

Their gate decides promotion, never yours — do not invent a threshold or apply your own (`feedback_never-apply-own-thresholds`).

## Phase 2 — Candidate pool

Gather, tagging every candidate with its source:

1. Newest `handoffs/*.md` → `## Next` block
2. `tasks/todo.md` → `## Open now (auto — …)` section only
3. **This session** — unfinished work, errors hit, `ponytail:` shortcuts touched
4. **Gaps** — north star minus current state (e.g. "Rule 1 unmet: 8 systems grandfathered")
5. `tasks/lessons.md` last ~5 entries — a **Guard** line saying "not yet built" or "open question" is unfinished work by definition
6. Blocked items, failing tests, `🔴 STALE FLAG` ids

## Phase 3 — Dead-end filter

Drop any candidate that matches:

- `tasks/todo.md` → `### Closed … — do not re-open`
- project rules → `§ Where Not To Spend Time`
- memory `~/.claude/projects/-Users-nicholashouseholder/memory/projects/<stem>-*` files matching `killed|rejected|nogo|negative|exhausted`
- `tasks/experiment_log.jsonl` negative verdicts

**Never drop silently.** Every dropped candidate is listed under `Already killed` with where it died. Silent omission is how a dead end gets re-proposed next month.

## Phase 4 — Score

| Factor | Scale | Meaning |
|---|---|---|
| **Impact** | 1–10 | 8–10 = wins a Table 1 seat, protects live money, or unblocks ≥2 other items. 1–3 = hygiene. |
| **Effort** | hours | >1 day → decompose or defer; never rank a whole multi-day block. |
| **Conf** | 0–1 | Do we know *how*? <0.5 → the action becomes a **timeboxed investigation**, not a fix. |
| **Decay** | hi/med/low | hi = money live now, in-season, data window closing, or a concurrent session will conflict. |

`Score = Impact × Conf ÷ Effort_hours` · ×1.5 if decay `hi` · ×0.7 if decay `low`.

Sort descending. Max 5 rows.

## Phase 5 — Drift check (self-audit)

Read the **last line** of `$PROJECT_DIR/tasks/whats-next-ledger.jsonl`. For each prior top-3 item, classify **Done / Partial / Ignored** from `git log --since=<ledger date>` plus handoffs written since. One line of output.

If an item appears in **3+ consecutive** ledger entries and is still Ignored:

```
⚠ recommended 3× never done — it is not actually #1, or it is blocked. Decide.
```

No ledger yet → `Drift: no prior ledger`.

## Phase 6 — Output

```
## What's Next — <project> — <date>
North star: <goal> · now: <measured>
Drift:      #1 done · #2 ignored · #3 partial  [⚠ stuck: <item> ×3]

| # | Action | Impact | Effort | Conf | Decay | Score |
|---|--------|--------|--------|------|-------|-------|

### #1 — <title> [<effort>]
Why now:   <one line, tied to a named gap or the north star>
Start:     `<exact command or file:line>`
Done when: <observable check>

### Queue
2. <title> — <one line> · src: <file>
…

### Blocked
- <item> — unblock by: <single action>

### Already killed
- <candidate> — <where it died>
```

## Phase 7 — Ledger append

Append **one** line to `$PROJECT_DIR/tasks/whats-next-ledger.jsonl` (create if missing, append only, never rewrite the file):

```json
{"date":"","version":"","head":"","north_star":"","top3":[{"title":"","impact":0,"effort_h":0,"conf":0,"decay":"","score":0,"source":""}],"blocked":[],"killed":[]}
```

---

## Rules

- **≤5** ranked items. Quality over coverage.
- **#1 must be executable with zero follow-up questions.** If it isn't, it isn't #1.
- Every item **cites the file or session event** that surfaced it.
- Blocked items are listed separately and are **never** ranked.
- Conf <0.5 → phrase as a timeboxed investigation ("30 min: determine whether X"), not a fix.
- Show the score table. The owner must be able to see why #1 beat #2 and overrule it.

**Do not read:** `CURRENT_STATE.md` (stale vs handoffs/git — same rule as `/get-ready` Phase 1.3) or `~/.claude/tasks/` (unused by these projects).
