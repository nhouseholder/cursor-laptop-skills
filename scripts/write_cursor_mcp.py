#!/usr/bin/env python3
"""Merge Engram Cloud + Tailscale iMac stdio MCP into ~/.cursor/mcp.json. No secrets."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path


def _merge_engram_env(existing: dict) -> dict:
    old_env = existing.get("env") if isinstance(existing, dict) else None
    merged = dict(old_env) if isinstance(old_env, dict) else {}
    merged["ENGRAM_CLOUD_AUTOSYNC"] = "1"
    merged.pop("ENGRAM_CLOUD_TOKEN", None)
    merged.pop("ENGRAM_CLOUD_SERVER", None)
    return merged


def main() -> int:
    home = Path(os.environ.get("HOME") or Path.home())
    wrap = Path(os.environ.get("ENGRAM_WRAP_BIN") or (home / ".local" / "bin" / "engram"))
    here = Path(__file__).resolve().parent
    ts_script = Path(
        os.environ.get("TAILSCALE_MCP_SCRIPT")
        or (here / "cloud_tailscale_mcp.py")
    )
    path = home / ".cursor" / "mcp.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text() or "{}")
            if isinstance(loaded, dict):
                data = loaded
        except json.JSONDecodeError:
            data = {}
    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        servers = {}
        data["mcpServers"] = servers
    existing = servers.get("engram") if isinstance(servers.get("engram"), dict) else {}
    servers["engram"] = {
        "command": str(wrap),
        "args": ["mcp", "--tools=agent"],
        "env": _merge_engram_env(existing if isinstance(existing, dict) else {}),
    }
    if ts_script.is_file():
        servers["tailscale-imac"] = {
            "command": "python3",
            "args": [str(ts_script)],
        }
    path.write_text(json.dumps(data, indent=2) + "\n")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    print(f"[engram-cloud] wrote {path} command={wrap}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
