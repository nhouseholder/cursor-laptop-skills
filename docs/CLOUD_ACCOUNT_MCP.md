# Account-wide Engram + Tailscale MCP for every Cloud Agent

Cursor Cloud does **not** honor account-plugin `mcp.json` (the plugin ships to Cloud as skills/commands only, and `${PLUGIN_ROOT}` is not resolved for MCP). It also does **not** read a repo's `.cursor/mcp.json`. Cloud Agents load MCP from:

1. **Personal MCP** — MCP dropdown at https://cursor.com/agents (this Cursor account, every repo)
2. **Team MCP** — https://cursor.com/dashboard/integrations (every teammate's Cloud Agent)

A product-repo `environment.json` `start` script is per-environment. It cannot follow diamond-predictions / jobhub / a brand-new repo. Register the two stdio servers below **once** on the account. New Cloud sessions then launch them inside the VM.

Do not put tokens in the JSON. Cloud already injects `SPORT_REPO_TOKEN` and `CLOUDFLARE_API_TOKEN`. Tailscale keys stay **User** secrets (`TS_API_KEY`), never environment-scoped.

Do not point Engram at `engram-memory.com`. Worker: `https://engram-cloud.nikhouseholdr.workers.dev`.

## The one recommended registration

Generate the live JSON from this repo (source of truth is `scripts/cloud_hq_mcp.py`):

```bash
python3 scripts/cloud_hq_mcp.py --print-mcp
```

It prints exactly two servers: `engram` and `tailscale-imac`. Each is `python3 -c <launcher> engram|tailscale`. **This is the only recommended Cloud registration, for Cursor Cloud, Grok Bot, and any other host.** Do not register `bash ./scripts/cloud_engram_mcp.sh`, `python3 ./scripts/cloud_tailscale_mcp.py`, `${PLUGIN_ROOT}` paths, or a bare `/workspace/scripts/...` path by hand. Those exist only when that exact tree is on the VM, and they are why a host reports a timeout or exit 127.

The pasted JSON **embeds the server scripts**, so it keeps working with no plugin tree, no clone, and no `PLUGIN_ROOT`. Re-paste after any release that changes `scripts/` (the checked-in `.cursor/mcp.json` is the same JSON and a test fails when it goes stale).

### How the launcher finds the scripts

First hit wins; the plugin cache entry is the newest by mtime:

1. `$CURSOR_LAPTOP_SKILLS_ROOT`
2. `~/.local/share/cursor-laptop-skills`
3. `~/.cursor/plugins/cache/*cursor-laptop-skills*` (present on Cloud once the account plugin is installed)
4. `~/.local/lib/engram`
5. `./scripts`, then `/workspace/scripts`
6. Embedded copies, written to `~/.local/lib/engram`
7. Last resort only: `git clone` (12 s timeout, `SPORT_REPO_TOKEN` extraheader). A clone hang or 401 can no longer take the server down.

`python3 scripts/cloud_hq_mcp.py --plant` (also `scripts/cloud_plant_hq_mcp.sh`, for environment `install`/`start`) pre-seeds step 4 and, for a host that hard-codes `/workspace/scripts/cloud_tailscale_mcp.py` or `cloud_engram_mcp.sh`, adds symlinks there **only when the path is free**, listed in `.git/info/exclude` so the product repo stays clean. A host that hard-codes a path on a VM where nothing runs `--plant` still fails; point that host at the registration above.

### Tailscale timeouts

`cloud_tailscale_mcp.py` always answers `initialize`, even with no key. Before plugin 1.8.0 it replied with `Content-Length` frames to every host, but MCP stdio is newline-delimited JSON. A newline-delimited host (Grok Bot) never saw a reply line and timed out with a healthy script. It now replies in the framing the host used. The marker for the old behavior: stdout starting with `Content-Length:` after a bare `{...}\n` request.

## Dashboard steps (once)

1. Open https://cursor.com/agents → MCP dropdown → add custom stdio **or** https://cursor.com/dashboard/integrations as a Team admin.
2. Add server `engram` from `--print-mcp` (`command` / `args` / `env.ENGRAM_CLOUD_AUTOSYNC=1`).
3. Add server `tailscale-imac` the same way (no token env).
4. Replace any older paste of these two servers. Pastes from before the embedded launcher (they contain `git clone` and no `EMBEDDED`) can hang on clone.
5. Enable both for Cloud Agents. Link Team MCP to the Default team marketplace so IDE/CLI can install the same servers.
6. **Do not use the marketplace Engram plugin on Cloud Agents.** It can conflict with this launcher: that plugin is `command: engram`, which exits 127 on a VM that has not run install yet and occupies namespace `Engram` in `error`. This launcher is the Cloud Engram server. Keep marketplace Engram, if at all, for the laptop IDE.
7. Keep User secrets: `TS_API_KEY` (required for iMac SSH), optional `TAILSCALE_AUTHKEY` / `TS_OAUTH_CLIENT_SECRET`. When not injected, `cloud_tailscale_hydrate.sh` reads private R2.

A **new** Cloud Agent is required after saving MCP. This running session cannot rediscover a stdio server that already failed.

JobHub is not in this JSON. Use the `tailscale-imac` `jobhub` tool, or register the separate read-only HTTP server `https://jobhub-cloud-mcp.nikhouseholdr.workers.dev/mcp` on its own.

## Skills

Skills and slash commands (including the folded-in `i-have-adhd`, `ponytail`, and the Matt Pocock set) come from the account plugin, not from MCP. Install `cursor-laptop-skills` once on the account; see `README.md` for the list. No other skill plugin is needed for them.

## Repo files (IDE + belt)

HQ product repos can commit `.cursor/mcp.json` from `--print-mcp` so the laptop IDE matches. Cloud does not depend on that file. Regenerate this repo's copy with `python3 scripts/cloud_hq_mcp.py --write-mcp .cursor/mcp.json`.
