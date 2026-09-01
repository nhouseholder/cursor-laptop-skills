"""cloud_tailscale_up.sh must stay userspace-only and never leak the auth key."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cloud_tailscale_up.sh"


def test_script_is_userspace_and_has_no_global_proxy():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "--tun=userspace-networking" in text
    assert "--socks5-server" in text
    assert "--outbound-http-proxy-listen" in text
    assert "nicholass-imac" in text
    assert "nicholashouseholder" in text
    assert "TAILSCALE_AUTHKEY" in text
    assert "TS_API_KEY" in text
    assert "credentials/tailscale.env" in text
    assert "TAILSCALE_CREDS_FILE" in text
    assert "cloud_tailscale_hydrate.sh" in text
    assert "prompt-betting-engram/tailscale.env" in text
    assert "Add it as a Cursor" not in text
    assert "start a new agent" not in text
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert not stripped.startswith("export HTTP_PROXY=")
        assert not stripped.startswith("export HTTPS_PROXY=")
        assert not stripped.startswith("export ALL_PROXY=")
        assert "echo \"$TAILSCALE_AUTHKEY\"" not in stripped
        assert "echo ${TAILSCALE_AUTHKEY}" not in stripped


def test_dry_check_passes():
    env = os.environ.copy()
    env["TAILSCALE_SKIP_INSTALL"] = "1"
    proc = subprocess.run(
        ["bash", str(SCRIPT), "--dry-check"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert "dry-check ok" in proc.stderr
    assert "tskey-" not in proc.stdout + proc.stderr


def test_missing_key_skips_without_bricking(tmp_path: Path):
    env = os.environ.copy()
    env.pop("TAILSCALE_AUTHKEY", None)
    env.pop("TS_API_KEY", None)
    env.pop("TAILSCALE_API_KEY", None)
    env.pop("TS_OAUTH_CLIENT_SECRET", None)
    env["TAILSCALE_SKIP_INSTALL"] = "1"
    env["TAILSCALE_SKIP_R2_HYDRATE"] = "1"
    env["CLOUD_GITHUB_SKIP_PROBE"] = "1"
    env["TAILSCALE_STATE_DIR"] = str(tmp_path / "ts")
    env["TAILSCALE_CREDS_FILE"] = str(tmp_path / "no-such-creds.env")
    proc = subprocess.run(
        ["bash", str(SCRIPT), "up"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, combined
    assert "no Tailscale credential" in combined
    assert "Add it as a Cursor" not in combined
    assert "tskey-" not in combined


def test_creds_file_prevents_skip(tmp_path: Path):
    import shutil

    creds = tmp_path / "tailscale.env"
    creds.write_text("TAILSCALE_AUTHKEY=tskey-auth-unit-test-only\n", encoding="utf-8")
    env = os.environ.copy()
    env.pop("TS_API_KEY", None)
    env.pop("TAILSCALE_API_KEY", None)
    env.pop("TS_OAUTH_CLIENT_SECRET", None)
    env.pop("TAILSCALE_AUTHKEY", None)
    env["TAILSCALE_CREDS_FILE"] = str(creds)
    env["TAILSCALE_SKIP_INSTALL"] = "1"
    env["TAILSCALE_SKIP_R2_HYDRATE"] = "1"
    env["CLOUD_GITHUB_SKIP_PROBE"] = "1"
    env["TAILSCALE_STATE_DIR"] = str(tmp_path / "ts")
    if shutil.which("tailscale"):
        # CLI is present: `up` would call `tailscale up` with the fake key.
        proc = subprocess.run(
            ["bash", str(SCRIPT), "--dry-check"],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0, combined
        assert "tskey-" not in combined
        return
    proc = subprocess.run(
        ["bash", str(SCRIPT), "up"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    combined = proc.stdout + proc.stderr
    assert "no Tailscale credential" not in combined
    assert "tskey-auth-unit-test-only" not in combined
    assert "tskey-" not in combined
    assert "TAILSCALE_SKIP_INSTALL=1" in combined or proc.returncode == 0


def test_hydrate_writes_0600_and_hides_key(tmp_path: Path):
    dest = tmp_path / "creds" / "tailscale.env"
    client = tmp_path / "tailscale.env"
    secret = "tskey-api-unit-test-only-not-real"
    client.write_text(f"TS_API_KEY={secret}\n")
    bin_dir = tmp_path / "bin"
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
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["CLOUDFLARE_API_TOKEN"] = "cf-test"
    env["CLOUDFLARE_ACCOUNT_ID"] = "acct-test"
    env["TAILSCALE_CREDS_FILE"] = str(dest)
    env["TAILSCALE_FORCE_HYDRATE"] = "1"
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts" / "cloud_tailscale_hydrate.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, combined
    assert secret not in combined
    assert dest.is_file()
    written = dest.read_text()
    assert f"TS_API_KEY={secret}" in written
    mode = os.stat(dest).st_mode & 0o777
    assert mode == 0o600
    assert "hydrated" in combined
