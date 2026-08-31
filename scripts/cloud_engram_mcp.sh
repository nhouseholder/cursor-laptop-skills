#!/usr/bin/env bash
# Launch the real engram binary with Engram Cloud autosync env loaded.
# Used as:
#   1. Cursor account plugin MCP command (mcp.json)
#   2. PATH wrapper installed by cloud_install_engram.sh so the marketplace
#      Engram plugin (`engram mcp --tools=agent`) autosyncs too
# Does not print secret values.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBEXEC="${ENGRAM_BIN:-${HOME}/.local/libexec/engram}"
HYDRATE="${SCRIPT_DIR}/cloud_engram_hydrate.sh"
if [[ ! -x "${HYDRATE}" && -x "${HOME}/.local/lib/engram/cloud_engram_hydrate.sh" ]]; then
  HYDRATE="${HOME}/.local/lib/engram/cloud_engram_hydrate.sh"
fi

if [[ ! -x "${LIBEXEC}" ]]; then
  for candidate in /usr/local/libexec/engram /usr/local/bin/engram-bin "${HOME}/.local/bin/engram.bin"; do
    if [[ -x "${candidate}" ]]; then
      LIBEXEC="${candidate}"
      break
    fi
  done
fi

if [[ ! -x "${LIBEXEC}" ]]; then
  echo "[engram-cloud] real binary missing at ${HOME}/.local/libexec/engram" >&2
  echo "[engram-cloud] run scripts/cloud_install_engram.sh" >&2
  exit 127
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
