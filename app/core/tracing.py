"""Langfuse and local execution trace telemetry integration (P6.10).

Provides structured tracing for LLM generations, retrieval steps, guardrails,
and MCP tool calls with local file-backed trace replay.
"""

import time
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.config import settings
from app.core.pii_guard import pii_guard

class TraceSpan(BaseModel):
    span_id: str
    trace_id: str
    name: str
    span_type: str  # generation, retrieval, tool, guardrail
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExecutionTrace(BaseModel):
    trace_id: str
    user_id: str
    session_id: str
    query: str
    timestamp: str
    total_duration_ms: Optional[float] = None
    spans: List[TraceSpan] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)

class TelemetryManager:
    """Manages Langfuse telemetry connections with reliable local file trace recorder."""

    def __init__(self, trace_storage_dir: Path = settings.DATA_DIR):
        self.trace_file = trace_storage_dir / "execution_traces.jsonl"
        self.active_traces: Dict[str, ExecutionTrace] = {}

    def start_trace(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ExecutionTrace:
        """Initializes a new execution trace."""
        t_id = f"trc-{uuid.uuid4().hex[:12]}"
        s_id = "sess-" + hashlib.sha256(f"{user_id}:{session_id}".encode()).hexdigest()[:24] if session_id else f"sess-{uuid.uuid4().hex[:8]}"
        trace = ExecutionTrace(
            trace_id=t_id,
            user_id=user_id,
            session_id=s_id,
            query="[QUERY OMITTED]",
            timestamp=datetime.now(timezone.utc).isoformat(),
            tags=tags or ["enterprise-rag", "eu-ai-act"]
        )
        self.active_traces[t_id] = trace
        return trace

    def start_span(
        self,
        trace_id: str,
        name: str,
        span_type: str,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        """Starts a new span within an active trace."""
        span_id = f"spn-{uuid.uuid4().hex[:8]}"
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            span_type=span_type,
            start_time=time.time(),
            inputs=inputs or {},
            metadata=metadata or {}
        )
        if trace_id in self.active_traces:
            self.active_traces[trace_id].spans.append(span)
        return span

    def end_span(
        self,
        span: TraceSpan,
        outputs: Optional[Dict[str, Any]] = None,
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> None:
        """Ends a span, calculates latency, and records outputs."""
        span.end_time = time.time()
        span.duration_ms = round((span.end_time - span.start_time) * 1000, 2)
        if outputs:
            span.outputs = outputs
        if metadata_update:
            span.metadata.update(metadata_update)

    def end_trace(
        self,
        trace_id: str,
        scores: Optional[Dict[str, float]] = None
    ) -> Optional[ExecutionTrace]:
        """Finalizes an execution trace and persists it to disk and Langfuse if enabled."""
        trace = self.active_traces.pop(trace_id, None)
        if not trace:
            return None

        # Calculate total duration
        if trace.spans:
            earliest = min(s.start_time for s in trace.spans)
            latest = max(s.end_time or s.start_time for s in trace.spans)
            trace.total_duration_ms = round((latest - earliest) * 1000, 2)

        if scores:
            trace.scores.update(scores)

        # 1. Local persistence
        try:
            self.trace_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace.model_dump(), ensure_ascii=False) + "\n")
        except Exception:
            pass

        # 2. Remote Langfuse emission if enabled
        if settings.LANGFUSE_ENABLED:
            self._send_to_langfuse(trace)

        return trace

    def _send_to_langfuse(self, trace: ExecutionTrace) -> None:
        """Sends trace data to remote Langfuse endpoint asynchronously."""
        try:
            import httpx
            # Minimal payload adhering to Langfuse ingestion API
            payload = {
                "batch": [
                    {
                        "id": trace.trace_id,
                        "type": "trace-create",
                        "timestamp": trace.timestamp,
                        "body": {
                            "id": trace.trace_id,
                            "name": "enterprise-agent-query",
                            "userId": trace.user_id,
                            "sessionId": trace.session_id,
                            "input": trace.query,
                            "metadata": {"scores": trace.scores, "duration_ms": trace.total_duration_ms}
                        }
                    }
                ]
            }
            # Attempt non-blocking flush
            with httpx.Client(timeout=2.0) as client:
                response = client.post(
                    f"{settings.LANGFUSE_HOST}/api/public/ingestion",
                    json=payload,
                    auth=(settings.LANGFUSE_PUBLIC_KEY, settings.LANGFUSE_SECRET_KEY)
                )
                response.raise_for_status()
                return not response.json().get("errors", [])
        except Exception:
            # Local trace remains; report remote failure to the caller.
            return False

    def get_recent_traces(self, limit: int = 20, user_id: Optional[str] = None) -> List[ExecutionTrace]:
        """Retrieves recent execution traces."""
        if not self.trace_file.exists():
            return []
        traces = []
        with open(self.trace_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    trace = ExecutionTrace(**json.loads(line.strip()))
                    if user_id is None or trace.user_id == user_id:
                        # Historical files may contain raw queries. Never return them.
                        trace.query = "[QUERY OMITTED]"
                        traces.append(trace)
        return list(reversed(traces))[:limit]

# Global singleton instance
telemetry = TelemetryManager()

