---
name: tailscale-cloud
description: "ALWAYS ACTIVE on Cloud Agents. Join Nicholas's tailnet in userspace mode and reach the iMac at nicholass-imac. First command on a Cloud VM: run the plugin script scripts/cloud_tailscale_up.sh. Do not wait to be asked. Do not print TAILSCALE_AUTHKEY."
---

# Tailscale on every Cursor Cloud Agent

This plugin is installed on the **account**, so this skill loads on every Cloud repo. Cursor does not have an account-wide `start` hook; this skill plus User secret `TAILSCALE_AUTHKEY` is what follows new environments.

## First command (do not skip)

```bash
SCRIPT="$(find "${HOME}/.cursor/plugins" -path '*cursor-laptop-skills*' -name cloud_tailscale_up.sh 2>/dev/null | head -n 1)"
if [[ -z "${SCRIPT}" && -f scripts/cloud_tailscale_up.sh ]]; then
  SCRIPT=scripts/cloud_tailscale_up.sh
fi
bash "${SCRIPT}"
```

Then talk to the iMac:

```bash
bash "${SCRIPT}" --imac
# or: tailscale --socket="$HOME/.local/share/tailscale/tailscaled.sock" ssh nicholass-imac
```

HQ trees live at `/Volumes/Extreme Pro/ProjectsHQ` on that host (diamond-predictions, soccer-ai, and the rest).

## Hard rules

- Userspace only: `tailscaled --tun=userspace-networking` (Cursor Cloud docs). Do not try kernel TUN as the primary path.
- `TAILSCALE_AUTHKEY` is a Cursor **User** secret (Runtime Secret). Never environment-scoped. Never in a repo, PR, log, or chat.
- Do not `export HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` globally. SOCKS is `localhost:1055` for a single iMac-bound command only.
- Missing key: say so and stop. Do not fake a connection.

If `tailscale status` does not show `nicholass-imac`, the iMac is offline or Tailscale SSH is not enabled for `tag:cursor-cloud`.
