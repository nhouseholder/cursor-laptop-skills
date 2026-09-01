"""Tailscale iMac MCP — initialize always works; tools call the up script."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _load_mcp():
    spec = importlib.util.spec_from_file_location(
        "cloud_tailscale_mcp", SCRIPTS / "cloud_tailscale_mcp.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _frame(msg: dict) -> bytes:
    body = json.dumps(msg).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _read_all(raw: bytes) -> list[dict]:
    msgs: list[dict] = []
    while raw:
        if b"\r\n\r\n" not in raw:
            break
        header, rest = raw.split(b"\r\n\r\n", 1)
        length = 0
        for line in header.decode().splitlines():
            if line.lower().startswith("content-length:"):
                length = int(line.split(":", 1)[1].strip())
        body, raw = rest[:length], rest[length:]
        msgs.append(json.loads(body.decode("utf-8")))
    return msgs


class TailscaleMcpTests(unittest.TestCase):
    def test_initialize_and_tools_list_without_tailnet(self) -> None:
        env = os.environ.copy()
        env.pop("TAILSCALE_AUTHKEY", None)
        env.pop("TS_API_KEY", None)
        proc = subprocess.Popen(
            ["python3", str(SCRIPTS / "cloud_tailscale_mcp.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        try:
            init = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"},
                },
            }
            listed = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            out, err = proc.communicate(_frame(init) + _frame(listed), timeout=8)
        finally:
            if proc.poll() is None:
                proc.kill()
        combined = out.decode("utf-8", "replace") + err.decode("utf-8", "replace")
        self.assertNotIn("tskey-", combined)
        msgs = _read_all(out)
        self.assertGreaterEqual(len(msgs), 2, combined)
        self.assertEqual(msgs[0]["result"]["serverInfo"]["name"], "tailscale-imac")
        names = {t["name"] for t in msgs[1]["result"]["tools"]}
        self.assertEqual(names, {"tailscale_status", "tailscale_up", "imac_exec", "jobhub"})

    def test_status_tool_uses_injected_script_and_redacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "cloud_tailscale_up.sh"
            fake.write_text(
                "#!/usr/bin/env bash\n"
                "echo \"mode=$1 tskey-auth-should-not-leak\"\n"
                "exit 0\n"
            )
            fake.chmod(0o755)
            os.environ["TAILSCALE_UP_SCRIPT"] = str(fake)
            os.environ["TAILSCALE_AUTHKEY"] = "tskey-auth-unit-test-only"
            try:
                mod = _load_mcp()
                result = mod.call_tool("tailscale_status", {})
            finally:
                os.environ.pop("TAILSCALE_UP_SCRIPT", None)
                os.environ.pop("TAILSCALE_AUTHKEY", None)
            text = result["content"][0]["text"]
            self.assertIn("mode=--status", text)
            self.assertNotIn("tskey-", text)
            self.assertFalse(result["isError"])


if __name__ == "__main__":
    unittest.main()
