"""Account-wide Cloud HQ MCP launcher — no live tokens, no network."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _env_with_home(home: Path) -> dict:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env.pop("CURSOR_LAPTOP_SKILLS_ROOT", None)
    env.pop("CLOUD_HQ_MCP_EXEC", None)
    env.pop("SPORT_REPO_TOKEN", None)
    env.pop("GH_SPORT_TOKEN", None)
    return env


def _seed_plugin(root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "cloud_engram_mcp.sh").write_text("#!/bin/sh\necho WRAPPER\n")
    (scripts / "cloud_engram_mcp.sh").chmod(0o755)
    (scripts / "cloud_tailscale_mcp.py").write_text("print('TS')\n")


class CloudHqMcpTests(unittest.TestCase):
    def test_finds_plugin_cache_without_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            plugin = (
                home
                / ".cursor"
                / "plugins"
                / "cache"
                / "nhouseholder-cursor-laptop-skills"
                / "57751513"
                / "deadbeef"
            )
            _seed_plugin(plugin)
            hook = Path(tmp) / "exec.txt"
            env = _env_with_home(home)
            env["CLOUD_HQ_MCP_EXEC"] = str(hook)
            proc = subprocess.run(
                ["python3", str(SCRIPTS / "cloud_hq_mcp.py"), "engram"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            argv = hook.read_text().splitlines()
            self.assertEqual(argv[0], "bash")
            self.assertTrue(argv[1].endswith("cloud_engram_mcp.sh"))
            self.assertEqual(argv[2:], ["mcp", "--tools=agent"])
            self.assertNotIn("git clone", proc.stderr)

    def test_finds_forced_root_and_launches_tailscale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            _seed_plugin(plugin)
            hook = Path(tmp) / "exec.txt"
            env = _env_with_home(Path(tmp) / "home")
            env["CURSOR_LAPTOP_SKILLS_ROOT"] = str(plugin)
            env["CLOUD_HQ_MCP_EXEC"] = str(hook)
            proc = subprocess.run(
                ["python3", str(SCRIPTS / "cloud_hq_mcp.py"), "tailscale"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            argv = hook.read_text().splitlines()
            self.assertEqual(argv[0], "python3")
            self.assertTrue(argv[1].endswith("cloud_tailscale_mcp.py"))

    def test_clone_uses_extraheader_not_token_on_argv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            dest = home / ".local" / "share" / "cursor-laptop-skills"
            hook = Path(tmp) / "exec.txt"
            env = _env_with_home(home)
            env["SPORT_REPO_TOKEN"] = "super-secret-pat"
            env["CLOUD_HQ_MCP_EXEC"] = str(hook)
            seen = {}

            def fake_call(cmd, **kwargs):
                seen["cmd"] = list(cmd)
                seen["env"] = kwargs.get("env") or {}
                _seed_plugin(dest)
                return 0

            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "cloud_hq_mcp", SCRIPTS / "cloud_hq_mcp.py"
            )
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            with mock.patch.object(mod.subprocess, "check_call", side_effect=fake_call):
                with mock.patch.object(mod.subprocess, "call", return_value=0):
                    with mock.patch.object(mod, "_home", return_value=home):
                        root = mod.clone_root()
            self.assertEqual(root, dest)
            self.assertEqual(seen["cmd"][:3], ["git", "clone", "--depth"])
            joined = " ".join(seen["cmd"])
            self.assertNotIn("super-secret-pat", joined)
            self.assertNotIn("x-access-token:", joined)
            self.assertIn("GIT_CONFIG_VALUE_0", seen["env"])
            self.assertIn("basic ", seen["env"]["GIT_CONFIG_VALUE_0"])

    def test_print_mcp_has_python_c_and_no_tokens(self) -> None:
        proc = subprocess.run(
            ["python3", str(SCRIPTS / "cloud_hq_mcp.py"), "--print-mcp"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        engram = data["mcpServers"]["engram"]
        self.assertEqual(engram["command"], "python3")
        self.assertEqual(engram["args"][0], "-c")
        self.assertEqual(engram["args"][2], "engram")
        self.assertIn("cloud_engram_mcp.sh", engram["args"][1])
        self.assertEqual(engram["env"]["ENGRAM_CLOUD_AUTOSYNC"], "1")
        ts = data["mcpServers"]["tailscale-imac"]
        self.assertEqual(ts["args"][2], "tailscale")
        blob = json.dumps(data)
        self.assertEqual(list(engram["env"].keys()), ["ENGRAM_CLOUD_AUTOSYNC"])
        self.assertNotIn("tskey-", blob)
        self.assertNotIn("ENGRAM_CLOUD_TOKEN", blob)
        self.assertNotIn("should-drop", blob)

    def test_python_c_payload_runs(self) -> None:
        src = subprocess.run(
            ["python3", str(SCRIPTS / "cloud_hq_mcp.py"), "--print-mcp"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(src.stdout)
        payload = data["mcpServers"]["engram"]["args"][1]
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            _seed_plugin(plugin)
            hook = Path(tmp) / "exec.txt"
            env = _env_with_home(Path(tmp) / "home")
            env["CURSOR_LAPTOP_SKILLS_ROOT"] = str(plugin)
            env["CLOUD_HQ_MCP_EXEC"] = str(hook)
            proc = subprocess.run(
                ["python3", "-c", payload, "engram"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(hook.read_text().splitlines()[1].endswith("cloud_engram_mcp.sh"))

    def test_shell_wrapper_execs_python(self) -> None:
        mode = stat.S_IMODE((SCRIPTS / "cloud_hq_mcp.sh").stat().st_mode)
        self.assertTrue(mode & stat.S_IXUSR)
        text = (SCRIPTS / "cloud_hq_mcp.sh").read_text()
        self.assertIn("cloud_hq_mcp.py", text)

    def test_docs_name_the_dashboard_not_repo_mcp(self) -> None:
        docs = (ROOT / "docs" / "CLOUD_ACCOUNT_MCP.md").read_text()
        self.assertIn("cursor.com/dashboard/integrations", docs)
        self.assertIn("cursor.com/agents", docs)
        self.assertIn("Disable the marketplace Engram plugin on Cloud Agents", docs)
        self.assertIn("Do not point Engram at `engram-memory.com`", docs)

    def test_lib_engram_fallback_without_plugin_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            lib = home / ".local" / "lib" / "engram"
            lib.mkdir(parents=True)
            (lib / "cloud_engram_mcp.sh").write_text("#!/bin/sh\necho WRAPPER\n")
            (lib / "cloud_engram_mcp.sh").chmod(0o755)
            hook = Path(tmp) / "exec.txt"
            env = _env_with_home(home)
            env["CLOUD_HQ_MCP_EXEC"] = str(hook)
            proc = subprocess.run(
                ["python3", str(SCRIPTS / "cloud_hq_mcp.py"), "engram"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            argv = hook.read_text().splitlines()
            self.assertEqual(argv[1], str(lib / "cloud_engram_mcp.sh"))


if __name__ == "__main__":
    unittest.main()
