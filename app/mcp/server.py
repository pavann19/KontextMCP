"""Model Context Protocol (MCP) Server and Execution Registry (P6.5 & P6.6)."""

import time
from jsonschema import Draft202012Validator
import json
from typing import Dict, List, Any, Optional, Tuple
from app.mcp.protocol import (
    ToolDefinition, ToolInputSchema, CallToolResult,
    JSONRPCRequest, JSONRPCResponse, JSONRPCError,
    InitializeResult, ServerCapabilities, ServerInfo
)
from app.mcp.permissions import UserContext, PermissionManager, TOOL_PERMISSIONS
from app.mcp.tools import MCPToolImplementations

class MCPServer:
    """Enterprise MCP Server coordinating tool schemas, authorization, and dispatch."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Registers all supported EU AI Act platform tools."""
        self.register_tool(
            ToolDefinition(
                name="search_eu_ai_act_provisions",
                description="Searches bilingual German/English EU AI Act regulatory provisions, articles, and annexes.",
                inputSchema=ToolInputSchema(
                    properties={
                        "query": {"type": "string", "description": "The search query in German or English."},
                        "language": {"type": "string", "enum": ["en", "de"], "description": "Optional language filter."},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 20, "default": 3, "description": "Number of provisions to retrieve."}
                    },
                    required=["query"]
                ),
                required_clearance=1,
                allowed_roles=["public_viewer", "developer", "auditor", "compliance_officer", "admin"]
            )
        )

        self.register_tool(
            ToolDefinition(
                name="query_ai_system_compliance",
                description="Queries an enterprise AI system's registration, risk classification, and conformity status.",
                inputSchema=ToolInputSchema(
                    properties={
                        "system_id": {"type": "string", "description": "The unique system ID (e.g., 'SYS-HR-001') or system name."}
                    },
                    required=["system_id"]
                ),
                required_clearance=1,
                allowed_roles=["public_viewer", "developer", "auditor", "compliance_officer", "admin"]
            )
        )

        self.register_tool(
            ToolDefinition(
                name="list_high_risk_systems",
                description="Lists registered AI systems classified as high-risk under Article 6 and Annex III.",
                inputSchema=ToolInputSchema(
                    properties={
                        "risk_level": {"type": "string", "default": "high_risk", "description": "Filter by risk tier (high_risk, prohibited, specific_transparency_risk, minimal_risk)."},
                        "department": {"type": "string", "description": "Optional department filter (e.g., human_resources)."}
                    }
                ),
                required_clearance=2,
                allowed_roles=["developer", "auditor", "compliance_officer", "admin"]
            )
        )

        self.register_tool(
            ToolDefinition(
                name="get_system_incident_history",
                description="Retrieves Article 73 serious incident reports, malfunctions, and fundamental rights breaches.",
                inputSchema=ToolInputSchema(
                    properties={
                        "system_id": {"type": "string", "description": "The AI system ID (e.g., 'SYS-BIO-002')."}
                    },
                    required=["system_id"]
                ),
                required_clearance=3,
                allowed_roles=["auditor", "compliance_officer", "admin"]
            )
        )

        self.register_tool(
            ToolDefinition(
                name="submit_compliance_audit_record",
                description="Submits an official compliance audit assessment and updates an AI system's conformity status.",
                inputSchema=ToolInputSchema(
                    properties={
                        "system_id": {"type": "string", "description": "Target AI system ID."},
                        "findings": {"type": "string", "description": "Summary of audit observations and compliance evidence."},
                        "compliance_status": {"type": "string", "enum": ["compliant", "conditional_pass", "non_compliant"], "description": "Conformity assessment conclusion."},
                        "risk_score": {"type": "number", "minimum": 0, "maximum": 10, "description": "Risk score metric from 0.0 to 10.0."},
                        "idempotency_key": {"type": "string", "minLength": 1, "maxLength": 128, "description": "Reuse for retries of identical fields; scoped to the authenticated caller."},
                        "remediation_plan": {"type": "string", "description": "Mandatory remediation actions if non-compliant or conditional."}
                    },
                    required=["system_id", "findings", "compliance_status", "risk_score"]
                ),
                required_clearance=4,
                allowed_roles=["compliance_officer", "admin"]
            )
        )

    def register_tool(self, tool_def: ToolDefinition) -> None:
        """Registers a tool definition."""
        self._tools[tool_def.name] = tool_def

    def list_tools(self, user: Optional[UserContext] = None) -> List[ToolDefinition]:
        """Lists available tools. If user is provided, filters to tools user is authorized to call."""
        user = user or UserContext.public_default()
        return [
            tool for tool in self._tools.values()
            if PermissionManager.check_tool_access(tool.name, user)[0]
        ]

    def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        user: Optional[UserContext] = None
    ) -> CallToolResult:
        """Executes a tool with strict pre-execution permission verification."""
        user_ctx = user or UserContext.public_default()
        start_time = time.time()

        # Check if tool exists
        if not isinstance(name, str) or name not in self._tools:
            return CallToolResult.error(f"Unknown MCP tool '{name}'.")

        if not isinstance(arguments, dict):
            return CallToolResult.error("Schema validation error: Arguments must be an object.")

        # 1. Enforce permission boundary
        allowed, denial_reason = PermissionManager.check_tool_access(name, user_ctx)
        if not allowed:
            # Security alert: Log unauthorized access attempt
            from app.core.audit import AuditLogger
            AuditLogger.log_event(
                user_id=user_ctx.username,
                user_role=user_ctx.role,
                action=f"CALL_TOOL:{name}",
                target_resource=str(arguments.get("system_id") or name),
                status="PERMISSION_DENIED",
                details=f"Access blocked by security policy: {denial_reason}"
            )
            return CallToolResult.error(
                denial_reason or "Permission denied.",
                metadata={"status": "PERMISSION_DENIED", "user": user_ctx.username, "role": user_ctx.role}
            )

        valid, error = self.validate_tool_arguments(name, arguments)
        if not valid:
            return CallToolResult.error(f"Schema validation error: {error}")

        # 2. Dispatch execution
        try:
            if name == "search_eu_ai_act_provisions":
                result = MCPToolImplementations.search_eu_ai_act_provisions(arguments, user_ctx)
            elif name == "query_ai_system_compliance":
                result = MCPToolImplementations.query_ai_system_compliance(arguments, user_ctx)
            elif name == "list_high_risk_systems":
                result = MCPToolImplementations.list_high_risk_systems(arguments, user_ctx)
            elif name == "get_system_incident_history":
                result = MCPToolImplementations.get_system_incident_history(arguments, user_ctx)
            elif name == "submit_compliance_audit_record":
                result = MCPToolImplementations.submit_compliance_audit_record(arguments, user_ctx)
            else:
                result = CallToolResult.error(f"Execution handler not implemented for tool '{name}'.")

            latency_ms = (time.time() - start_time) * 1000
            result.metadata.update({"latency_ms": round(latency_ms, 2), "tool": name, "user": user_ctx.username})

            if name == "submit_compliance_audit_record" and not result.isError:
                # The committed transaction already contains its audit intent.
                # A ledger outage must not turn a successful write into a retryable error.
                result.metadata["audit_delivery"] = "DURABLE_OUTBOX"
                return result

            # 3. Log audit event
            from app.core.audit import AuditLogger
            log_status = "ERROR" if result.isError else "EXECUTED"
            AuditLogger.log_event(
                user_id=user_ctx.username,
                user_role=user_ctx.role,
                action=f"CALL_TOOL:{name}",
                target_resource=str(arguments.get("system_id") or name),
                status=log_status,
                details=f"Execution completed in {round(latency_ms, 2)}ms. Result status: {log_status}"
            )
            return result

        except Exception as e:
            from app.core.audit import AuditLogger
            AuditLogger.log_event(
                user_id=user_ctx.username,
                user_role=user_ctx.role,
                action=f"CALL_TOOL:{name}",
                target_resource=str(arguments.get("system_id") or name),
                status="ERROR",
                details=f"Tool exception type: {type(e).__name__}"
            )
            return CallToolResult.error(f"Error executing tool '{name}'. The operation failed; consult the operator.")

    def validate_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates tool arguments against the declared ToolInputSchema."""
        tool = self._tools.get(tool_name) if isinstance(tool_name, str) else None
        if not tool:
            return False, f"Unknown tool '{tool_name}'."

        if not isinstance(arguments, dict):
            return False, "Arguments must be an object."
        schema = tool.inputSchema
        # 1. Check required properties
        for req in schema.required:
            if req not in arguments or arguments[req] is None or arguments[req] == "":
                return False, f"Missing required parameter '{req}'."

        errors = sorted(Draft202012Validator(schema.model_dump()).iter_errors(arguments), key=lambda e: str(e.path))
        if errors:
            return False, errors[0].message
        return True, None

    def handle_jsonrpc(
        self,
        request_data: Dict[str, Any],
        user: Optional[UserContext] = None
    ) -> Dict[str, Any]:
        """Standard JSON-RPC 2.0 dispatcher implementing the MCP 2024-11-05 protocol."""
        if not isinstance(request_data, dict):
            return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
        req_id = request_data.get("id")
        method = request_data.get("method")
        params = request_data.get("params") or {}

        if (request_data.get("jsonrpc") != "2.0" or not isinstance(method, str)
                or not method or isinstance(req_id, bool)
                or not isinstance(req_id, (str, int, type(None)))):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32600, "message": "Invalid Request: Must be valid JSON-RPC 2.0 with a 'method'."}
            }

        if not isinstance(params, dict):
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Params must be an object."}}

        # 1. Ping
        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # 2. Initialize
        if method == "initialize":
            init_res = InitializeResult()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": init_res.model_dump()
            }

        # 3. Tools / List
        if method == "tools/list":
            tools = self.list_tools(user)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [t.model_dump(exclude={"required_clearance", "allowed_roles"}) for t in tools]
                }
            }

        # 4. Tools / Call
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params: Missing required 'name' in tools/call."}
                }

            # Validate arguments against schema
            is_valid, validation_err = self.validate_tool_arguments(tool_name, tool_args)
            if not is_valid:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": f"Schema validation error: {validation_err}"}
                }

            result = self.call_tool(tool_name, tool_args, user=user)
            if result.isError and (result.metadata.get("status") == "PERMISSION_DENIED" or "SECURITY VIOLATION" in result.content[0].text or "PERMISSION DENIED" in result.content[0].text):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32001, "message": result.content[0].text, "data": result.metadata}
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [c.model_dump() for c in result.content],
                    "isError": result.isError,
                    "_meta": result.metadata
                }
            }

        # Unknown method
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: '{method}'."}
        }

# Singleton MCP server instance
mcp_server = MCPServer()

