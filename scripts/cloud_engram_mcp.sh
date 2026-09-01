#!/usr/bin/env bash
# Launch the real engram binary with Engram Cloud autosync env loaded.
# Used as:
#   1. Cursor account plugin MCP command (mcp.json)
#   2. PATH wrapper installed by cloud_install_engram.sh so the marketplace
#      Engram plugin (`engram mcp --tools=agent`) autosyncs too
#
# Self-heals: if the binary is missing, install it. Never exit 127 — that is
# how Cloud Engram stayed down. stdout stays MCP-clean (install logs on stderr).
# Does not print secret values.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBEXEC="${ENGRAM_BIN:-${HOME}/.local/libexec/engram}"
HYDRATE="${SCRIPT_DIR}/cloud_engram_hydrate.sh"
INSTALLER="${SCRIPT_DIR}/cloud_install_engram.sh"
if [[ ! -x "${HYDRATE}" && -x "${HOME}/.local/lib/engram/cloud_engram_hydrate.sh" ]]; then
  HYDRATE="${HOME}/.local/lib/engram/cloud_engram_hydrate.sh"
fi
if [[ ! -x "${INSTALLER}" && -x "${HOME}/.local/lib/engram/cloud_install_engram.sh" ]]; then
  INSTALLER="${HOME}/.local/lib/engram/cloud_install_engram.sh"
fi

is_wrapper() {
  grep -q 'Launch the real engram binary with Engram Cloud autosync' "$1" 2>/dev/null
}

pick_real_binary() {
  local cand rest
  rest="${ENGRAM_BIN_CANDIDATES:-}"
  if [ -z "${rest}" ]; then
    rest="${ENGRAM_BIN:-}:${HOME}/.local/libexec/engram:/usr/local/libexec/engram:/opt/homebrew/bin/engram:/usr/local/bin/engram-bin:${HOME}/.local/bin/engram.bin:/usr/local/bin/engram:/opt/homebrew/opt/engram/bin/engram"
  fi
  while [ -n "${rest}" ]; do
    cand="${rest%%:*}"
    if [ "${rest}" = "${cand}" ]; then
      rest=""
    else
      rest="${rest#*:}"
    fi
    if [ -n "${cand}" ] && [ -x "${cand}" ] && ! is_wrapper "${cand}"; then
      printf '%s' "${cand}"
      return 0
    fi
  done
  return 1
}

if ! LIBEXEC="$(pick_real_binary)"; then
  if [[ -x "${INSTALLER}" ]]; then
    echo "[engram-cloud] binary missing; installing" >&2
    bash "${INSTALLER}" >/dev/null || true
  fi
  if ! LIBEXEC="$(pick_real_binary)"; then
    echo "[engram-cloud] real binary still missing after install" >&2
    exit 127
  fi
fi

if [[ -x "${HYDRATE}" ]]; then
  bash "${HYDRATE}" >/dev/null || true
fi

CLOUD_JSON="${ENGRAM_DATA_DIR:-${HOME}/.engram}/cloud.json"
if [[ -f "${CLOUD_JSON}" ]]; then
  eval "$(python3 - "${CLOUD_JSON}" <<'PY'
import json, shlex, sys
raw = json.loads(open(sys.argv[1]).read())
server = str(raw.get("server_url") or "").strip()
token = str(raw.get("token") or "").strip()
if server and token:
    print(f"export ENGRAM_CLOUD_SERVER={shlex.quote(server)}")
    print(f"export ENGRAM_CLOUD_TOKEN={shlex.quote(token)}")
    print("export ENGRAM_CLOUD_AUTOSYNC=1")
PY
)"
fi

export ENGRAM_CLOUD_AUTOSYNC="${ENGRAM_CLOUD_AUTOSYNC:-1}"
exec "${LIBEXEC}" "$@"
