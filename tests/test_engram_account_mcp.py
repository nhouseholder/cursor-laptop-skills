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
        ts = data["mcpServers"]["tailscale-imac"]
        self.assertEqual(ts["command"], "python3")
        self.assertEqual(ts["args"], ["./scripts/cloud_tailscale_mcp.py"])
        self.assertEqual(ts["cwd"], "${PLUGIN_ROOT}")

    def test_cursor_plugin_manifest_points_at_mcp_json(self) -> None:
        manifest = json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["mcpServers"], "./mcp.json")
        self.assertGreaterEqual(tuple(int(p) for p in manifest["version"].split(".")), (1, 5, 0))


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

    def test_wrapper_self_heals_when_binary_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            libexec = home / ".local" / "libexec"
            libexec.mkdir(parents=True)
            real = libexec / "engram"
            installer = Path(tmp) / "cloud_install_engram.sh"
            installer.write_text(
                "#!/usr/bin/env bash\n"
                f"install -m 0755 /bin/true {real}\n"
            )
            installer.chmod(0o755)
            # Place installer next to the wrapper copy used as SCRIPT_DIR.
            wrap_dir = Path(tmp) / "scripts"
            wrap_dir.mkdir()
            (wrap_dir / "cloud_install_engram.sh").write_text(installer.read_text())
            (wrap_dir / "cloud_install_engram.sh").chmod(0o755)
            wrap = wrap_dir / "cloud_engram_mcp.sh"
            wrap.write_text((SCRIPTS / "cloud_engram_mcp.sh").read_text())
            wrap.chmod(0o755)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env.pop("ENGRAM_BIN", None)
            env["ENGRAM_BIN_CANDIDATES"] = str(real)
            env["PATH"] = f"{wrap_dir}:{env['PATH']}"
            proc = subprocess.run(
                ["bash", str(wrap), "version"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(real.exists())
            self.assertIn("binary missing; installing", proc.stderr)

    def test_write_cursor_mcp_merges_without_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            cursor = home / ".cursor"
            cursor.mkdir(parents=True)
            (cursor / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "other": {"url": "https://example.test/mcp"},
                            "engram": {
                                "command": "uvx",
                                "env": {"ENGRAM_CLOUD_TOKEN": "should-drop"},
                            },
                        }
                    }
                )
            )
            wrap = home / ".local" / "bin" / "engram"
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["ENGRAM_WRAP_BIN"] = str(wrap)
            proc = subprocess.run(
                ["python3", str(SCRIPTS / "write_cursor_mcp.py")],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads((cursor / "mcp.json").read_text())
            self.assertEqual(data["mcpServers"]["other"]["url"], "https://example.test/mcp")
            engram = data["mcpServers"]["engram"]
            self.assertEqual(engram["command"], str(wrap))
            self.assertEqual(engram["args"], ["mcp", "--tools=agent"])
            self.assertEqual(engram["env"]["ENGRAM_CLOUD_AUTOSYNC"], "1")
            self.assertNotIn("ENGRAM_CLOUD_TOKEN", json.dumps(data))
            self.assertNotIn("should-drop", json.dumps(data))
            ts = data["mcpServers"]["tailscale-imac"]
            self.assertEqual(ts["command"], "python3")
            self.assertTrue(str(ts["args"][0]).endswith("cloud_tailscale_mcp.py"))

    def test_installer_pins_darwin_and_linux(self) -> None:
        text = (SCRIPTS / "cloud_install_engram.sh").read_text()
        self.assertIn("engram_1.20.0_darwin_arm64.tar.gz", text)
        self.assertIn("engram_1.20.0_darwin_amd64.tar.gz", text)
        self.assertIn("engram_1.20.0_linux_amd64.tar.gz", text)
        self.assertIn("2363d5012f23e58878f86c3ddcc1f63cfe9dcf3eec7f413e70eaafcbb9d394cc", text)

    def test_launchd_skipped_on_linux(self) -> None:
        proc = subprocess.run(
            ["bash", str(SCRIPTS / "install_engram_launchd.sh")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("launchd skipped (not Darwin)", proc.stderr)


if __name__ == "__main__":
    unittest.main()
