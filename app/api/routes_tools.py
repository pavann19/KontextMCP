"""Model Context Protocol (MCP) tool execution endpoints (P6.5 & P6.6)."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.core.security import resolve_user_context
from app.mcp.permissions import UserContext
from app.mcp.server import mcp_server
from app.mcp.protocol import ToolDefinition, CallToolResult

router = APIRouter(prefix="/tools", tags=["MCP Tools"])

class CallToolRequest(BaseModel):
    name: str = Field(..., description="Tool name according to MCP specification.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool invocation parameters.")

@router.get("/list", response_model=List[ToolDefinition])
def list_authorized_tools(
    user: UserContext = Depends(resolve_user_context)
):
    """Lists MCP tools available to the requesting user based on role and clearance level."""
    return mcp_server.list_tools(user=user)

@router.post("/call", response_model=CallToolResult)
def execute_tool(
    request: CallToolRequest,
    user: UserContext = Depends(resolve_user_context)
):
    """Executes an MCP tool with strict authorization enforcement and audit logging."""
    result = mcp_server.call_tool(
        name=request.name,
        arguments=request.arguments,
        user=user
    )
    return result

