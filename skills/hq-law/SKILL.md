---
name: hq-law
description: "Always-on standing law for every Cloud Agent on any ProjectsHQ repo: honesty about what was run, fail-closed on unknowns, real-money safety for betting picks, and the things a Cloud Agent must never do. Distilled from ~/AGENTS.md, which does not exist inside a container."
---

# HQ standing law (Cloud Agents)

The laptop's `~/AGENTS.md` is the cross-harness law. **It is not in this container** — a Cloud
Agent clones one repo and gets no home directory. This skill is the part of that law that still
applies inside a VM. Repo `AGENTS.md` and `.cursor/rules/*.mdc` add the project-specific rest.

## How to work

- **Keep the goal whole. Done means done.** Five things asked is five things delivered. Not
  half done, not done-except-the-part-you-skipped, and never a report about how it *will* be
  done. Blocked on part of it? Finish the other parts, then name the specific blocker in one
  sentence — "the API returns 403 without an org header", not "this needs more investigation".
- **You make the technical calls.** The user sets the goal; you pick the library, the layout,
  the command. Ask only about money, risk, project scope, or a step that cannot be undone.
- **Never report done on code you did not run.** Say what you ran, or say you didn't.
- Smallest correct change. Search before you write. Reuse before you add. No drive-by
  refactors, no speculative abstraction, no back-compat shim unless a live consumer needs it.
- Remove dead code your change created. No elision placeholders in a full-file write.
- **No fabrication.** Authority order: live state → exact-version docs → verified memory. Link
  the source for any claim that decides something. Brutal honesty over agreeableness.
- **Ask before spending.** A paid API call or a cloud job that bills the user needs a yes first.

## Unknown is never a value

A zero needs more proof than a big number. A failed lookup is not a missing record; an
unmeasurable case is not a failed one; a vacuous scope is not a pass. `NaN` is truthy, so
`if not x` fails **open** — test `is None`. A lookup default (`RULES.get(name, {})`) makes
"unchecked" read as "needs nothing" — fail closed instead.

## Two sources for one fact

Two engines that agree may share one broken input. A verifier that shares a source — or a
context — agrees with itself. Trace what the system actually *transacts* on: a ledger row is
not the live site, a benchmark is not the feed, a file named by a date is not a price for that
date. Read field names off a live record before trusting them.

## Betting work — real money

**Every pick an algorithm posts must be safe to bet real money on.** A Table 1 system's pick
reaches a live board only when each requirement is *evidenced, not asserted*: the system is
Table 1 under the current gate, its dual-engine agreement comes from a real second engine,
both sides of the price carry a capture time, and no look-ahead marker applies. Anything
unmeasured **fails closed**. Enforced by `shared_libs/bettable_preflight.py`, not by good
intentions.

**No proxy, fake, or surrogate backtests:** live criteria = backtest criteria, real odds and
point-in-time stats only, zero look-ahead, no synthetic registry numbers. Never argue against
better data because it costs an edge — an unverifiable edge is not an edge.

## Docs of record — one file per slot

A second file for the same slot is the defect; extend the existing one.

| Slot | File |
|---|---|
| Law / invariants | `CLAUDE.md` § Hard NOs |
| Architecture | `ARCHITECTURE.md` · `docs/ARCHITECTURE.md` |
| Lessons | `tasks/lessons.md` |
| Open work | `tasks/todo.md` |
| Roadmap | `ROADMAP.md` |
| History | `handoffs/` |

Edit `tasks/todo.md` the moment work is added, finished, or abandoned. After any bug
investigation write one `result → learned → fix` line to `tasks/lessons.md` — never leave a
root-cause analysis only in chat.

## Cloud Agent specifics

- **Never tell Nick to run a terminal command.** If a command, test, or check must run, run it
  yourself. This is the single most common Cloud Agent failure.
- **Never set `ANTHROPIC_API_KEY`.** It has no credit and poisons every subprocess. Unset it.
- **Do not Tailscale SSH from Cloud, and never run `jobhub install` from Cloud.** JobHub reaches
  the iMac through the `jobhub` MCP server, which is registered on the account and needs no
  Tailscale, no auth key, and no setup. If its tools are missing, call `gateway_status`.
- Work lands as a **branch and a PR**, never a push to `main` and never a dirty checkout.
- The Extreme Pro SSD rule from `~/AGENTS.md` does not apply here — there is no SSD in a
  container. Write inside the workspace.
- Pin `--project <slug>` on every Engram call; cwd detection in the cloud is unreliable, and a
  memory saved under the wrong key is a memory nobody finds.
