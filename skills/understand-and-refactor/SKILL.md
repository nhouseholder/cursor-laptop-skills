---
name: understand-and-refactor
description: "Join an unfamiliar product repo: map architecture and data flow, then apply the highest-ROI structural / duplication / perf / maintainability refactors."
disable-model-invocation: true
argument-hint: "[path] [--report-only]"
---

# Understand and refactor

First session on an unfamiliar product repo. **Map, then change.** Do not edit until the map names the highest-ROI targets — unless the user passed a path so narrow the map is that path.

`$ARGUMENTS` is the scope: a path or subsystem, and/or `--report-only`. Default scope is the current workspace. `--report-only` maps and ranks; it does not edit.

## Hard gates

- Behavior stays the same unless the user asked for a behavior change. This skill is structure, not features.
- Prefer existing docs over re-exploring: `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, ADRs, `handoffs/`, README.
- A failed lookup is not a missing record. Prove the search can find something before reporting nothing.
- Do not invent product rules, betting thresholds, or deploy steps. Point at the file that already owns them.
- Do not add a library that duplicates one already in the repo. Search `package.json` / imports first.

## 1. Scope

- Named path / subsystem → that tree only.
- No path → whole workspace, but still start at the product surface the user cares about (app entry, API, pipeline) rather than listing every folder.
- `--report-only` present → stop after §4. No edits, no commits.

## 2. Map (write this down)

Read docs first. Then the repo:

1. Top-level layout and what each tree is for.
2. Runtime entry points (CLI, workers, HTTP, UI routes, schedulers).
3. Data flow for the main job: who writes, who reads, which store/key, which combiner.
4. Shared modules vs one-off copies.
5. Test / verify command that actually runs.

Keep the map short. Names, paths, arrows. Not a tour.

If a code-graph / memory MCP is available for this repo, use it before a repo-wide grep for symbols. Grep for exact string literals.

## 3. Rank problems

Only four buckets. Drop anything that is taste, renaming-for-renaming, or a rewrite of a working seam:

| Bucket | Look for |
|---|---|
| Structural | God modules, inverted dependencies, business rules stuck in I/O |
| Duplication | Two sources for one fact, copy-pasted gates, parallel formatters |
| Perf | Hot path doing N+1, unbounded walks, extra renders, sync work on the request path |
| Maintainability | Dead flags, undocumented invariants, tests that cannot fail, comments that lie |

Score each candidate:

- **Blast radius** — files/callers touched
- **Payoff** — fewer lies, fewer copies, cheaper hot path, safer change later
- **Proof** — how you will know it worked (test, metric, or both)

Highest ROI = high payoff, bounded blast radius, a proof. Skip “clean up the whole layer.”

## 4. Report

Print:

1. **Map** — entries, data flow, stores.
2. **Ranked list** — 3–7 items, ROI first, with proof.
3. **Do not touch** — sacred files / hard rules found in docs.
4. **First move** — the one change you would make this session.

`--report-only` ends here.

## 5. Apply (not `--report-only`)

Do the first move, then the next only if it is still the highest ROI after the first lands.

- One logical change per commit-sized chunk.
- Existing tests run; add a characterization test before moving a seam that has none.
- Hunt regressions on sibling readers of any fact you moved.
- Stop when the ranked list’s remaining items are speculative or out of scope.

## Done

The map is still accurate. The edits match the ranked list. Proof ran. No drive-by refactors outside the list.
