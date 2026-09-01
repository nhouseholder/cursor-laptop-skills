#!/usr/bin/env bash
# Install Gentleman-Programming engram 1.20.0 plus a PATH wrapper that loads
# Engram Cloud autosync before `engram mcp` (account plugin and marketplace plugin).
# Linux Cloud + Darwin desktop. Idempotent. Does not print secret values.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VER="${ENGRAM_VERSION:-1.20.0}"
BIN_DEST="${HOME}/.local/libexec"
WRAP_DEST="${HOME}/.local/bin"
LIB_DEST="${HOME}/.local/lib/engram"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "${OS}-${ARCH}" in
  linux-x86_64|linux-amd64) ASSET="engram_${VER}_linux_amd64.tar.gz" ;;
  linux-aarch64|linux-arm64) ASSET="engram_${VER}_linux_arm64.tar.gz" ;;
  darwin-x86_64|darwin-amd64) ASSET="engram_${VER}_darwin_amd64.tar.gz" ;;
  darwin-arm64) ASSET="engram_${VER}_darwin_arm64.tar.gz" ;;
  *) echo "unsupported os/arch: ${OS} ${ARCH}" >&2; exit 1 ;;
esac

# sha256 of the pinned 1.20.0 GitHub release assets (checksums.txt on the tag).
declare -A PINNED_SHA256=(
  ["engram_1.20.0_linux_amd64.tar.gz"]="7dc3003318e303bee269a4772144f3ce01c8ec700bfd524aaec76770acd389ca"
  ["engram_1.20.0_linux_arm64.tar.gz"]="7eb815910a76ae6cfa9a5d0161d3701e293dcca71f7743cffa62e236e5af59af"
  ["engram_1.20.0_darwin_amd64.tar.gz"]="3b9015dcfcdd9f823eb7ad0b590b1dbc4c25bb5d81dda3f84e623709815afe80"
  ["engram_1.20.0_darwin_arm64.tar.gz"]="2363d5012f23e58878f86c3ddcc1f63cfe9dcf3eec7f413e70eaafcbb9d394cc"
)

mkdir -p "$BIN_DEST" "$WRAP_DEST" "$LIB_DEST"
export PATH="$WRAP_DEST:$PATH"

is_wrapper() {
  grep -q 'Launch the real engram binary with Engram Cloud autosync' "$1" 2>/dev/null
}

preserve_real_binary() {
  local src="$1"
  if [[ -x "${src}" ]] && ! is_wrapper "${src}"; then
    if [[ ! -x "${BIN_DEST}/engram" ]]; then
      install -m 0755 "${src}" "${BIN_DEST}/engram"
    fi
  fi
}

preserve_real_binary "${HOME}/.local/bin/engram"
preserve_real_binary /usr/local/bin/engram
preserve_real_binary /opt/homebrew/bin/engram

need_install=0
if [[ ! -x "${BIN_DEST}/engram" ]] || is_wrapper "${BIN_DEST}/engram"; then
  need_install=1
fi

