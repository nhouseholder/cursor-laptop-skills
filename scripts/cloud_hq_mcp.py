#!/usr/bin/env python3
"""Account-wide Cloud HQ MCP launcher. stdout is MCP-only.

Finds cursor-laptop-skills (plugin cache or ~/.local/share), clones it with
SPORT_REPO_TOKEN extraheader if missing, then execs Engram or Tailscale MCP.
Never prints tokens. Never puts a token on argv.

  python3 cloud_hq_mcp.py engram
  python3 cloud_hq_mcp.py tailscale
  python3 cloud_hq_mcp.py --print-mcp
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/nhouseholder/cursor-laptop-skills.git"
SHARE_REL = ".local/share/cursor-laptop-skills"
MARKER = "scripts/cloud_engram_mcp.sh"
CLONE_LOG = "/tmp/cloud-hq-mcp-clone.log"


def _home() -> Path:
    return Path(os.environ.get("HOME") or Path.home())


def _ok(root: Path) -> bool:
    return (root / MARKER).is_file()


def _token() -> str:
    for name in ("SPORT_REPO_TOKEN", "GH_SPORT_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _git_env() -> dict:
    env = os.environ.copy()
    token = _token()
    if not token:
        return env
    basic = base64.b64encode(f"x-access-token:{token}".encode("ascii")).decode("ascii")
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {basic}"
    return env


def find_root() -> Path | None:
    home = _home()
    forced = os.environ.get("CURSOR_LAPTOP_SKILLS_ROOT", "").strip()
    if forced and _ok(Path(forced)):
        return Path(forced)
    share = home / SHARE_REL
    if _ok(share):
        return share
    cache = home / ".cursor" / "plugins" / "cache"
    if cache.is_dir():
        for match in sorted(cache.glob("*cursor-laptop-skills*")):
            if _ok(match):
                return match
            if not match.is_dir():
                continue
            for hit in sorted(match.rglob("cloud_engram_mcp.sh")):
                return hit.parent.parent
    return None


def _script(name: str) -> Path | None:
    root = find_root()
    candidates = []
    if root is not None:
        candidates.append(root / "scripts" / name)
        candidates.append(root / name)
    candidates.append(_home() / ".local" / "lib" / "engram" / name)
    for path in candidates:
        if path.is_file():
            return path
    return None


def clone_root() -> Path:
    dest = _home() / SHARE_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not _ok(dest):
        shutil.rmtree(dest)
    if _ok(dest):
        return dest
    with open(CLONE_LOG, "ab") as log:
        subprocess.check_call(
            ["git", "clone", "--depth", "1", REPO, str(dest)],
            env=_git_env(),
            stdout=log,
            stderr=log,
        )
    subprocess.call(
        ["git", "-C", str(dest), "remote", "set-url", "origin", REPO],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not _ok(dest):
        print("cloud_hq_mcp: clone missing Engram wrapper", file=sys.stderr)
        raise SystemExit(1)
    return dest


def _exec(argv: list[str]) -> None:
    hook = os.environ.get("CLOUD_HQ_MCP_EXEC", "").strip()
    if hook:
        Path(hook).write_text("\n".join(argv) + "\n")
        return
    os.execvp(argv[0], argv)


def launch(mode: str) -> int:
    name = "cloud_tailscale_mcp.py" if mode == "tailscale" else "cloud_engram_mcp.sh"
    path = _script(name)
    if path is None:
        root = clone_root()
        path = root / "scripts" / name
    if mode == "tailscale":
        _exec(["python3", str(path)])
        return 0
    os.environ["ENGRAM_CLOUD_AUTOSYNC"] = os.environ.get("ENGRAM_CLOUD_AUTOSYNC") or "1"
    _exec(["bash", str(path), "mcp", "--tools=agent"])
    return 0


def python_c_source() -> str:
    import inspect

    header = (
        "from __future__ import annotations\n"
        "import base64, os, shutil, subprocess, sys\n"
        "from pathlib import Path\n"
        f"REPO = {REPO!r}\n"
        f"SHARE_REL = {SHARE_REL!r}\n"
        f"MARKER = {MARKER!r}\n"
        f"CLONE_LOG = {CLONE_LOG!r}\n"
    )
    body = "\n".join(
        inspect.getsource(fn)
        for fn in (
            _home,
            _ok,
            _token,
            _git_env,
            find_root,
            _script,
            clone_root,
            _exec,
            launch,
        )
    )
    return (
        header
        + body
        + "\nraise SystemExit(launch(sys.argv[1] if len(sys.argv) > 1 else 'engram'))\n"
    )


def mcp_server(mode: str) -> dict:
    block: dict = {
        "command": "python3",
        "args": ["-c", python_c_source(), mode],
    }
    if mode == "engram":
        block["env"] = {"ENGRAM_CLOUD_AUTOSYNC": "1"}
    return block


JOBHUB_MCP_URL = "https://jobhub-cloud-mcp.nikhouseholdr.workers.dev/mcp"


def account_mcp_document() -> dict:
    """Every server a Cloud Agent needs, in dashboard paste form.

    jobhub is a plain HTTP server: the Cloudflare Worker injects the iMac token from KV,
    so the client config carries no secret and needs no Tailscale. engram and
    tailscale-imac are stdio launchers that self-heal on a fresh VM.
    """
    return {
        "mcpServers": {
            "jobhub": {"url": JOBHUB_MCP_URL},
            "engram": mcp_server("engram"),
            "tailscale-imac": mcp_server("tailscale"),
        }
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--print-mcp":
        sys.stdout.write(json.dumps(account_mcp_document(), indent=2) + "\n")
        return 0
    if args and args[0] == "--write-mcp":
        dest = Path(args[1] if len(args) > 1 else "-")
        text = json.dumps(account_mcp_document(), indent=2) + "\n"
        if str(dest) == "-":
            sys.stdout.write(text)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
        return 0
    mode = args[0] if args else "engram"
    if mode not in ("engram", "tailscale"):
        print(f"cloud_hq_mcp: unknown mode {mode!r}", file=sys.stderr)
        return 2
    return launch(mode)


if __name__ == "__main__":
    raise SystemExit(main())
