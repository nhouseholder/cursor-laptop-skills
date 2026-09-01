---
name: engram-save
description: "ALWAYS ACTIVE on Cloud Agents. Save decisions, conventions, and finished work to the existing Engram MCP (mem_save / mem_session_summary) so other agents can mem_search them. Do not wait for /wrap-up. If the Engram namespace is error, say so."
---

# Engram save (Cloud Agents)

Use the **Engram** Cursor plugin already on the agent. Do not add another memory MCP.

Tools: `mem_save`, `mem_search`, `mem_context`, `mem_session_summary` (namespace `Engram`).

## When MCP is down

If GetDynamicTools reports Engram `namespaceStatus: error`, Cloud launched marketplace `command: engram` (exit 127) or Team/personal MCP was never saved. The account launcher is `scripts/cloud_hq_mcp.py` (self-install + hydrate). This running agent cannot rediscover a failed stdio MCP — a new agent is required after https://cursor.com/agents MCP (and Team Integrations) has `engram` from `python3 scripts/cloud_hq_mcp.py --print-mcp`, with marketplace Engram **disabled** on Cloud. Do not fake a save. Do not point at `engram-memory.com`.

## When to save (do not wait to be asked)

- Decision, convention, preference, architecture
- Bugfix with root cause
- Finished slice other agents will continue
- `/wrap-up` — also `mem_session_summary`

`mem_save`: title, type, scope `project`, stable `topic_key`, content with What / Why / Where / Learned.

Other agents only see the write when Engram Cloud autosync is on. The account plugin wrapper sets `ENGRAM_CLOUD_AUTOSYNC=1` and loads token/server from `~/.engram/cloud.json` after `scripts/cloud_engram_hydrate.sh`. A local SQLite on this VM is not the iMac store.
