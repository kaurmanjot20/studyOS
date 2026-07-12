"""MCP routes: list configured servers and their live tool inventory."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import McpServerStatus
from app.services import mcp_service

router = APIRouter(tags=["mcp"])


@router.get("/servers", response_model=list[McpServerStatus])
async def list_servers():
    return await mcp_service.server_status()


@router.get("/servers/{name}/tools")
async def server_tools(name: str):
    try:
        return {"tools": await mcp_service.list_tools(name)}
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown MCP server")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)[:200])