_download_tarball() {
  local dest="$1"
  local url="https://github.com/Gentleman-Programming/engram/releases/download/v${VER}/${ASSET}"
  if curl -fsSL "$url" -o "$dest"; then
    return 0
  fi
  # Private R2 fallback (same pin). Token from master.env / process env.
  if [[ -z "${CLOUDFLARE_API_TOKEN:-}" && -f "${HOME}/.claude/credentials/master.env" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${HOME}/.claude/credentials/master.env"
    set +a
  fi
  if [[ -n "${CLOUDFLARE_API_TOKEN:-}" && -n "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
    local r2="https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/r2/buckets/prompt-betting-engram/objects/bootstrap/${ASSET}"
    curl -fsSL -A "Mozilla/5.0 engram-install" \
      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      "$r2" -o "$dest" && return 0
  fi
  return 1
}

if [[ "$need_install" -eq 1 ]]; then
  expected="${ENGRAM_SHA256:-${PINNED_SHA256[$ASSET]:-}}"
  if [[ -z "$expected" ]]; then
    echo "[engram] no sha256 pin for ${ASSET}; set ENGRAM_SHA256" >&2
    exit 1
  fi
  tmp="$(mktemp -d)"
  if ! _download_tarball "$tmp/engram.tgz"; then
    echo "[engram] download failed for ${ASSET}" >&2
    rm -rf "$tmp"
    exit 1
  fi
  got="$(sha256sum "$tmp/engram.tgz" | awk '{print $1}')"
  if [[ "$got" != "$expected" ]]; then
    echo "[engram] sha256 mismatch for ${ASSET}: got ${got} want ${expected}" >&2
    rm -rf "$tmp"
    exit 1
  fi
  tar -xzf "$tmp/engram.tgz" -C "$tmp"
  install -m 0755 "$tmp/engram" "${BIN_DEST}/engram"
  rm -rf "$tmp"
fi

install -m 0755 "${SCRIPT_DIR}/cloud_engram_hydrate.sh" "${LIB_DEST}/cloud_engram_hydrate.sh"
install -m 0755 "${SCRIPT_DIR}/cloud_engram_mcp.sh" "${LIB_DEST}/cloud_engram_mcp.sh"
install -m 0755 "${SCRIPT_DIR}/cloud_install_engram.sh" "${LIB_DEST}/cloud_install_engram.sh"
install -m 0755 "${SCRIPT_DIR}/write_cursor_mcp.py" "${LIB_DEST}/write_cursor_mcp.py"
install -m 0755 "${SCRIPT_DIR}/install_engram_launchd.sh" "${LIB_DEST}/install_engram_launchd.sh"
if [[ -f "${SCRIPT_DIR}/cloud_hq_mcp.py" ]]; then
  install -m 0755 "${SCRIPT_DIR}/cloud_hq_mcp.py" "${LIB_DEST}/cloud_hq_mcp.py"
fi
if [[ -f "${SCRIPT_DIR}/cloud_hq_mcp.sh" ]]; then
  install -m 0755 "${SCRIPT_DIR}/cloud_hq_mcp.sh" "${LIB_DEST}/cloud_hq_mcp.sh"
fi
if [[ -f "${SCRIPT_DIR}/cloud_tailscale_mcp.py" ]]; then
  install -m 0755 "${SCRIPT_DIR}/cloud_tailscale_mcp.py" "${LIB_DEST}/cloud_tailscale_mcp.py"
fi
if [[ -f "${SCRIPT_DIR}/cloud_tailscale_hydrate.sh" ]]; then
  install -m 0755 "${SCRIPT_DIR}/cloud_tailscale_hydrate.sh" "${LIB_DEST}/cloud_tailscale_hydrate.sh"
fi
if [[ -f "${SCRIPT_DIR}/cloud_tailscale_up.sh" ]]; then
  install -m 0755 "${SCRIPT_DIR}/cloud_tailscale_up.sh" "${LIB_DEST}/cloud_tailscale_up.sh"
fi
if [[ -f "${SCRIPT_DIR}/cloud_tailscale_mint_key.py" ]]; then
  install -m 0755 "${SCRIPT_DIR}/cloud_tailscale_mint_key.py" "${LIB_DEST}/cloud_tailscale_mint_key.py"
fi
install -m 0755 "${SCRIPT_DIR}/cloud_engram_mcp.sh" "${WRAP_DEST}/engram"
if [[ -d /usr/local/bin ]] && sudo -n true >/dev/null 2>&1; then
  sudo install -m 0755 "${SCRIPT_DIR}/cloud_engram_mcp.sh" /usr/local/bin/engram
  sudo mkdir -p /usr/local/libexec
  sudo install -m 0755 "${BIN_DEST}/engram" /usr/local/libexec/engram
fi

if [[ -f "${HOME}/.profile" ]] && ! grep -q '.local/bin' "${HOME}/.profile"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.profile"
fi

bash "${SCRIPT_DIR}/cloud_engram_hydrate.sh" >/dev/null || true
ENGRAM_WRAP_BIN="${WRAP_DEST}/engram" python3 "${SCRIPT_DIR}/write_cursor_mcp.py" >&2 || true
bash "${SCRIPT_DIR}/install_engram_launchd.sh" || true

command -v engram >&2
"${BIN_DEST}/engram" version >&2
