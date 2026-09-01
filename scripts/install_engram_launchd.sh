#!/usr/bin/env bash
# Keep `engram serve` alive on macOS so desktop autosync survives Cursor upgrades.
# Linux Cloud VMs skip this. Does not print secret values.
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[engram-cloud] launchd skipped (not Darwin)" >&2
  exit 0
fi

WRAP="${ENGRAM_WRAP_BIN:-${HOME}/.local/bin/engram}"
LABEL="com.nhouseholder.engram-serve"
PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="${HOME}/Library/Logs"
mkdir -p "${HOME}/Library/LaunchAgents" "${LOG_DIR}"

cat > "${PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${WRAP}</string>
    <string>serve</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>ENGRAM_CLOUD_AUTOSYNC</key>
    <string>1</string>
    <key>PATH</key>
    <string>${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/engram-serve.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/engram-serve.err</string>
</dict>
</plist>
EOF
chmod 644 "${PLIST}"

if command -v launchctl >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)" "${PLIST}" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "${PLIST}" >/dev/null 2>&1 || launchctl load -w "${PLIST}" >/dev/null 2>&1 || true
fi
echo "[engram-cloud] launchd ${LABEL} installed" >&2
