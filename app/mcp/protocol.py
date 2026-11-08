"""Model Context Protocol (MCP) data models and schemas (P6.5 & P6.6).

Standard-compliant MCP 2024-11-05 & JSON-RPC 2.0 protocol specifications,
tool definition schemas, structured results, and JSON-RPC dispatch contracts.
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

class ToolInputSchema(BaseModel):
    type: str = "object"
    additionalProperties: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)

class ToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: ToolInputSchema
    required_clearance: int = 1
    allowed_roles: List[str] = Field(default_factory=list)

class TextContent(BaseModel):
    type: str = "text"
    text: str

class CallToolResult(BaseModel):
    content: List[TextContent] = Field(default_factory=list)
    isError: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success(cls, text: str, metadata: Optional[Dict[str, Any]] = None) -> "CallToolResult":
        return cls(content=[TextContent(type="text", text=text)], isError=False, metadata=metadata or {})

    @classmethod
    def error(cls, error_msg: str, metadata: Optional[Dict[str, Any]] = None) -> "CallToolResult":
        return cls(content=[TextContent(type="text", text=error_msg)], isError=True, metadata=metadata or {})

# --- JSON-RPC 2.0 / MCP Protocol Types ---

class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None

class ServerCapabilities(BaseModel):
    tools: Dict[str, Any] = Field(default_factory=lambda: {"listChanged": False})

class ServerInfo(BaseModel):
    name: str = "kontext-mcp"
    version: str = "1.0.0"

class InitializeResult(BaseModel):
    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    serverInfo: ServerInfo = Field(default_factory=ServerInfo)
