#!/usr/bin/env python3
"""stdio MCP: Tailscale userspace + SSH to nicholass-imac.

Discovery always succeeds. Missing TS_API_KEY / TAILSCALE_AUTHKEY is a tool
error, never an initialize failure. Does not print secret values.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROTOCOL = "2024-11-05"
SERVER_NAME = "tailscale-imac"
IMAC = os.environ.get("IMAC_TAILSCALE_HOST", "nicholass-imac")
_REDACT = re.compile(
    r"(tskey-[A-Za-z0-9-]+|Bearer\s+\S+|"
    r"(?:CLOUDFLARE_API_TOKEN|TAILSCALE_AUTHKEY|TS_API_KEY|TS_OAUTH_CLIENT_SECRET|"
    r"ENGRAM_CLOUD_TOKEN|SPORT_REPO_TOKEN)=[^\s]+)",
    re.IGNORECASE,
)

TOOLS = [
    {
        "name": "tailscale_status",
        "description": (
            f"Tailscale userspace status on this Cloud VM and whether {IMAC} is in view."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "tailscale_up",
        "description": (
            "Join the tailnet in userspace (mint ephemeral key via TS_API_KEY when present)."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "imac_exec",
        "description": (
            f"Run a command on {IMAC} over Tailscale SSH as nicholashouseholder. "
            "HQ trees: /Volumes/Extreme Pro/ProjectsHQ and ~/ProjectsHQ."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Remote argv/command string passed to Tailscale SSH.",
                }
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
    {
        "name": "jobhub",
        "description": (
            f"Run `python -m jobhub …` on {IMAC} via Tailscale SSH (start/stop/repair jobs)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "string",
                    "description": "Arguments after `python -m jobhub`, e.g. `run prompt-betting.daily-ai-pipeline --dry-run`.",
                }
            },
            "required": ["args"],
            "additionalProperties": False,
        },
    },
]


def redact(text: str) -> str:
    return _REDACT.sub("[redacted]", text)


def find_up_script() -> Optional[Path]:
    env = os.environ.get("TAILSCALE_UP_SCRIPT")
    if env:
        p = Path(env)
        if p.is_file():
            return p
    here = Path(__file__).resolve().parent
    home = Path(os.environ.get("HOME") or Path.home())
    candidates: List[Path] = [
        here / "cloud_tailscale_up.sh",
        home / ".local" / "lib" / "engram" / "cloud_tailscale_up.sh",
        Path("/workspace/scripts/cloud_tailscale_up.sh"),
    ]
    plugins = home / ".cursor" / "plugins"
    if plugins.is_dir():
        candidates.extend(sorted(plugins.glob("**/scripts/cloud_tailscale_up.sh")))
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def run_up(args: List[str], timeout: int = 90) -> Tuple[int, str]:
    script = find_up_script()
    if script is None:
        return 1, "cloud_tailscale_up.sh not found on this VM"
    env = os.environ.copy()
    env.setdefault("CLOUD_GITHUB_SKIP_PROBE", "1")
    try:
        proc = subprocess.run(
            ["bash", str(script), *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 1, f"timed out after {timeout}s: {' '.join(args)}"
    out = redact((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, out or f"exit {proc.returncode}"


def tool_result(text: str, is_error: bool = False) -> Dict[str, Any]:
    return {
        "content": [{"type": "text", "text": redact(text)}],
        "isError": is_error,
    }


def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name == "tailscale_status":
        code, out = run_up(["--status"], timeout=30)
        return tool_result(out, is_error=code != 0)
    if name == "tailscale_up":
        code, out = run_up(["up"], timeout=90)
        return tool_result(out, is_error=code != 0)
    if name == "imac_exec":
        command = str(arguments.get("command") or "").strip()
        if not command:
            return tool_result("imac_exec requires command", is_error=True)
        code, out = run_up(["--imac", command], timeout=120)
        return tool_result(out, is_error=code != 0)
    if name == "jobhub":
        raw = str(arguments.get("args") or "").strip()
        if not raw:
            return tool_result("jobhub requires args", is_error=True)
        extra = raw.split()
        code, out = run_up(["--jobhub", *extra], timeout=180)
        return tool_result(out, is_error=code != 0)
    return tool_result(f"unknown tool: {name}", is_error=True)


def handle_request(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = str(msg.get("method") or "")
    req_id = msg.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": "1.0.0"},
            },
        }
    if method == "notifications/initialized" or req_id is None:
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        name = str(params.get("name") or "")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        return {"jsonrpc": "2.0", "id": req_id, "result": call_tool(name, arguments)}
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def _read_stdio_message() -> Optional[Tuple[Dict[str, Any], str]]:
    """Return (message, framing). MCP stdio is newline-delimited JSON; some hosts
    use LSP-style Content-Length frames. Reply in whichever the host sent."""
    stdin = sys.stdin.buffer
    while True:
        line = stdin.readline()
        if not line:
            return None
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(b"{"):
            return json.loads(stripped.decode("utf-8")), "line"
        length = 0
        while stripped:
            if stripped.lower().startswith(b"content-length:"):
                length = int(stripped.split(b":", 1)[1].strip())
            stripped = (stdin.readline() or b"").strip()
        body = stdin.read(length) if length else b""
        if not body:
            return None
        return json.loads(body.decode("utf-8")), "frame"


def _write_stdio_message(msg: Dict[str, Any], framing: str = "line") -> None:
    body = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    if framing == "frame":
        body = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
    else:
        body += b"\n"
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def main() -> int:
    while True:
        try:
            incoming = _read_stdio_message()
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"[tailscale-imac] bad message: {exc}", file=sys.stderr)
            continue
        if incoming is None:
            return 0
        message, framing = incoming
        if not isinstance(message, dict):
            continue
        reply = handle_request(message)
        if reply is not None:
            _write_stdio_message(reply, framing)


if __name__ == "__main__":
    raise SystemExit(main())
