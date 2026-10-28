# cursor-laptop-skills

Slash commands for **every** Cursor Cloud Agent, on **every** repo, after one account install.

Laptop `~/.cursor/commands` and `~/.claude/skills` never copy onto Cloud VMs. Cloud `/` indexes:

1. Built-ins
2. **This repo's** `.cursor/commands` + `.cursor/skills` (this repo only)
3. **Account plugins** (all repos)

This plugin is (3). Do not vendor copies into product repos.

## Slash commands

| Slash | When |
|---|---|
| `/kg` (`/keep-going`) | Keep going. Audit open work, pick the highest-leverage task, implement it, verify. Do not pause for routine confirmation. |
| `/fybr` | Follow your best recommendation. Pick one course and execute. Do not interview. |
| `/get-ready` | Session start, **read-only**. Engram standing decisions + recent `handoffs/`. Never write a handoff. |
| `/wrap-up` | Session end. Lean handoff in **this** project's `handoffs/`. Saves standing memory to the existing **Engram MCP**. Does not auto-ship. |
| `/understand-and-refactor` | First session on an unfamiliar product repo. Map, then highest-ROI refactors. `--report-only` maps only. |
| `/performance-optimize` | Slowness, memory, extra rendering. Measurable target required. `--report-only` baselines only. |
| `/clean-architecture-rebuild` | Same behavior; new seams / folders / decoupling. `--report-only` proposes the folder plan. |
| `/handoff` | Full session close: bug scan, commit sweep, version bump, project log, handoff file, roadmap. Heavier than `/wrap-up`. |
| `/whats-next` | Strategic prioritizer. Scores impact vs effort vs confidence vs decay against the north star, and audits its own prior calls. |
| `/code-review` | Review changes since a fixed point on two axes — repo coding standards, and match to what the issue asked for. |
| `/confidence-check` | Pre-execution gate. Scores readiness on 5 criteria; under 70% it stops and asks rather than building the wrong thing. |
| `/estimate` | Effort, time and complexity breakdown with confidence intervals. Does not start work. |
| `/reflect` | Mid-session or closing retrospective: what got done versus the original goal, and what drifted. |
| `/grilling` | Stress-test a plan or decision by arguing against it relentlessly. |
| `/grill-me` | Relentless interview that sharpens a plan or design. Runs `/grilling`. |
| `/tdd` | Red-green loop with seams agreed up front; what a test worth keeping looks like. Also loads on "red-green-refactor". |
| `/diagnosing-bugs` | Hard bugs and regressions: build a tight pass/fail loop first, then hypothesise. Also loads on "debug this". |
| `/codebase-design` | Deep-module vocabulary: seam, depth, leverage, locality. Reference, not a session. |
| `/domain-modeling` | Sharpen terms, write `GLOSSARY.md` and sparing ADRs as they crystallise. |
| `/to-spec` | Synthesise the conversation into a spec (no interview) and publish it. |
| `/to-tickets` | Break a spec or plan into tracer-bullet tickets with blocking edges. |
| `/handoff-brief` | Compact this conversation into a short doc in `$TMPDIR` for a fresh agent. Not `/handoff` (7-phase close) and not `/wrap-up`. |
| `/wait-what` | The last message did not land: re-pitch it in plain language. |
| `/ponytail` | Laziest solution that works (YAGNI, stdlib first). `/ponytail lite\|full\|ultra`; off with "stop ponytail". Also loads on "be lazy" / "yagni". |
| `/i-have-adhd` | Action-first output shape for the rest of the session; off with "stop adhd mode". |
| `/debate` | Formal 3-round debate against Gemini as challenger, ending in a verdict. Needs a backend key; says so plainly if absent. |

### Folded-in skills (no separate plugins needed)

These came from three third-party packs, trimmed to the keepers. Do **not** install the packs for these workflows; if they are still installed, remove them so names do not collide.

