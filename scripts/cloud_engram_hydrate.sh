#!/usr/bin/env bash
# Point this machine's Engram CLI at the Cloudflare Worker cloud.
# Token lives in private R2 (prompt-betting-engram/client.json), not git.
# Does not print the bearer token.
set -euo pipefail

MASTER_ENV="${HOME}/.claude/credentials/master.env"
BUCKET="${ENGRAM_CLOUD_R2_BUCKET:-prompt-betting-engram}"
OBJECT="${ENGRAM_CLOUD_R2_OBJECT:-client.json}"
DEST="${ENGRAM_DATA_DIR:-${HOME}/.engram}/cloud.json"

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" || -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]] && [[ -f "${MASTER_ENV}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${MASTER_ENV}"
  set +a
fi

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" || -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
  echo "[engram-cloud] hydrate skipped: CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID missing" >&2
  exit 0
fi

if [[ -f "${DEST}" && "${ENGRAM_CLOUD_FORCE_HYDRATE:-}" != "1" ]]; then
  if python3 - "${DEST}" <<'PY'
import json, sys
raw = json.loads(open(sys.argv[1]).read())
server = str(raw.get("server_url") or raw.get("ServerURL") or "").strip()
token = str(raw.get("token") or raw.get("Token") or "").strip()
raise SystemExit(0 if server and token else 1)
PY
  then
    echo "[engram-cloud] hydrate skipped: ${DEST} already has server_url+token" >&2
    exit 0
  fi
fi

tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT
url="https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/r2/buckets/${BUCKET}/objects/${OBJECT}"
code="$(curl -sS -o "${tmp}" -w "%{http_code}" \
  -A "Mozilla/5.0 engram-hydrate" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  "${url}" || true)"
if [[ "${code}" != "200" ]]; then
  echo "[engram-cloud] hydrate skipped: R2 GET ${OBJECT} HTTP ${code:-000}" >&2
  exit 0
fi

python3 - "${tmp}" "${DEST}" <<'PY'
import json, os, pathlib, stat, sys

src, dest = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
raw = json.loads(src.read_text())
inner = raw.get("result", raw) if isinstance(raw, dict) else {}
if not isinstance(inner, dict):
    inner = raw if isinstance(raw, dict) else {}
server = str(inner.get("server_url") or inner.get("ServerURL") or raw.get("server_url") or "").strip()
token = str(inner.get("token") or inner.get("Token") or raw.get("token") or "").strip()
if not server or not token:
    raise SystemExit("client.json missing server_url/token")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps({"server_url": server, "token": token}, indent=2) + "\n")
os.chmod(dest, stat.S_IRUSR | stat.S_IWUSR)
host = server.split("/")[2] if "://" in server else server
print(f"[engram-cloud] hydrated {dest} host={host}", file=sys.stderr)
print(server)
PY
