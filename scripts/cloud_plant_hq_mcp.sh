#!/usr/bin/env bash
# Plant HQ Engram + Tailscale stdio scripts: ~/.local/lib/engram (always) and
# git-excluded /workspace/scripts symlinks for hosts that hard-code that path.
# One implementation: cloud_hq_mcp.py --plant. Env start/install call this so the
# files exist before MCP initialize. The recommended registration stays the
# self-healing launcher from `cloud_hq_mcp.py --print-mcp`.
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cloud_hq_mcp.py" --plant
