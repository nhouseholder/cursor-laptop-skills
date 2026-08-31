#!/usr/bin/env bash
# Install Gentleman-Programming engram 1.20.0 plus a PATH wrapper that loads
# Engram Cloud autosync before `engram mcp` (account plugin and marketplace plugin).
# Idempotent. Does not print secret values.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VER="${ENGRAM_VERSION:-1.20.0}"
BIN_DEST="${HOME}/.local/libexec"
WRAP_DEST="${HOME}/.local/bin"
LIB_DEST="${HOME}/.local/lib/engram"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) ASSET="engram_${VER}_linux_amd64.tar.gz" ;;
  aarch64|arm64) ASSET="engram_${VER}_linux_arm64.tar.gz" ;;
  *) echo "unsupported arch: $ARCH" >&2; exit 1 ;;
esac

# sha256 of the pinned 1.20.0 GitHub release assets (checksums.txt on the tag).
declare -A PINNED_SHA256=(
  ["engram_1.20.0_linux_amd64.tar.gz"]="7dc3003318e303bee269a4772144f3ce01c8ec700bfd524aaec76770acd389ca"
  ["engram_1.20.0_linux_arm64.tar.gz"]="7eb815910a76ae6cfa9a5d0161d3701e293dcca71f7743cffa62e236e5af59af"
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

need_install=0
if [[ ! -x "${BIN_DEST}/engram" ]]; then
  need_install=1
fi

if [[ "$need_install" -eq 1 ]]; then
  expected="${ENGRAM_SHA256:-${PINNED_SHA256[$ASSET]:-}}"
  if [[ -z "$expected" ]]; then
    echo "[engram] no sha256 pin for ${ASSET}; set ENGRAM_SHA256" >&2
    exit 1
  fi
  tmp="$(mktemp -d)"
  url="https://github.com/Gentleman-Programming/engram/releases/download/v${VER}/${ASSET}"
  curl -fsSL "$url" -o "$tmp/engram.tgz"
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

command -v engram
"${BIN_DEST}/engram" version
