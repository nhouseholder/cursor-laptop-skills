#!/usr/bin/env bash
# Hydrate ~/.claude/credentials/tailscale.env from private R2.
# Same bucket as Engram Cloud (prompt-betting-engram). Object is never in git.
# stdout stays quiet; stderr names the dest, never the key.
set -euo pipefail

MASTER_ENV="${HOME}/.claude/credentials/master.env"
BUCKET="${TAILSCALE_R2_BUCKET:-prompt-betting-engram}"
OBJECT="${TAILSCALE_R2_OBJECT:-tailscale.env}"
if [[ -n "${TAILSCALE_CREDS_FILE+x}" ]]; then
  DEST="${TAILSCALE_CREDS_FILE}"
else
  DEST="${HOME}/.claude/credentials/tailscale.env"
fi

if [[ "${TAILSCALE_SKIP_R2_HYDRATE:-}" == "1" ]]; then
  echo "[cloud-tailscale] hydrate skipped: TAILSCALE_SKIP_R2_HYDRATE=1" >&2
  exit 0
fi

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" || -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]] && [[ -f "${MASTER_ENV}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${MASTER_ENV}"
  set +a
fi

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" || -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
  echo "[cloud-tailscale] hydrate skipped: CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID missing" >&2
  exit 0
fi

if [[ -f "${DEST}" && "${TAILSCALE_FORCE_HYDRATE:-}" != "1" ]]; then
  if python3 - "${DEST}" <<'PY'
import sys
text = open(sys.argv[1]).read()
ok = any(
    line.split("=", 1)[0].strip() in ("TS_API_KEY", "TAILSCALE_API_KEY", "TAILSCALE_AUTHKEY", "TS_OAUTH_CLIENT_SECRET")
    and line.split("=", 1)[1].strip()
    for line in text.splitlines()
    if line.strip() and not line.lstrip().startswith("#") and "=" in line
)
raise SystemExit(0 if ok else 1)
PY
  then
    echo "[cloud-tailscale] hydrate skipped: ${DEST} already has a credential" >&2
    exit 0
  fi
fi

tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT
url="https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/r2/buckets/${BUCKET}/objects/${OBJECT}"
code="$(curl -sS -o "${tmp}" -w "%{http_code}" \
  -A "Mozilla/5.0 tailscale-hydrate" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  "${url}" || true)"
if [[ "${code}" != "200" ]]; then
  echo "[cloud-tailscale] hydrate skipped: R2 GET ${OBJECT} HTTP ${code:-000}" >&2
  exit 0
fi

python3 - "${tmp}" "${DEST}" <<'PY'
import os, pathlib, stat, sys

src, dest = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
text = src.read_text()
allowed = ("TS_API_KEY", "TAILSCALE_API_KEY", "TAILSCALE_AUTHKEY", "TS_OAUTH_CLIENT_SECRET")
ok = False
for line in text.splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        continue
    name, value = stripped.split("=", 1)
    if name.strip() in allowed and value.strip():
        ok = True
if not ok:
    raise SystemExit("tailscale.env missing TS_API_KEY/TAILSCALE_AUTHKEY")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(text if text.endswith("\n") else text + "\n")
os.chmod(dest, stat.S_IRUSR | stat.S_IWUSR)
print(f"[cloud-tailscale] hydrated {dest}", file=sys.stderr)
PY
