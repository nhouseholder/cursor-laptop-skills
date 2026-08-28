---
name: clean-architecture-rebuild
description: "Same behavior; new seams / folders / decoupling. Convert code to clean architecture — separate concerns, increase modularity, reduce coupling."
disable-model-invocation: true
argument-hint: "[path] [--report-only]"
---

# Clean architecture rebuild

Behavior unchanged. New seams, folders, and decoupling so policy does not depend on I/O.

`$ARGUMENTS` is the feature / path to rebuild, and/or `--report-only`. `--report-only` proposes the folder plan and does not move code.

## Hard gates

- **Same behavior.** Inputs, outputs, errors, ordering, and side effects stay. If a test must change, the rebuild leaked a behavior change — stop.
- One writer per shared key / file remains one writer. Do not split a store and leave two combiners.
- Two sources for one fact stay a bug; the rebuild collapses them or keeps a single SoT with a named adapter.
- Do not invent layers the repo already has under another name. Match neighboring module shape.
- Do not add a library that duplicates one already in the repo.

## Vocabulary

Use these words in the plan and the code:

- **Policy** — the decision the product cares about
- **Seam** — the interface you can test through
- **Adapter** — I/O, HTTP, disk, UI, clock behind the seam
- **Inward** — adapters depend on policy; policy never imports adapters

One adapter is a hypothetical seam. Two adapters (or a test double plus production) make it real.

## 1. Scope the slice

Named feature / path → that slice. No path → ask which job is being decoupled; do not rebuild the whole repo.

Read existing docs (`AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, ADRs) so you do not reopen a decided seam.

## 2. Current coupling map

For the slice, list:

- Policy mixed into I/O (SQL in a route, fetch in a calculator, disk in a scorer)
- Folder layout vs actual dependencies (`grep`/imports, not the folder names)
- Tests that boot the world because there is no seam
- Sacred choke points already documented (do not bypass them)

## 3. Folder / seam plan

Propose the smallest plan that makes policy inward-only. Example shape — **adapt names to this repo**, do not paste a generic Clean Architecture tree into a JS worker or a Python pipeline that already has a house style:

```
<slice>/
  <policy>     # pure decisions, types, invariants
  <seam>       # ports the policy calls
  <adapter>    # HTTP, R2, SQLite, UI, clock
  <tests>      # policy tests through the seam
```

For each move: from-path, to-path, what the seam is, what stays put.

`--report-only` prints this plan and stops. No files moved.

## 4. Move (not `--report-only`)

Order:

1. Characterization tests around the current behavior if none exist.
2. Extract the seam (interface / function boundary) **in place**.
3. Move policy to the new folder; leave adapters calling in.
4. Point tests at the seam. Run them after each move.
5. Delete the hollow old file. Do not leave a re-export maze unless a public import path must stay stable — then one shim, listed in the report.

No feature work in the same change. No “while we’re here” refactors outside the plan.

## 5. Verify

- Same tests green without rewriting assertions to match new behavior.
- Policy modules do not import adapters (spot-check imports).
- Public callers still compile / run.
- One-writer and one-SoT invariants still hold.

## Done

Plan executed or (report-only) proposed. Behavior unchanged. New seam is the test surface. Extra folders that do no decoupling were not added.
