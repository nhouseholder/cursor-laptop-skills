---
name: engram-save
description: "ALWAYS ACTIVE on Cloud Agents. Save decisions, conventions, and finished work to the existing Engram MCP (mem_save / mem_session_summary) so other agents can mem_search them. Do not wait for /wrap-up. If the Engram namespace is error, say so."
---

# Engram save (Cloud Agents)

Use the **Engram** Cursor plugin already on the agent. Do not add another memory MCP.

Tools: `mem_save`, `mem_search`, `mem_context`, `mem_session_summary` (namespace `Engram`).

## When MCP is down

If GetDynamicTools reports Engram `namespaceStatus: error`, the usual cause on Cloud VMs is a missing `engram` binary (`command: engram mcp --tools=agent`). Say Engram is unavailable. Do not fake a save. Diamondpredictions install: `scripts/cloud_install_engram.sh`.

## When to save (do not wait to be asked)

- Decision, convention, preference, architecture
- Bugfix with root cause
- Finished slice other agents will continue
- `/wrap-up` — also `mem_session_summary`

`mem_save`: title, type, scope `project`, stable `topic_key`, content with What / Why / Where / Learned.

Other agents only see the write when Engram Cloud autosync is on (`ENGRAM_CLOUD_AUTOSYNC=1`, `ENGRAM_CLOUD_TOKEN`, `ENGRAM_CLOUD_SERVER`). A local SQLite on this VM is not the iMac store.
