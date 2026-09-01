# Account-wide Engram + Tailscale MCP for every Cloud Agent

Cursor Cloud does **not** run account-plugin `mcp.json` (plugins are `static` skills/commands only). It also does **not** read a repo's `.cursor/mcp.json`. Cloud Agents load MCP from:

1. **Personal MCP** — MCP dropdown at https://cursor.com/agents (this Cursor account, every repo)
2. **Team MCP** — https://cursor.com/dashboard/integrations (every teammate's Cloud Agent)

A product-repo `environment.json` `start` script is per-environment. It cannot follow diamond-predictions / jobhub / a brand-new repo. Register the two stdio servers below **once** on the account. New Cloud sessions then launch them inside the VM.

Do not put tokens in the JSON. Cloud already injects `SPORT_REPO_TOKEN` and `CLOUDFLARE_API_TOKEN`. Tailscale keys stay **User** secrets (`TS_API_KEY`), never environment-scoped.

Do not point Engram at `engram-memory.com`. Worker: `https://engram-cloud.nikhouseholdr.workers.dev`.

## What to paste

Generate the live JSON from this repo (source of truth is `scripts/cloud_hq_mcp.py`):

```bash
python3 scripts/cloud_hq_mcp.py --print-mcp
```

Each server is `python3 -c <launcher> engram|tailscale`. The launcher finds `cursor-laptop-skills` under `~/.cursor/plugins/cache/*cursor-laptop-skills*` (already on Cloud when this account plugin is installed) or clones `nhouseholder/cursor-laptop-skills` with git extraheader, then execs `cloud_engram_mcp.sh` / `cloud_tailscale_mcp.py`. The wrapper self-installs the Engram binary if PATH is empty. stdout stays MCP-clean.

## Dashboard steps (once)

1. Open https://cursor.com/agents → MCP dropdown → add custom stdio **or** https://cursor.com/dashboard/integrations as a Team admin.
2. Add server `engram` from `--print-mcp` (`command` / `args` / `env.ENGRAM_CLOUD_AUTOSYNC=1`).
3. Add server `tailscale-imac` the same way (no token env).
4. Enable both for Cloud Agents. Link Team MCP to the Default team marketplace so IDE/CLI can install the same servers.
5. **Disable the marketplace Engram plugin on Cloud Agents.** That plugin is `command: engram`, which exits 127 on a VM that has not run install yet and occupies namespace `Engram` in `error`. This launcher is the Cloud Engram server.
6. Keep User secrets: `TS_API_KEY` (required for iMac SSH), optional `TAILSCALE_AUTHKEY` / `TS_OAUTH_CLIENT_SECRET`.

A **new** Cloud Agent is required after saving MCP. This running session cannot rediscover a stdio server that already failed.

## Repo files (IDE + belt)

HQ product repos also commit `.cursor/mcp.json` from `--print-mcp` so the laptop IDE matches. Cloud does not depend on that file.
