---
name: handoff
description: Explicit /handoff only — 7-phase close: bug scan → commit sweep → version bump → project log → handoff file → roadmap synthesis → final commit + deploy + verify. No phases skipped. Artifact-producing close tool, not the casual wrap-up flow.
triggers: ["/handoff", "handoff", "close session", "session close"]
disable-model-invocation: true
---

You are a senior engineering lead at Stripe.
Close every development session by executing a fixed 7-phase sequence that leaves the codebase committed, documented, versioned, deployed, and ready for an immediate next-session handoff.

**You are a senior engineering lead running a rigorous session close-out. Nothing leaves uncommitted, undocumented, or unverified — the next session starts with complete context.**

**When to use which:** default to `/wrap-up` (≤20-line handoff, no deploy enforcement) for everyday session closes. Reach for `/handoff` only when this session's work needs the heavier artifact — a version bump, an actual deploy, and post-deploy verification. `/handoff`'s structured template (Session Outcomes table, What Shipped, Bug Flags, Roadmap, Suggested Skills) intentionally runs longer than `/wrap-up`'s 20-line cap; keep it lean by holding each section to its own existing bullet limit (2–4 in Phase 4, 3–5 in Phase 6) rather than trimming the structure itself. `/write-handoff` is a legacy redirect to `close.md`.

# /handoff — Immutable Session-Close Gadget

Fixed 7-phase sequence. Run all phases in order. No phase may be skipped. If a phase fails, fix it before proceeding — do not skip forward.

---

## Phase 0 — Orient

Read context before touching anything:

```bash
git log --oneline -5
git status -sb
```

Identify project name from CWD (last path segment of `/Volumes/Extreme Pro/ProjectsHQ/<name>`) — call it `$proj`.

<!-- ⇩ META-RESOLVER — ONE implementation, in orient.sh. Do not re-inline the awk block here. ⇩ -->
Resolve this project's row from the META.md single-source-of-truth. **PRECONDITION:** `$proj` is the project name already resolved above (from the user's argument or cwd) — do **not** recompute it via `basename "$PWD"` (this skill is often run from `~`).

```bash
eval "$(~/.claude/scripts/orient.sh --meta-only "$proj")"   # sets prod_url / ver_file / deploy_cmd
```

