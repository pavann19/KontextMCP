"""LangGraph node execution functions (P6.7 & P6.8 & P6.9)."""

import re
import time
import threading
from typing import Dict, Any
from app.agent.state import AgentState
from app.agent.llm import GroundedLegalSynthesizer, local_llm
from app.config import settings
from app.core.pii_guard import pii_guard
from app.core.prompt_guard import prompt_guard
from app.core.audit import AuditLogger
from app.core.tracing import telemetry
from app.core.grounding import citation, verify_excerpts, requested_references
from app.mcp.server import mcp_server
from app.mcp.permissions import PermissionManager
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import LegalCrossReranker

# Shared retrieval components
_cached_chunks = None
_hybrid_retriever = None
_reranker = None
_retrieval_lock = threading.RLock()

def get_retrieval_engine():
    global _cached_chunks, _hybrid_retriever, _reranker
    with _retrieval_lock:
        if _hybrid_retriever is None:
            chunks = IngestionPipeline().load_cached_chunks()
            retriever = HybridRetriever()
            retriever.index(chunks)
            _cached_chunks = chunks
            _reranker = LegalCrossReranker(top_n=3)
            _hybrid_retriever = retriever
    return _hybrid_retriever, _reranker

def guardrails_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Evaluates prompt injection, adversarial attacks, and PII presence."""
    start_t = time.time()
    span = telemetry.start_span(state.trace_id, "guardrails_inspection", "guardrail")

    query = state.original_query

    # 1. Inspect for Prompt Injections / Jailbreaks
    guard_res = prompt_guard.inspect(query)
    if not guard_res.is_safe:
        telemetry.end_span(span, outputs={"is_safe": False, "category": guard_res.risk_category})
        AuditLogger.log_event(
            user_id=state.user_context.username,
            user_role=state.user_context.role,
            action="GUARDRAIL_INTERCEPT",
            status="BLOCKED_SECURITY",
            details=f"Adversarial input blocked: {guard_res.details}",
            trace_id=state.trace_id
        )
        return {
            "is_safe": False,
            "security_flag": guard_res.risk_category,
            "intent": "blocked_security",
            "final_answer": (
                "ðŸš¨ **SECURITY POLICY VIOLATION**\n"
                "Your request contains an adversarial prompt injection or unauthorized instruction override pattern. "
                "The operation has been blocked and logged to the enterprise security audit registry."
            )
        }

    # 2. PII Detection and Masking/Pseudonymization
    pii_rep = pii_guard.pseudonymize(query, session_id=state.trace_id)

    telemetry.end_span(
        span,
        outputs={"has_pii": pii_rep.has_pii, "detected_count": pii_rep.detected_count}
    )

    return {
        "is_safe": True,
        "has_pii": pii_rep.has_pii,
        "pii_entity_count": pii_rep.detected_count,
        "sanitized_query": pii_rep.clean_text
    }

def intent_router_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Routes query to Knowledge RAG, MCP Tool execution, Hybrid, or Direct Chat."""
    if not state.is_safe:
        return {"intent": "blocked_security"}

    q = state.sanitized_query.lower()

    # Detect language using whole-word boundary matching to avoid substrings like 'der' in 'under'
    is_de = bool(re.search(r"\b(?:welche|artikel|hochrisiko|verordnung|anbieter|geldbuÃŸe|geldbusse|nicht|pflichten)\b", q))
    lang = state.target_language or ("de" if is_de else "en")

    # Database Tool indicators
    sys_id_match = re.search(r"\b(SYS-[A-Z0-9]+-\d+)\b", state.original_query, re.IGNORECASE)
    tool_keywords = [
        "high-risk systems", "hochrisiko-systeme", "incident", "vorfall",
        "submit audit", "compliance audit", "audit signoff", "audit protokoll",
        "registered system", "registrierte systeme", "system compliance"
    ]
    is_tool = bool(sys_id_match) or any(k in q for k in tool_keywords)

    # Legal Knowledge indicators
    knowledge_keywords = [
        "article", "artikel", "art.", "act", "verordnung", "prohibited", "verboten",
        "transparency", "transparenz", "fine", "fines", "geldbuÃŸe", "geldbuÃŸen", "penalty",
        "recital", "erwÃ¤gungsgrund", "annex", "anhang", "gpai", "systemic risk", "systemisches risiko"
    ]
    is_knowledge = any(k in q for k in knowledge_keywords)

    if is_tool and is_knowledge:
        intent = "hybrid"
    elif is_tool:
        intent = "mcp_tool"
    elif is_knowledge:
        intent = "knowledge_rag"
    else:
        intent = "knowledge_rag"  # Default knowledge search for enterprise knowledge platform

    # Prepare tool calls if intent involves tools
    tool_calls = []
    if is_tool:
        if "audit" in q and ("submit" in q or "einreichen" in q):
            allowed, reason = PermissionManager.check_tool_access("submit_compliance_audit_record", state.user_context)
            if not allowed:
                return {"intent": "direct_chat", "target_language": lang, "tool_calls": [],
                        "final_answer": f"PERMISSION DENIED: {reason}"}
            return {
                "intent": "direct_chat", "target_language": lang, "tool_calls": [],
                "final_answer": (
                    "Compliance sign-offs require explicit system_id, findings, compliance_status "
                    "and risk_score submitted through the authorized /api/v1/tools/call endpoint. "
                    "Chat does not create compliance records."
                )
            }
        elif sys_id_match:
            sys_id = sys_id_match.group(1).upper()
            if "incident" in q or "vorfall" in q:
                tool_calls.append({"name": "get_system_incident_history", "arguments": {"system_id": sys_id}})
            else:
                tool_calls.append({"name": "query_ai_system_compliance", "arguments": {"system_id": sys_id}})
        else:
            tool_calls.append({"name": "list_high_risk_systems", "arguments": {"risk_level": "high_risk"}})

    return {
        "intent": intent,
        "target_language": lang,
        "tool_calls": tool_calls
    }

