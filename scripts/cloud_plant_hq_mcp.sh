#!/usr/bin/env bash
# Copy HQ Engram + Tailscale stdio scripts into ~/.local/lib/engram.
# Cloud MCP initialize races start and does not read .cursor/mcp.json.
# Install (snapshot builds) and start both call this so the files exist
# before python -c discovery, including on an old dashboard paste.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_DEST="${HOME}/.local/lib/engram"
mkdir -p "${LIB_DEST}"
for f in cloud_tailscale_mcp.py cloud_tailscale_up.sh cloud_tailscale_hydrate.sh \
         cloud_tailscale_mint_key.py cloud_engram_mcp.sh cloud_engram_hydrate.sh \
         cloud_install_engram.sh cloud_hq_mcp.py; do
  if [[ -f "${ROOT}/scripts/${f}" ]]; then
    install -m 0755 "${ROOT}/scripts/${f}" "${LIB_DEST}/${f}"
  fi
done
