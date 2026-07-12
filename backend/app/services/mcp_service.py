"""MCP (Model Context Protocol) integration.

Connects to MCP servers over stdio (spawned via `npx`) and exposes a small, uniform
surface: list servers, list a server's tools, and call a tool. The registry is built
from configuration, and adding a new server is just another `McpServerDef` — the rest of
the app (and the planner's filesystem tool) does not change.

Connections are opened per operation. That is simple and robust for a local single-user
app; MCP server packages are cached by npx after first use.
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import settings

# Pinned so the server matches the mcp client's protocol level (newer servers require
# the "roots" capability this client version doesn't advertise).
_FILESYSTEM_PKG = "@modelcontextprotocol/server-filesystem@0.6.2"


@dataclass
class McpServerDef:
    name: str
    label: str
    enabled: bool
    params: StdioServerParameters
    requires: str | None = None  # human note when a credential is missing
    roots: list[str] | None = None  # directories exposed to the server


def _registry() -> dict[str, McpServerDef]:
    root = os.path.abspath(settings.mcp_filesystem_root)
    os.makedirs(root, exist_ok=True)

    servers: dict[str, McpServerDef] = {
        "filesystem": McpServerDef(
            name="filesystem",
            label="Filesystem",
            enabled=settings.mcp_filesystem_enabled,
            roots=[root],
            params=StdioServerParameters(
                command="npx",
                args=["-y", _FILESYSTEM_PKG, root],
            ),
        ),
    }

    notion_headers = json.dumps(
        {
            "Authorization": f"Bearer {settings.notion_api_key}",
            "Notion-Version": "2022-06-28",
        }
    )
    servers["notion"] = McpServerDef(
        name="notion",
        label="Notion",
        enabled=settings.mcp_notion_enabled and bool(settings.notion_api_key),
        requires=None if settings.notion_api_key else "Notion integration token",
        params=StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={**os.environ, "OPENAPI_MCP_HEADERS": notion_headers},
        ),
    )
    return servers


def available_servers() -> list[McpServerDef]:
    return list(_registry().values())


def _get(name: str) -> McpServerDef:
    server = _registry().get(name)
    if server is None:
        raise ValueError(f"Unknown MCP server: {name}")
    return server


@asynccontextmanager
async def _session(server: McpServerDef):
    async with stdio_client(server.params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def _list_tools_impl(server: McpServerDef) -> list[str]:
    async with _session(server) as session:
        result = await session.list_tools()
        return [t.name for t in result.tools]


async def _call_tool_impl(server: McpServerDef, tool: str, arguments: dict) -> str:
    async with _session(server) as session:
        result = await session.call_tool(tool, arguments)
        return "\n".join(
            getattr(c, "text", "") for c in result.content if getattr(c, "text", "")
        )


# MCP servers are spawned as stdio subprocesses. Managing that subprocess lifecycle on
# the server's main event loop deadlocks under uvicorn, so each operation runs in its own
# event loop on a worker thread, fully isolated from the request loop.
async def list_tools(name: str) -> list[str]:
    server = _get(name)
    return await asyncio.to_thread(lambda: asyncio.run(_list_tools_impl(server)))


async def call_tool(name: str, tool: str, arguments: dict) -> str:
    server = _get(name)
    return await asyncio.to_thread(
        lambda: asyncio.run(_call_tool_impl(server, tool, arguments))
    )


async def server_status() -> list[dict]:
    """Report each server's enabled/connected state and tools (connects to verify)."""
    out: list[dict] = []
    for server in available_servers():
        entry = {
            "name": server.name,
            "label": server.label,
            "enabled": server.enabled,
            "requires": server.requires,
            "connected": False,
            "tools": [],
            "error": None,
        }
        if server.enabled:
            try:
                entry["tools"] = await list_tools(server.name)
                entry["connected"] = True
            except Exception as exc:  # pragma: no cover - environment dependent
                entry["error"] = str(exc)[:200]
        out.append(entry)
    return out
