---
name: tailscale-cloud
description: "ALWAYS ACTIVE on Cloud Agents. Join the tailnet in userspace, reach JobHub on nicholass-imac, fix Cloud git extraheader, use GitHub and Cloudflare APIs already injected. Do not print secrets. Do not wait to be asked."
---

# Cloud HQ (every Cursor Cloud Agent)

This plugin is installed on the **account**. Cursor has no account-wide `start` hook. What actually follows every new Cloud environment:

1. Cursor **User** secrets (not environment-scoped): `TS_API_KEY` and/or `TAILSCALE_AUTHKEY` (optional `TS_OAUTH_CLIENT_SECRET`)
2. This skill + `scripts/cloud_tailscale_up.sh` (`tailscaled --tun=userspace-networking`)
3. Product repos that opt in: `"start": "bash scripts/cloud_tailscale_up.sh"` in `.cursor/environment.json`

Already injected on Cloud for this account (do not ask Nicholas to re-paste them): `SPORT_REPO_TOKEN`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `R2_*`. GitHub MCP, Cloudflare MCP, and JobHub MCP are already connected. JobHub MCP is **read-only** (list/status/logs). Starting or repairing a job is Tailscale SSH to the iMac.

## First commands (do not skip)

```bash
SCRIPT="$(find "${HOME}/.cursor/plugins" -path '*cursor-laptop-skills*' -name cloud_tailscale_up.sh 2>/dev/null | head -n 1)"
if [[ -z "${SCRIPT}" && -f scripts/cloud_tailscale_up.sh ]]; then
  SCRIPT=scripts/cloud_tailscale_up.sh
fi
DIR="$(dirname "${SCRIPT}")"
if [[ -f "${DIR}/cloud_github_git_env.py" ]]; then
  eval "$(python3 "${DIR}/cloud_github_git_env.py")"
elif [[ -f scripts/cloud_github_git_env.py ]]; then
  eval "$(python3 scripts/cloud_github_git_env.py)"
fi
bash "${SCRIPT}"
```

Then:

```bash
bash "${SCRIPT}" --imac
bash "${SCRIPT}" --jobhub run prompt-betting.daily-ai-pipeline
# or: tailscale --socket="$HOME/.local/share/tailscale/tailscaled.sock" ssh nicholass-imac
```

HQ trees live at `/Volumes/Extreme Pro/ProjectsHQ` and `~/ProjectsHQ` on that host.

Auth resolution inside the script, in order: `TAILSCALE_AUTHKEY` → `TS_OAUTH_CLIENT_SECRET` (passed to `tailscale up` with ephemeral/preauthorized) → mint ephemeral key via `TS_API_KEY` (`scripts/cloud_tailscale_mint_key.py`). Missing all three: skip the tailnet, bind GitHub, exit 0. Do not invent a `tskey-`.

## APIs already on the agent

- **GitHub**: `SPORT_REPO_TOKEN` + GitHub MCP. Cursor injects a stale `GIT_CONFIG` bearer extraheader that 401s `git fetch`/`git push`. `eval "$(python3 …/cloud_github_git_env.py)"` replaces it with HTTP Basic. Contents API (`engine/repo_publisher.py` in prompt-betting) works without that eval.
- **Cloudflare**: `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` + Cloudflare MCP + wrangler. Never pass the token on a CLI argv.
- **JobHub**: MCP tools `list_jobs`, `job_status`, `tail_log`, `recent_failures`, `site_freshness`, `fleet_rollup`, `secrets_status`. Cannot start/stop jobs. Mutate via `--jobhub` / Tailscale SSH.

## Hard rules

- Userspace only: `tailscaled --tun=userspace-networking`. Do not try kernel TUN as the primary path.
- Never environment-scope Tailscale secrets. Never put keys in a repo, PR, log, or chat.
- Do not `export HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` globally. SOCKS is `localhost:1055` for a single iMac-bound command only.
- Do not ask Nicholas to mint keys or SSH to the iMac. If the credential is missing, skip and use GitHub/Cloudflare/JobHub MCP.