| Source | Skills here |
|---|---|
| `i-have-adhd` plugin by Ayoub G. (MIT) | `i-have-adhd` |
| `ponytail` plugin by Dietrich Gebert (MIT), main skill only | `ponytail` (not audit / debt / gain / help / review) |
| [mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock (MIT) | `grill-me`, `grilling`, `tdd`, `diagnosing-bugs`, `codebase-design`, `domain-modeling`, `to-spec`, `to-tickets`, `code-review`, `wait-what`, and `handoff` as `handoff-brief` |

Local edits: Codex/Gemini agent manifests dropped; `/setup-matt-pocock-skills` and "Skill tool" references replaced (tracker = GitHub via the GitHub MCP, else local `.scratch/` files); `handoff` renamed `handoff-brief` because `/handoff` is already the 7-phase close above; `i-have-adhd` never hands you a command an agent can run itself.

Skills that back those slashes set `disable-model-invocation: true` on purpose — they load when you type `/`, not as silent always-on rules. Exceptions that **are** always-on:

- `skills/engram-save/SKILL.md` — `mem_save` during the session, not only at wrap-up
- `skills/tailscale-cloud/SKILL.md` — Tailscale userspace, JobHub on `nicholass-imac`, GitHub extraheader fix, Cloudflare tokens already on Cloud
- `skills/hq-law/SKILL.md` — the standing law from `~/AGENTS.md`, which no container ever sees: done means done, unknown is never a value, every posted pick real-money safe, never tell Nick to run a terminal command

Model-invocable by description (also have a `/` command): `tdd`, `diagnosing-bugs`, `codebase-design`, `domain-modeling`, `ponytail`. Their descriptions are the only always-on cost.

## Cloud HQ (every Cloud Agent, every repo)

Cursor Cloud does **not** run this plugin's `mcp.json` (Cloud enables the plugin as skills/commands only) and does **not** read a repo `.cursor/mcp.json`. MCP for Cloud Agents is **account/team dashboard**:

1. Paste the output of `python3 scripts/cloud_hq_mcp.py --print-mcp` (two servers: `engram`, `tailscale-imac`) as personal MCP (https://cursor.com/agents) **and** Team MCP (https://cursor.com/dashboard/integrations). This is the **only** recommended Cloud registration for Grok Bot and every other host too. Exact steps: `docs/CLOUD_ACCOUNT_MCP.md`. Re-paste after every release that changes `scripts/`: the JSON embeds them.
2. Disable the marketplace Engram plugin on Cloud Agents. It can conflict with the launcher: `command: engram` exits 127 on a VM that has not installed yet and leaves namespace `Engram` in `error`. The launcher is the Cloud Engram server.
3. Cursor **User** secrets `TS_API_KEY` / `TAILSCALE_AUTHKEY` when injected. If they are not, `cloud_tailscale_hydrate.sh` GETs private R2 `prompt-betting-engram/tailscale.env` with `CLOUDFLARE_API_TOKEN`. Do not ask Nicholas to re-paste a Tailscale key.
4. Product-repo `"start": "bash scripts/cloud_agent_start.sh"` is still useful (Engram on PATH + `engram serve` + Tailscale userspace) but it is **per environment**. The dashboard MCP is what follows a brand-new repo.

The launcher looks for the scripts in this order and never needs `PLUGIN_ROOT`: `$CURSOR_LAPTOP_SKILLS_ROOT`, `~/.local/share/cursor-laptop-skills`, the newest `~/.cursor/plugins/cache/*cursor-laptop-skills*` tree, `~/.local/lib/engram`, `./scripts`, `/workspace/scripts`. If none has them it writes the copies **embedded in the pasted JSON** to `~/.local/lib/engram` and execs those. A time-bounded `git clone` (`SPORT_REPO_TOKEN` extraheader) is the last resort, never the first. `python3 scripts/cloud_hq_mcp.py --plant` (or `scripts/cloud_plant_hq_mcp.sh`) pre-seeds `~/.local/lib/engram` and, for hosts that hard-code `/workspace/scripts/cloud_tailscale_mcp.py`, adds git-excluded symlinks there when the path is free. GitHub (`SPORT_REPO_TOKEN`) and Cloudflare (`CLOUDFLARE_API_TOKEN`) already inject. JobHub MCP is read-only; Tailscale MCP tools `imac_exec` / `jobhub` SSH to the iMac. `eval "$(python3 scripts/cloud_github_git_env.py)"` replaces Cloud's stale git bearer extraheader. iMac MagicDNS: `nicholass-imac`. Do not export `HTTP_PROXY` globally. Do not put keys in a repo.


## Engram Cloud MCP (this plugin)

`mcp.json` launches `scripts/cloud_engram_mcp.sh mcp --tools=agent` with `ENGRAM_CLOUD_AUTOSYNC=1`. That is the same Gentleman-Programming agent profile (`mem_save` / `mem_search` / `mem_session_summary`). Do not add a second memory product (not `engram-memory.com`).

The wrapper **self-heals**: if `~/.local/libexec/engram` is missing it runs `cloud_install_engram.sh` (Linux amd64/arm64 and Darwin amd64/arm64, sha256-pinned) then hydrates Cloud autosync. stdout stays MCP-clean. A missing binary must never leave the Engram namespace in `error`.

Cloud token and server URL are **not** in git. `scripts/cloud_engram_hydrate.sh` reads private R2 `prompt-betting-engram/client.json` with `CLOUDFLARE_API_TOKEN` (already injected on Cloud) and writes `~/.engram/cloud.json` mode `0600`. Worker: `https://engram-cloud.nikhouseholdr.workers.dev` (`GET /health` → `{"status":"ok","service":"engram-cloud"}`). The installer also writes global `~/.cursor/mcp.json` from `cloud_hq_mcp.py --print-mcp` (desktop + Cloud) and, on macOS, a KeepAlive LaunchAgent for `engram serve`. Cloud Agents still need that same JSON saved in the MCP dropdown — `~/.cursor/mcp.json` on the VM is not the dashboard.

A local SQLite without that hydrate is not the iMac store.

## Tailscale iMac MCP (this plugin)

`mcp.json` also launches `scripts/cloud_tailscale_mcp.py`. Tools: `tailscale_status`, `tailscale_up`, `imac_exec`, `jobhub`. Initialize succeeds even when `TS_API_KEY` is missing — the tools then report the skip. It speaks MCP stdio and answers in the framing the host used: newline-delimited JSON (the MCP spec; Grok Bot) or `Content-Length` frames. Before 1.8.0 it always answered with `Content-Length` frames, which a newline-delimited host cannot read: initialize "timed out" while the script was healthy. The installer merges `tailscale-imac` into `~/.cursor/mcp.json` next to Engram. Cloud hydrates `TS_API_KEY` from private R2 when the User secret is not injected. Never environment-scope those keys. Never put them in git.

## Install (required once, on the Cursor account)

Until this is installed on the **account**, Cloud `/` will not list these commands.

1. Cursor desktop → **Customize → Plugins**
2. Add GitHub repo: `https://github.com/nhouseholder/cursor-laptop-skills`
3. Enable it for Cloud Agents (account or team), not only this workspace
4. Start a **new** Cloud session — the current one will not retroactively grow its `/` menu

Team Marketplace import of this private repo works the same if you share it with the team.

A sharp-oracle environment snapshot is **not** a substitute for Team MCP. Snapshots follow that environment; they do not follow diamondpredictions / mmalogic / other repos. The dashboard MCP does.

## Update

Laptop remains canon when a skill file exists there. After a laptop edit: copy into `skills/<name>/SKILL.md` here, bump `version` in `plugin.json` and `.cursor-plugin/plugin.json`, push `main`. After any change under `scripts/`, run `python3 scripts/cloud_hq_mcp.py --write-mcp .cursor/mcp.json` (a test fails when it is stale) and re-paste the dashboard MCP. Cloud sessions pick up the new commit on next start.

## Layout

```
commands/     # what Cloud `/` indexes (name + description frontmatter)
skills/       # the protocol each command reads (incl. folded-in i-have-adhd, ponytail, Matt Pocock set)
scripts/      # Tailscale, git extraheader, Engram install/hydrate, account-wide MCP launcher (+ --plant)
tests/        # python3 -m unittest discover -s tests
docs/         # CLOUD_ACCOUNT_MCP.md — dashboard paste for every Cloud session
mcp.json      # desktop/plugin Engram Cloud MCP + Tailscale iMac MCP (Cloud ignores this)
.cursor-plugin/plugin.json
plugin.json   # Agent Plugins manifest (skills + commands + mcp)
```
