"""Account-plugin Engram Cloud MCP wiring — no live tokens, no network."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class McpManifestTests(unittest.TestCase):
    def test_plugin_mcp_launches_wrapper_with_autosync(self) -> None:
        data = json.loads((ROOT / "mcp.json").read_text())
        server = data["mcpServers"]["engram"]
        self.assertEqual(server["command"], "bash")
        self.assertEqual(
            server["args"],
            ["./scripts/cloud_engram_mcp.sh", "mcp", "--tools=agent"],
        )
        self.assertEqual(server["cwd"], "${PLUGIN_ROOT}")
        self.assertEqual(server["env"]["ENGRAM_CLOUD_AUTOSYNC"], "1")
        self.assertNotIn("ENGRAM_CLOUD_TOKEN", json.dumps(data))

    def test_cursor_plugin_manifest_points_at_mcp_json(self) -> None:
        manifest = json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["mcpServers"], "./mcp.json")
        self.assertGreaterEqual(tuple(int(p) for p in manifest["version"].split(".")), (1, 4, 0))


class HydrateTests(unittest.TestCase):
    def test_hydrate_writes_0600_cloud_json_and_hides_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp) / "engram"
            client = Path(tmp) / "client.json"
            client.write_text(
                json.dumps(
                    {
                        "server_url": "https://engram-cloud.example.test",
                        "token": "super-secret-token-value",
                    }
                )
            )
            dest = dest_dir / "cloud.json"
            env = os.environ.copy()
            env["ENGRAM_DATA_DIR"] = str(dest_dir)
            env["ENGRAM_CLOUD_FORCE_HYDRATE"] = "1"
            # Bypass Cloudflare: feed the fixture through a fake curl via PATH.
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            fake_curl = bin_dir / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\n"
                "out=''\n"
                "while [[ $# -gt 0 ]]; do\n"
                "  case \"$1\" in\n"
                "    -o) out=\"$2\"; shift 2 ;;\n"
                "    -w) shift 2 ;;\n"
                "    -A|-H) shift 2 ;;\n"
                "    -sS) shift ;;\n"
                "    *) shift ;;\n"
                "  esac\n"
                "done\n"
                f"cp {client} \"$out\"\n"
                "printf 200\n"
            )
            fake_curl.chmod(0o755)
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["CLOUDFLARE_API_TOKEN"] = "cf-test"
            env["CLOUDFLARE_ACCOUNT_ID"] = "acct-test"
            proc = subprocess.run(
                ["bash", str(SCRIPTS / "cloud_engram_hydrate.sh")],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            combined = proc.stdout + proc.stderr
            self.assertNotIn("super-secret-token-value", combined)
            self.assertTrue(dest.is_file(), msg=combined)
            written = json.loads(dest.read_text())
            self.assertEqual(written["server_url"], "https://engram-cloud.example.test")
            self.assertEqual(written["token"], "super-secret-token-value")
            mode = stat.S_IMODE(dest.stat().st_mode)
            self.assertEqual(mode, 0o600)
            self.assertIn("engram-cloud.example.test", combined)


class WrapperTests(unittest.TestCase):
    def test_wrapper_exports_autosync_and_execs_real_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            libexec = Path(tmp) / "engram.bin"
            libexec.write_text(
                "#!/usr/bin/env bash\n"
                "printf 'AUTOSYNC=%s\\n' \"${ENGRAM_CLOUD_AUTOSYNC:-}\"\n"
                "printf 'SERVER_SET=%s\\n' \"${ENGRAM_CLOUD_SERVER:+yes}\"\n"
                "printf 'TOKEN_SET=%s\\n' \"${ENGRAM_CLOUD_TOKEN:+yes}\"\n"
                "printf 'ARG=%s\\n' \"$1\"\n"
            )
            libexec.chmod(0o755)
            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            (data_dir / "cloud.json").write_text(
                json.dumps(
                    {
                        "server_url": "https://engram-cloud.example.test",
                        "token": "wrapper-secret",
                    }
                )
            )
            env = os.environ.copy()
            env["ENGRAM_BIN"] = str(libexec)
            env["ENGRAM_DATA_DIR"] = str(data_dir)
            env.pop("ENGRAM_CLOUD_TOKEN", None)
            env.pop("ENGRAM_CLOUD_SERVER", None)
            env.pop("ENGRAM_CLOUD_AUTOSYNC", None)
            proc = subprocess.run(
                ["bash", str(SCRIPTS / "cloud_engram_mcp.sh"), "mcp", "--tools=agent"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("AUTOSYNC=1", proc.stdout)
            self.assertIn("SERVER_SET=yes", proc.stdout)
            self.assertIn("TOKEN_SET=yes", proc.stdout)
            self.assertIn("ARG=mcp", proc.stdout)
            self.assertNotIn("wrapper-secret", proc.stdout)
            self.assertNotIn("wrapper-secret", proc.stderr)


if __name__ == "__main__":
    unittest.main()