The script already applies the sentinel: a cell is *unknown* if the row is missing OR the cell **starts with** `—` (prefix test, not equality — NBA Alg's Live URL is `— (deploy targets courtside-ai …)`), and unknown cells come back **empty**. On an empty cell, fall back to this skill's existing behavior and print: `ℹ META.md has no <field> for <proj> — run /project-repo to refresh`.

**Deploy-cmd cell is human-annotated markdown, not a bare command** (3 of 22 rows): strip one surrounding pair of code-span backticks; if it contains `→`, run it as two sequential steps; treat a trailing `⚠` or trailing `(…)` after the last backtick as a note to surface, not command text. Never `eval` the raw cell.
<!-- ⇧ END META-RESOLVER ⇧ -->

Then check which version source is canonical — **use `$ver_file` from the resolver above first** if set; otherwise fall back in order:
1. `VERSION` file at repo root
2. Root `package.json` → `"version"`
3. `CURRENT_STATE.md` → version line

Detect which project-specific files exist (used in Phase 4):
- `LEDGER.md`
- `CURRENT_STATE.md`
- `tasks/todo.md`
- `tasks/lessons.md`
- `mlb_system_registry.json` (→ diamondpredictions)
- `scripts/verify_deploy.py`
- `sync_and_deploy.py` (→ mmalogic)

State what was found (including the resolved `$prod_url` / `$deploy_cmd`, or the fallback notice) before proceeding.

---

## Phase 1 — Quick Bug Scan (60 seconds, non-blocking)

Scan changed files only:

```bash
git diff HEAD --name-only
```

For each changed file, grep for: `TODO`, `FIXME`, `HACK`, `XXX`, `print(`, `console.log(`

If `scripts/verify_deploy.py` exists:
```bash
PYTHONPATH=. python3 scripts/verify_deploy.py 2>&1 | tail -10
```

If `package.json` exists in the frontend dir:
```bash
cd mlb_predict/webapp/frontend && npm run build --silent 2>&1 | tail -3
```

**Rules:**
- Do NOT fix anything found here — flag only
- Bugs flagged here feed the roadmap in Phase 6
- Proceed regardless of findings

Output: `🔍 Bug scan: <N issues / clean>`

---

## Phase 2 — Commit Sweep

Leave no work behind:

```bash
git status -sb
```

If uncommitted changes exist:
```bash
git add -A
git commit -m "chore: session work — pre-handoff sweep $(date +%Y-%m-%d)"
```

```bash
git log origin/main..HEAD --oneline
```

If unpushed commits exist:
```bash
git push origin main
```

Confirm repo is clean before Phase 3.

---

## Phase 3 — Version Bump

1. Read current version from the canonical source identified in Phase 0
2. Compute new version: bump patch only (`X.Y.Z` → `X.Y.(Z+1)`)
3. Update **all version files that exist** in this project:

| File | Update |
|------|--------|
| `VERSION` | Replace entire contents |
| `package.json` (root) | `"version": "X.Y.Z"` |
| `mlb_predict/webapp/frontend/package.json` | `"version": "X.Y.Z"` |
| `mlb_predict/__init__.py` | `__version__ = "X.Y.Z"` |
| `mlb_predict/webapp/frontend/src/config/version.js` | `export const APP_VERSION = "X.Y.Z"` |
| `mlb_predict/webapp/frontend/public/data/version.json` | `{"version": "X.Y.Z"}` |
| `CURRENT_STATE.md` | Update version field in header |

Only update files that actually exist — do not create missing ones.

4. Commit:
```bash
git add VERSION package.json mlb_predict/__init__.py \
  mlb_predict/webapp/frontend/package.json \
  mlb_predict/webapp/frontend/src/config/version.js \
  mlb_predict/webapp/frontend/public/data/version.json \
  CURRENT_STATE.md 2>/dev/null || true
git commit -m "chore: bump version to vX.Y.(Z+1)"
```

---

## Phase 4 — Update Project-Specific Logs

Update only files that exist. Use current date and new version from Phase 3.

### LEDGER.md (if exists — diamondpredictions, courtside-ai, icebreaker-ai)
Append at the bottom:
```markdown
## YYYY-MM-DD vX.Y.Z
- <what was done bullet 1>
- <what was done bullet 2>
- <what was done bullet 3, if applicable>
```
Keep bullets specific (file names, system names, feature names). 2–4 bullets max.

### CURRENT_STATE.md (optional — demoted)
**Not mandatory on routine handoffs.** `CURRENT_STATE.md` is a milestone /
phase-close snapshot only — Engram standing decisions + `handoffs/` are the
live status path (`/get-ready` skips CURRENT_STATE).

Update it **only** when this session is an explicit phase/milestone close
(or the user asks). When you do update:
- `**Version:**` → match package.json exactly
- `**Updated:**` → today's date
- `## What just shipped` → 1–3 bullets
- `## What's next` → max 5 bullets

If neither root nor legacy `.kimi/CURRENT_STATE.md` exists, do **not** create
one on a routine wrap — skip.

### tasks/todo.md (if exists)
- Mark completed items `[x]`
- Remove items that are clearly stale or no longer relevant
- Do not invent new items

### tasks/lessons.md (if exists)
Append 1–2 entries. Non-obvious only — skip trivial fixes:
```
[YYYY-MM-DD] <what broke or surprised> | Root cause: <why> | Guard: <how to prevent>
```

### ~/.claude/session-health.jsonl (always)
Append one JSON line:
```json
{"ts":"YYYY-MM-DD","project":"<name>","corrections":<n>,"tool_calls":"~<n>","grade_avg":"none","outcome":"clean|issues","friction":"<one-line description or none>","patterns_found":<0|1>}
```
- `corrections`: count of times user corrected approach this session (0 if none recalled)
- `tool_calls`: rough estimate from session length
- `outcome`: "clean" if no bugs flagged and deploy is live; "issues" otherwise

---

## Phase 5 — Write Handoff File

Filename: `handoffs/YYYY-MM-DD_keyword1_keyword2.md`
- `keyword1_keyword2` = 2–3 lowercase underscore-separated words from handoff topic
- Version goes in the file body (## Version line below), not the filename
- Uses underscore separators (not hyphens) for consistency with the handoff naming convention

Write this exact structure:

```markdown
# Handoff — <project> — YYYY-MM-DD

**Version:** vX.Y.Z
**HEAD:** `<git rev-parse --short HEAD>`
**Production:** <prod URL if known> · confirmed YYYY-MM-DD

---

## Session Outcomes

| Item | Status |
|------|--------|
| <what was accomplished 1> | ✅ Shipped |
| <what was accomplished 2> | ✅ Shipped |

---

## What Shipped
- `<file or feature 1>` — <one-line description>
- `<file or feature 2>` — <one-line description>

## Bug Flags
<none — clean scan / or bulleted list of flagged items>

## Verification
```bash
<the command to confirm production is live / tests pass>
```

---

## Next Session Roadmap
1. <priority 1 — specific, actionable, names a file or feature>
2. <priority 2>
3. <priority 3>

## Suggested Skills
- `<skill name 1>` — <reason/trigger for next session agent to invoke this skill>
- `<skill name 2>` — <reason>
```

Then append to `handoffs/INDEX.md`:
```
- **[YYYY-MM-DD]** [filename.md](filename.md) — Handoff — YYYY-MM-DD — vX.Y.Z — <slug>
```

---

## Phase 6 — Roadmap Synthesis

Synthesize 3–5 priorities for the next session. Draw only from evidence in the current session:

**Sources (check all that apply):**
- Bugs flagged in Phase 1
- Open `[ ]` items in `tasks/todo.md`
- `git log --oneline -10` — direction of recent work
- `CURRENT_STATE.md` "What's next" section
- Any known follow-ups mentioned in the AGENTS.md or last handoff

**Rules for each roadmap item:**
- Must name a specific file, system, or feature — not "improve X"
- Must be startable in the first 5 minutes of the next session
- Must be grounded in something from this session or existing open state
- Order by urgency: blocking bugs → broken features → enhancements → research

These priorities flow into: handoff file (Phase 5) and final sign-off (Phase 7).
Optional: milestone `CURRENT_STATE.md` only on explicit phase closes.

---

## Phase 7 — Final Commit + Deploy + Verify

### 7a — Persist session memory to engram

Write **one** durable, high-signal handoff observation so a future session can recall this close even after the handoff file ages out. Save it with the `engram` CLI (pull-based, SQLite, **zero background LLM** — no worker, no MCP dependency, no API cost):

```bash
engram save "<project> vX.Y.Z YYYY-MM-DD" \
  "<curated 1–2 sentence summary: the substance of 'What Shipped' plus the top roadmap item / key decision or lesson>" \
  --type handoff --project <name>
```

Also list Engram `topic_key`s for standing decisions made/changed this session in the handoff body (or Phase 6 roadmap note). Do **not** re-save mid-session decisions that already cleared the gated Engram rule. Do **not** dump exploratory micro-choices.

- **Non-blocking:** if the binary is missing or errors, print one line and continue — never fail the handoff on a memory write.
- This is the deliberate, curated *write* path. The matching *read* path is **pull-based, not automatic**: `/get-ready` runs standing-decision search + `engram context <project>` at session start (Phase 2.5) for THIS project only. There is no global SessionStart injection — that's the anti-clog guarantee; default (non-get-ready) sessions stay clean. A lightweight Stop hook (`~/.claude/hooks/engram-session-save.py`) also writes a one-line session summary automatically, but it too calls only `engram save` (no LLM).
- Mid-task Engram posture remains **default don't save** — see Cursor rule `engram-gated-saves` / AGENTS.md memory lanes.
- (claude-mem was explicitly disabled 2026-07-08 via `"claude-mem@thedotmack": false` in `~/.claude/settings.json` `enabledPlugins` — do not call `mcp__plugin_claude-mem_mcp-search__*`; its worker daemon and chroma-mcp processes are killed and its hooks no longer fire. Mnemosyne was decommissioned 2026-07-04 — `~/.mnemosyne-venv/bin/mnemosyne` no longer exists.)

### 7a.2 — Refresh code graph (codebase-memory-mcp)

After committing code changes, the code graph index is stale. Refresh it for the next session so `/get-ready` surfaces a fresh architecture summary:

```bash
# Run the codebase-memory-mcp index_repository tool for this project.
# Use fast mode (no similarity/semantic edges) for speed — the handoff
# is already in progress; full indexing is for dedicated sessions.
```
Call `mcp__codebase-memory-mcp__index_repository` with `repo_path=<PROJECT_DIR>` and `mode=fast`.

- **Non-blocking:** if the MCP is unavailable or the index fails, print `⚠ Code graph refresh skipped — run /get-ready for full indexing` and continue. Never fail the handoff on a code graph refresh.
- This is the counterpart to the `/get-ready` Phase 3.5 code graph check — write on handoff, read on start.

### 7b — Commit all docs
```bash
git add handoffs/ tasks/lessons.md tasks/todo.md LEDGER.md
# CURRENT_STATE.md is demoted — only stage it on explicit milestone/phase closes, not routine handoffs.
git commit -m "docs: handoff YYYY-MM-DD — vX.Y.Z"
git push origin main
```

### 7c — Deploy (enforce if not already live at current version)

Uses `$prod_url` / `$deploy_cmd` resolved in Phase 0 from META.md. Check whether the live site is already at the new version (skip this check if `$prod_url` is unknown — empty or starts with `—` — and treat deploy as not-yet-done this session):
```bash
curl -s "$prod_url"/data/version.json
# or: curl -s "$prod_url"/api/version
```

**If live version == current version:** skip deploy, mark ✅ already live.

**If live version != current version (or deploy not yet done this session):** run the full deploy sequence:

1. Load credentials:
```bash
source ~/.claude/credentials/master.env
```

2. Run pre-deploy verify (if `scripts/verify_deploy.py` exists):
```bash
PYTHONPATH=. python3 scripts/verify_deploy.py 2>&1 | grep -E "error|Error|Results:"
# Must show 0 errors before continuing
```

3. Build + deploy using `$deploy_cmd` resolved from META.md in Phase 0 (per-project deploy commands now live in `~/.claude/META.md`, maintained by `/project-repo`). Parse the cell before running, per the Phase-0 resolver rules: strip one surrounding pair of code-span backticks; if it contains `→`, run it as two sequential steps (e.g. `wrangler versions upload …` → `wrangler versions deploy <uuid>@100%`); surface a trailing `⚠` or `(…)` annotation to the user rather than executing it.

If `$deploy_cmd` is unknown (empty or starts with `—`), print `ℹ META.md has no deploy cmd for <proj> — run /project-repo to refresh` and fall back to the generic:
```bash
npx wrangler pages deploy dist --project-name=<project-name> --branch=main
```

4. On EPIPE or bad_record_mac error: retry once with `NODE_OPTIONS='--import ./dns-fix.mjs'` prefix.

### 7d — Post-Deploy Verification (mandatory after every deploy)

Spawn a subagent to independently verify the live site:

> **Sub-agent task:** "Verify the live deployment at `$prod_url` (resolved from META.md in Phase 0). Make fresh HTTP requests — no cached data. Check:
> 1. `curl -s "$prod_url"/data/version.json` — does `.version` equal `<NEW_VERSION>`?
> 2. `curl -s "$prod_url"/data/picks.json` (or `/data/merged-picks.json`) — does the picks array exist and have >0 items?
> Report PASS or FAIL for each with the exact values observed."

If verification fails: report the mismatch and do NOT mark the handoff as clean.

### 7e — Sign-off output

Output to chat — exactly this format, no extra prose:

```
✅ Handoff — vX.Y.Z · <short sha>

📦 Shipped:
• <item 1>
• <item 2>

🔍 Bugs flagged: <none / N items — see handoff>

📋 Lesson: <one-liner from tasks/lessons.md>

🚀 Deploy: vX.Y.Z live at <prod-url> · verified <HH:MM>

🗺️ Next session:
1. <priority 1>
2. <priority 2>
3. <priority 3>

→ handoffs/YYYY-MM-DD_keyword1_keyword2.md
```

---

## Hard Rules

- **No phase skipped.** If Phase 1 finds bugs, note them and continue — bugs do not block the sequence.
- **No invented content.** Handoff bullets, lessons, and roadmap items must come from what actually happened this session or existing project state. Never fabricate.
- **Version bump is mandatory.** Even on a light session. Every `/handoff` increments the patch version.
- **Deploy is mandatory.** Phase 7b runs every time. If live version already matches, log it and skip the build. If it doesn't match, deploy and verify before sign-off.
- **Roadmap items must be specific.** "Investigate X" is not a roadmap item. "Run `scripts/verify_deploy.py` and fix the 3 warnings in merged-picks.json data consistency check" is.
