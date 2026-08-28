---
name: performance-optimize
description: "Performance engineer loop — speed, memory, scalability, extra rendering. Find the bottleneck, then ship a measured fix against an explicit target."
disable-model-invocation: true
argument-hint: "[path] [--report-only]"
---

# Performance optimize

Slowness, memory, or extra rendering with a **measurable target**. No target → agree one before changing code.

`$ARGUMENTS` is the scope (path / surface) and/or `--report-only`. `--report-only` baselines and names the bottleneck; it does not edit.

## Hard gates

- Measure first. A story about what is slow is not a baseline.
- Fix the bottleneck you measured, not a neighboring one that looks ugly.
- Re-measure the same probe after the fix. If the number did not move, revert.
- Do not trade correctness or a hard product rule for a faster path.
- Do not add a library that duplicates one already in the repo.

## 1. Target

Write one line before any profile:

- **What** is slow / fat / over-rendering (user-visible or a named job)
- **Probe** (command, trace, log field, heap snapshot — the thing you will run twice)
- **Number** (p50/p95 latency, RSS, allocs, render count, LCP/INP/CLS, query count, CPU-ms)
- **Budget** (good enough). If the user did not give one, pick a conservative budget from the probe and state it.

No probe you can run in this environment → say so and stop, or switch to a probe you can run. Do not ship an unmeasured “should be faster.”

## 2. Baseline

Run the probe. Record: command, environment, n, result. That number is the only “before.”

Frontend: DevTools/Lighthouse/trace, render counts, bundle bytes. Backend/jobs: timing around the hot function, query logs, heap, CPU profile. Rendering: how many times the expensive component/function ran per user action.

## 3. Find the bottleneck

Use the symptom tree; do not skip to a rewrite:

```
What is slow?
├── First load / TTFB / LCP     → bytes, blocking, server wait, images
├── Interaction / INP / jank    → long tasks, extra renders, layout thrash
├── After navigation            → waterfalls, refetch, cache miss
├── One API / job               → queries, locks, sync CPU, N+1, huge payloads
├── Memory growth               → unbounded cache, retained DOM/closures, giant JSON
└── Scale (n items / n markets) → O(n²), full-table walks, no pagination
```

Name **one** dominant cost with evidence (stack, query, flame, render reason). Secondary issues go on a parked list.

## 4. Report

Print: target, baseline, bottleneck + evidence, proposed fix, parked list, how you will re-measure.

`--report-only` ends here.

## 5. Fix (not `--report-only`)

Change only what the bottleneck requires. Typical moves, only when the profile points here:

- Cut extra renders (stable props, split state, skip work off-screen)
- Cut bytes / parse cost (smaller payload, less JSON, fewer round trips)
- Cut queries (batch, index, stop N+1)
- Bound memory (caps, streaming, drop caches that grow with the slate)
- Move work off the critical path (cache, defer, compute once)

No speculative memoization. No new abstraction “for later.”

## 6. Verify

Run the **same** probe. Report before → after vs budget. If it missed, either a second evidence-backed pass on the same bottleneck or revert. Add a guard when cheap (test that counts queries/renders, CI budget, log).

## Done

Target, before, after, and whether the budget cleared. Parked items named, not silently “fixed.”
