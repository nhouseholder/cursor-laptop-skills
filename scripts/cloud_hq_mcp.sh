#!/usr/bin/env bash
# Thin wrapper around cloud_hq_mcp.py for plugin mcp.json cwd=${PLUGIN_ROOT}.
# stdout stays MCP-clean. Does not print secret values.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${HERE}/cloud_hq_mcp.py" "$@"
