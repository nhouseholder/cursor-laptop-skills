#!/usr/bin/env bash
# Bring up Tailscale userspace networking on a Cursor Cloud VM when a key is
# already in the environment. The Cloud sibling path that always works is
# SPORT_REPO_TOKEN + GitHub API (`scripts/cloud_github_git_env.py` and
# `engine/cloud_github_siblings.py`). Do not instruct Nicholas to mint a
# Tailscale key or SSH to the iMac.
#
# Canon also lives in cursor-laptop-skills/scripts/cloud_tailscale_up.sh
# (account plugin — every Cloud Agent). Keep the two files identical.
#
# Cursor Cloud has no TUN default path that works; use userspace mode
# (https://cursor.com/docs/cloud-agent/setup — Running Tailscale).
# Do not export HTTP_PROXY/HTTPS_PROXY globally — that would send GitHub
# and Cloudflare through the tailnet and break the job.
#
# Auth: TAILSCALE_AUTHKEY if present (never echo it). Missing key: skip the
# tailnet, bind GitHub, exit 0 so `start` does not brick the VM.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

skip_tailnet() {
  log "no Tailscale credential in env — skipping tailnet."
  log "Cloud sibling path is SPORT_REPO_TOKEN + GitHub API until TS_API_KEY or TAILSCALE_AUTHKEY is present."
}

resolve_authkey() {
  if [[ -n "${TAILSCALE_AUTHKEY:-}" ]]; then
    return 0
  fi
  if [[ -n "${TS_OAUTH_CLIENT_SECRET:-}" ]]; then
    TAILSCALE_AUTHKEY="${TS_OAUTH_CLIENT_SECRET}?ephemeral=true&preauthorized=true"
    TS_ADVERTISE_TAGS="${TAILSCALE_ADVERTISE_TAGS:-tag:cursor-cloud}"
    log "using TS_OAUTH_CLIENT_SECRET for tailscale up (redacted)"
    return 0
  fi
  local mint_py="${SCRIPT_DIR}/cloud_tailscale_mint_key.py"
  if [[ -f "${mint_py}" && -n "${TS_API_KEY:-}${TAILSCALE_API_KEY:-}" ]]; then
    local minted
    minted="$(python3 "${mint_py}")" || true
    if [[ -n "${minted}" ]]; then
      TAILSCALE_AUTHKEY="${minted}"
      log "minted ephemeral Tailscale auth key via TS_API_KEY (redacted)"
      return 0
    fi
    log "TS_API_KEY present but mint returned empty"
  fi
  return 1
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
  if ! resolve_authkey; then
    skip_tailnet
    return 0
  fi
  if tailscale_cmd status --json 2>/dev/null | grep -q '"BackendState": "Running"'; then
    log "already up as ${TS_HOSTNAME}"
    return 0
  fi
  log "tailscale up hostname=${TS_HOSTNAME} (auth key redacted)"
  local -a up_args=(
    up
    --auth-key="${TAILSCALE_AUTHKEY}"
    --hostname="${TS_HOSTNAME}"
    --accept-routes
    --timeout=45s
  )
  if [[ -n "${TS_ADVERTISE_TAGS:-}" ]]; then
    up_args+=(--advertise-tags="${TS_ADVERTISE_TAGS}")
  fi
  tailscale_cmd "${up_args[@]}"
}

status_line() {
  if ! daemon_running; then
    log "tailscaled is not running"
    return 1
  fi
  tailscale_cmd status
  log "iMac MagicDNS ${IMAC_HOST} (only when the tailnet is up)"
  log "SOCKS5 localhost:${SOCKS_PORT} — set ALL_PROXY only on iMac-bound commands, never globally"
}

bind_github() {
  local env_py="${SCRIPT_DIR}/cloud_github_git_env.py"
  local probe_py="${SCRIPT_DIR}/cloud_github_siblings.py"
  if [[ -f "${env_py}" ]]; then
    local exports
    exports="$(python3 "${env_py}")" || log "github git env apply failed"
    if [[ -n "${exports}" ]]; then
      eval "${exports}"
      log "git HTTPS extraheader replaced with SPORT_REPO_TOKEN (redacted)"
    fi
  fi
  if [[ "${CLOUD_GITHUB_SKIP_PROBE:-}" == "1" ]]; then
    return 0
  fi
  if [[ -f "${probe_py}" ]]; then
    python3 "${probe_py}" --probe || log "github sibling probe failed"
  fi
}

case "${MODE}" in
  --install-only|install-only)
    install_cli
    log "CLI installed; daemon not started (no auth key needed for this mode)"
    ;;
  --status|status)
    status_line
    ;;
  --imac|imac|--jobhub|jobhub)
    if ! resolve_authkey; then
      skip_tailnet
      bind_github
      exit 0
    fi
    install_cli
    start_daemon
    bring_up
    bind_github
    if [[ "${MODE}" == "--jobhub" || "${MODE}" == "jobhub" ]]; then
      exec tailscale --socket="${SOCKET}" ssh "${IMAC_HOST}" python3 -m jobhub "${@:2}"
    fi
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
    if ! resolve_authkey; then
      skip_tailnet
      bind_github
      exit 0
    fi
    install_cli
    start_daemon
    bring_up
    status_line || true
    bind_github
    ;;
  *)
    log "usage: $0 [up|--install-only|--status|--imac|--jobhub|--dry-check]"
    exit 2
    ;;
esac
