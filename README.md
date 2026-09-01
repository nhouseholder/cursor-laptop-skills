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

Skills that back those slashes set `disable-model-invocation: true` on purpose — they load when you type `/`, not as silent always-on rules. Exceptions that **are** always-on:

- `skills/engram-save/SKILL.md` — `mem_save` during the session, not only at wrap-up
- `skills/tailscale-cloud/SKILL.md` — Tailscale userspace, JobHub on `nicholass-imac`, GitHub extraheader fix, Cloudflare tokens already on Cloud

## Cloud HQ (every Cloud Agent)

Cursor has **no** account-wide `start` script. What actually follows every new Cloud environment on this account:

1. Cursor **User** secrets `TS_API_KEY` and/or `TAILSCALE_AUTHKEY` (optional `TS_OAUTH_CLIENT_SECRET`) — not environment-scoped
2. This plugin skill + `scripts/cloud_tailscale_up.sh` (`tailscaled --tun=userspace-networking`). `TS_API_KEY` mints an ephemeral auth key per boot.
3. Product repos that opt in: `"start": "bash scripts/cloud_tailscale_up.sh"` in `.cursor/environment.json` so the daemon comes up at boot, not after the model reads the skill

GitHub (`SPORT_REPO_TOKEN`) and Cloudflare (`CLOUDFLARE_API_TOKEN`) already inject. JobHub MCP is read-only; `bash scripts/cloud_tailscale_up.sh --jobhub …` SSHs to the iMac to run jobs. `eval "$(python3 scripts/cloud_github_git_env.py)"` replaces Cloud's stale git bearer extraheader. iMac MagicDNS: `nicholass-imac`. Do not export `HTTP_PROXY` globally. Do not put keys in a repo.


## Engram Cloud MCP (this plugin)

`mcp.json` launches `scripts/cloud_engram_mcp.sh mcp --tools=agent` with `ENGRAM_CLOUD_AUTOSYNC=1`. That is the same Gentleman-Programming agent profile (`mem_save` / `mem_search` / `mem_session_summary`). Do not add a second memory product (not `engram-memory.com`).

The wrapper **self-heals**: if `~/.local/libexec/engram` is missing it runs `cloud_install_engram.sh` (Linux amd64/arm64 and Darwin amd64/arm64, sha256-pinned) then hydrates Cloud autosync. stdout stays MCP-clean. A missing binary must never leave the Engram namespace in `error`.

Cloud token and server URL are **not** in git. `scripts/cloud_engram_hydrate.sh` reads private R2 `prompt-betting-engram/client.json` with `CLOUDFLARE_API_TOKEN` (already injected on Cloud) and writes `~/.engram/cloud.json` mode `0600`. Worker: `https://engram-cloud.nikhouseholdr.workers.dev` (`GET /health` → `{"status":"ok","service":"engram-cloud"}`). The installer also writes global `~/.cursor/mcp.json` to the autosync wrapper (desktop + Cloud) and, on macOS, a KeepAlive LaunchAgent for `engram serve`.

A local SQLite without that hydrate is not the iMac store.

## Install (required once, on the Cursor account)

Until this is installed on the **account**, Cloud `/` will not list these commands.

1. Cursor desktop → **Customize → Plugins**
2. Add GitHub repo: `https://github.com/nhouseholder/cursor-laptop-skills`
3. Enable it for Cloud Agents (account or team), not only this workspace
4. Start a **new** Cloud session — the current one will not retroactively grow its `/` menu

Team Marketplace import of this private repo works the same if you share it with the team.

A sharp-oracle environment snapshot is **not** a substitute. Snapshots follow that environment; they do not follow diamondpredictions / mmalogic / other repos.

## Update

Laptop remains canon when a skill file exists there. After a laptop edit: copy into `skills/<name>/SKILL.md` here, bump `version` in `plugin.json` and `.cursor-plugin/plugin.json`, push `main`. Cloud sessions pick up the new commit on next start.

## Layout

```
commands/     # what Cloud `/` indexes (name + description frontmatter)
skills/       # the protocol each command reads
scripts/      # Tailscale, git extraheader, Engram install/hydrate/MCP wrapper
mcp.json      # account Engram MCP (self-healing stdio wrapper + Cloud autosync)
.cursor-plugin/plugin.json
plugin.json   # Agent Plugins manifest (skills + commands + mcp)
```
