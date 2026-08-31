#!/usr/bin/env python3
"""Mint a one-shot Tailscale auth key from TS_API_KEY. Prints the key to stdout.

Cursor Cloud VMs are ephemeral. A reusable TAILSCALE_AUTHKEY works, but a Tailscale
API token can mint a fresh ephemeral preauthorized key per boot so the static key
is optional. Never log the minted key. Missing API token: exit 0, empty stdout.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

API = "https://api.tailscale.com/api/v2/tailnet/-/keys"
TIMEOUT_SEC = 30.0


def api_token() -> str:
    for name in ("TS_API_KEY", "TAILSCALE_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _payload(tags: Optional[list[str]] = None) -> Dict[str, Any]:
    create: Dict[str, Any] = {
        "reusable": False,
        "ephemeral": True,
        "preauthorized": True,
    }
    if tags:
        create["tags"] = tags
    return {
        "capabilities": {"devices": {"create": create}},
        "expirySeconds": 3600,
        "description": "cursor-cloud-ephemeral",
    }


def mint_auth_key(token: Optional[str] = None, tags: Optional[list[str]] = None) -> str:
    tok = token if token is not None else api_token()
    if not tok:
        return ""
    data = json.dumps(_payload(tags)).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=data,
        method="POST",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json",
            "User-Agent": "prompt-betting-cloud-tailscale",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        body = json.loads(resp.read().decode("utf-8") or "{}")
    key = str(body.get("key") or "").strip()
    if not key:
        raise RuntimeError("Tailscale API returned no auth key")
    return key


def main() -> int:
    tok = api_token()
    if not tok:
        return 0
    raw_tags = os.environ.get("TAILSCALE_TAGS", "").strip()
    tags = [t for t in raw_tags.split(",") if t.strip()] or None
    try:
        key = mint_auth_key(tok, tags)
    except urllib.error.HTTPError as ex:
        # Tagged keys fail when the tailnet has no matching ACL tag. Retry bare.
        if ex.code in (400, 403) and tags:
            try:
                key = mint_auth_key(tok, None)
            except Exception as inner:
                print(f"tailscale mint failed: {type(inner).__name__}", file=sys.stderr)
                return 0
        else:
            print(f"tailscale mint HTTP {ex.code}", file=sys.stderr)
            return 0
    except Exception as ex:
        print(f"tailscale mint failed: {type(ex).__name__}", file=sys.stderr)
        return 0
    sys.stdout.write(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