def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Executes hybrid BM25 + Dense retrieval + Reranking."""
    span = telemetry.start_span(state.trace_id, "hybrid_retrieval", "retrieval")
    hybrid, reranker = get_retrieval_engine()

    q = state.sanitized_query
    lang = state.target_language

    candidates = hybrid.search(q, top_k=6, language=lang)
    # A named provision is a metadata lookup, not a lexical popularity contest.
    # Full publication text often mentions other articles more than its own ID.
    requested = requested_references(q)
    if requested:
        exact = [c for c in (_cached_chunks or [])
                 if (not lang or c.language == lang)
                 and requested.intersection(requested_references(c.article_id))]
        covered = set().union(*(requested_references(c.article_id) for c in exact))
        if requested.issubset(covered):
            candidates = [(c, 1.0) for c in exact]
    reranked = reranker.rerank(q, candidates, top_n=3, target_language=lang)

    chunks_data = []
    citations = []
    for chunk, score in reranked:
        chunks_data.append({
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "article_id": chunk.article_id,
            "title": chunk.title,
            "language": chunk.language,
            "text": chunk.text,
            "context_header": chunk.context_header,
            "score": round(score, 4)
        })
        citations.append({
            "article_id": chunk.article_id,
            "title": chunk.title,
            "language": chunk.language
        })

    # Sanitize retrieved chunks against Indirect Prompt Injection
    clean_chunks, quarantined = prompt_guard.sanitize_retrieved_chunks(chunks_data)
    clean_chunks = [c for c in clean_chunks if not c.get("has_indirect_injection")]
    citations = [{"article_id": c["article_id"], "title": c["title"], "language": c["language"]}
                 for c in clean_chunks]
    if quarantined:
        AuditLogger.log_event(
            user_id=state.user_context.username,
            user_role=state.user_context.role,
            action="INDIRECT_PROMPT_INJECTION_NEUTRALIZED",
            status="INTERCEPTED",
            details=f"Neutralized {len(quarantined)} indirect injection payloads in retrieved chunks: {quarantined[0].get('injection_details')}",
            trace_id=state.trace_id
        )

    telemetry.end_span(
        span,
        outputs={"retrieved_count": len(clean_chunks), "quarantined_count": len(quarantined)},
        metadata_update={"top_score": clean_chunks[0]["score"] if clean_chunks else 0.0}
    )

    return {
        "retrieved_chunks": clean_chunks,
        "citations": citations
    }

def tool_execution_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Executes authorized MCP tools through the Permission Gateway."""
    span = telemetry.start_span(state.trace_id, "mcp_tool_execution", "tool")
    results = []
    errors = []

    for call in state.tool_calls:
        t_name = call.get("name", "")
        t_args = call.get("arguments", {})

        res = mcp_server.call_tool(t_name, t_args, user=state.user_context)
        out_text = res.content[0].text if res.content else ""
        results.append({
            "tool": t_name,
            "result": out_text,
            "isError": res.isError
        })
        if res.isError:
            errors.append(out_text)

    telemetry.end_span(span, outputs={"results_count": len(results), "errors_count": len(errors)})

    return {
        "tool_results": results,
        "tool_errors": errors
    }

def synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Node 5: Synthesizes final response using local LLM or grounded synthesizer."""
    span = telemetry.start_span(state.trace_id, "response_synthesis", "generation")

    # If already blocked by security, return directly
    if not state.is_safe:
        return {"final_answer": state.final_answer, "citations": state.citations,
            "grounding_status": state.grounding_status, "grounding_error": state.grounding_error}

    # Use extractive synthesis until model output grounding is independently validated.
    if state.final_answer:
        return {"final_answer": state.final_answer, "citations": state.citations,
            "grounding_status": state.grounding_status, "grounding_error": state.grounding_error}
    selected = state.retrieved_chunks
    backend = "extractive"
    if settings.SYNTHESIS_MODE == "ollama_select" and not state.tool_results:
        proposed = local_llm.select_chunks(state.sanitized_query, selected)
        if proposed:
            selected, backend = proposed, "ollama_selection"
    answer = GroundedLegalSynthesizer.synthesize(
        query=state.sanitized_query,
        retrieved_chunks=selected,
        tool_results=state.tool_results,
        language=state.target_language or "en"
    )

    telemetry.end_span(span, outputs={"answer_length": len(answer)})

    is_excerpt = "[[source:" in answer and not state.tool_results
    return {"final_answer": answer, "answer_mode": "extractive" if is_excerpt else "notice",
            "citations": [citation(c) for c in selected[:3]] if is_excerpt else [], "synthesis_backend": backend}

def output_guard_node(state: AgentState) -> Dict[str, Any]:
    """Node 6: Final output safety validation, trace finalization, and audit recording."""
    state.final_answer = AuditLogger.mask_sensitive_payload(pii_guard.mask(state.final_answer).clean_text)
    for result in state.tool_results:
        result["result"] = AuditLogger.mask_sensitive_payload(pii_guard.mask(result.get("result", "")).clean_text)
    if state.answer_mode == "extractive":
        trusted = {c.chunk_id: c.model_dump() for c in (_cached_chunks or [])}
        valid, error = verify_excerpts(
            state.final_answer, state.citations, trusted, state.target_language or "en",
            sanitize=lambda text: AuditLogger.mask_sensitive_payload(pii_guard.mask(text).clean_text)
        )
        state.grounding_status = "SOURCE_VERIFIED" if valid else "REJECTED"
        state.grounding_error = error
        if not valid:
            state.final_answer = "The response could not be verified against local sources. No legal excerpts were returned."
            state.citations = []
    else:
        state.citations = []
        state.grounding_status = "NOT_APPLICABLE"
    # Write audit log record
    AuditLogger.log_event(
        user_id=state.user_context.username,
        user_role=state.user_context.role,
        action=f"AGENT_QUERY:{state.intent.upper()}",
        status="EXECUTED" if state.is_safe else "BLOCKED_SECURITY",
        details=(
            f"Intent: {state.intent} | PII: {state.has_pii} ({state.pii_entity_count}) | "
            f"Chunks: {len(state.retrieved_chunks)} | Tools: {len(state.tool_calls)} | Grounding: {state.grounding_status}"
        ),
        trace_id=state.trace_id
    )

    # End telemetry trace
    telemetry.end_trace(state.trace_id)

    return {"final_answer": state.final_answer, "citations": state.citations,
            "grounding_status": state.grounding_status, "grounding_error": state.grounding_error}
