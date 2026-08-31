#!/usr/bin/env bash
# Bring up Tailscale userspace networking on a Cursor Cloud VM.
#
# Canon also lives in cursor-laptop-skills/scripts/cloud_tailscale_up.sh
# (account plugin — every Cloud Agent). Keep the two files identical.
#
# Cursor Cloud has no TUN default path that works; use userspace mode
# (https://cursor.com/docs/cloud-agent/setup — Running Tailscale).
# Do not export HTTP_PROXY/HTTPS_PROXY globally — that would send GitHub
# and Cloudflare through the tailnet and break the job.
#
# Auth: User secret TAILSCALE_AUTHKEY (Runtime Secret). Never echo it.
# Missing key: print a loud skip and exit 0 so `start` does not brick the VM.
set -euo pipefail

STATE_DIR="${TAILSCALE_STATE_DIR:-${HOME}/.local/share/tailscale}"
SOCKS_PORT="${TAILSCALE_SOCKS_PORT:-1055}"
HTTP_PROXY_PORT="${TAILSCALE_HTTP_PROXY_PORT:-1054}"
IMAC_HOST="${IMAC_TAILSCALE_HOST:-nicholass-imac}"
SHORT_HOST="$(hostname -s 2>/dev/null || echo cloud)"
TS_HOSTNAME="${TAILSCALE_HOSTNAME:-cursor-cloud-${SHORT_HOST}}"
SOCKET="${STATE_DIR}/tailscaled.sock"
PIDFILE="${STATE_DIR}/tailscaled.pid"
LOGFILE="${STATE_DIR}/tailscaled.log"
MODE="${1:-up}"

log() { printf '[cloud-tailscale] %s\n' "$*" >&2; }

die_no_key() {
  log "TAILSCALE_AUTHKEY missing — this Cloud VM cannot join the tailnet."
  log "Add it as a Cursor *User* secret (not environment-scoped) and start a new agent."
  log "iMac MagicDNS name remains ${IMAC_HOST}."
  exit 0
}

install_cli() {
  if command -v tailscale >/dev/null 2>&1 && command -v tailscaled >/dev/null 2>&1; then
    return 0
  fi
  if [[ "${TAILSCALE_SKIP_INSTALL:-}" == "1" ]]; then
    log "TAILSCALE_SKIP_INSTALL=1 and tailscale CLI is absent"
    return 1
  fi
  log "installing Tailscale CLI"
  curl -fsSL https://tailscale.com/install.sh | sudo sh
  command -v tailscale >/dev/null 2>&1
  command -v tailscaled >/dev/null 2>&1
}

tailscale_cmd() {
  tailscale --socket="${SOCKET}" "$@"
}

daemon_running() {
  [[ -S "${SOCKET}" ]] && tailscale_cmd status >/dev/null 2>&1
}

start_daemon() {
  mkdir -p "${STATE_DIR}"
  if daemon_running; then
    return 0
  fi
  if [[ -f "${PIDFILE}" ]] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
    return 0
  fi
  log "starting tailscaled --tun=userspace-networking socks5=:${SOCKS_PORT} http-proxy=:${HTTP_PROXY_PORT}"
  nohup tailscaled \
    --tun=userspace-networking \
    --socks5-server="localhost:${SOCKS_PORT}" \
    --outbound-http-proxy-listen="localhost:${HTTP_PROXY_PORT}" \
    --statedir="${STATE_DIR}" \
    --socket="${SOCKET}" \
    >"${LOGFILE}" 2>&1 &
  echo $! >"${PIDFILE}"
  local i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if [[ -S "${SOCKET}" ]]; then
      return 0
    fi
    sleep 0.3
  done
  log "tailscaled socket did not appear at ${SOCKET}"
  return 1
}

bring_up() {
  if [[ -z "${TAILSCALE_AUTHKEY:-}" ]]; then
    die_no_key
  fi
  if tailscale_cmd status --json 2>/dev/null | grep -q '"BackendState": "Running"'; then
    log "already up as ${TS_HOSTNAME}"
    return 0
  fi
  log "tailscale up hostname=${TS_HOSTNAME} (auth key redacted)"
  tailscale_cmd up \
    --auth-key="${TAILSCALE_AUTHKEY}" \
    --hostname="${TS_HOSTNAME}" \
    --accept-routes \
    --timeout=45s
}

status_line() {
  if ! daemon_running; then
    log "tailscaled is not running"
    return 1
  fi
  tailscale_cmd status
  log "iMac: tailscale ssh ${IMAC_HOST}"
  log "SOCKS5 localhost:${SOCKS_PORT} — set ALL_PROXY only on iMac-bound commands, never globally"
}

case "${MODE}" in
  --install-only|install-only)
    install_cli
    log "CLI installed; daemon not started (no auth key needed for this mode)"
    ;;
  --status|status)
    status_line
    ;;
  --imac|imac)
    if [[ -z "${TAILSCALE_AUTHKEY:-}" ]]; then
      die_no_key
    fi
    install_cli
    start_daemon
    bring_up
    exec tailscale --socket="${SOCKET}" ssh "${IMAC_HOST}" "${@:2}"
    ;;
  --dry-check|dry-check)
    grep -q -- '--tun=userspace-networking' "$0"
    grep -q -- '--socks5-server' "$0"
    if grep -E '^export (ALL_PROXY|HTTP_PROXY|HTTPS_PROXY)=' "$0"; then
      log "refusing: script would export a global HTTP proxy"
      exit 1
    fi
    log "dry-check ok userspace socks5=${SOCKS_PORT} imac=${IMAC_HOST} hostname=${TS_HOSTNAME}"
    ;;
  up|"")
    if [[ -z "${TAILSCALE_AUTHKEY:-}" ]]; then
      die_no_key
    fi
    install_cli
    start_daemon
    bring_up
    status_line || true
    ;;
  *)
    log "usage: $0 [up|--install-only|--status|--imac|--dry-check]"
    exit 2
    ;;
esac
