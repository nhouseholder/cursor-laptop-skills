#!/usr/bin/env python3
"""Merge Engram Cloud + Tailscale iMac stdio MCP into ~/.cursor/mcp.json. No secrets."""
from __future__ import annotations

import importlib.util
import json
import os
import stat
from pathlib import Path


def _hq():
    spec = importlib.util.spec_from_file_location(
        "_cloud_hq_mcp",
        Path(__file__).resolve().parent / "cloud_hq_mcp.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cloud_hq_mcp.py missing next to write_cursor_mcp.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    home = Path(os.environ.get("HOME") or Path.home())
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
    account = _hq().account_mcp_document()["mcpServers"]
    servers["engram"] = account["engram"]
    servers["tailscale-imac"] = account["tailscale-imac"]
    blob = json.dumps(data, indent=2) + "\n"
    path.write_text(blob)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    print(f"[engram-cloud] wrote {path} launcher=cloud_hq_mcp.py", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
