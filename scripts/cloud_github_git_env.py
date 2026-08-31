#!/usr/bin/env python3
"""Print eval-able exports that replace Cursor Cloud's stale git extraheader.

Cloud injects GIT_CONFIG_COUNT=1 with
`http.https://github.com/.extraheader=AUTHORIZATION: bearer <cloud token>`.
That bearer 401s git-upload-pack (git fetch/push/clone). SPORT_REPO_TOKEN is a
classic PAT with `repo` scope: GitHub REST already accepted it; git smart HTTP
accepts HTTP Basic `x-access-token:TOKEN`.

eval "$(python3 scripts/cloud_github_git_env.py)"

Never print the token. Missing token: stderr note, empty stdout, exit 0.
"""
from __future__ import annotations

import base64
import os
import shlex
import sys


def sport_token() -> str:
    for name in ("SPORT_REPO_TOKEN", "GH_SPORT_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def extraheader_value(token: str) -> str:
    basic = base64.b64encode(f"x-access-token:{token}".encode("ascii")).decode("ascii")
    return f"AUTHORIZATION: basic {basic}"


def export_block(token: str) -> str:
    quoted = shlex.quote(extraheader_value(token))
    return (
        "export GIT_CONFIG_COUNT=1\n"
        "export GIT_CONFIG_KEY_0=http.https://github.com/.extraheader\n"
        f"export GIT_CONFIG_VALUE_0={quoted}\n"
    )


def main() -> int:
    token = sport_token()
    if not token:
        print(
            "SPORT_REPO_TOKEN missing — git extraheader unchanged",
            file=sys.stderr,
        )
        return 0
    sys.stdout.write(export_block(token))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
