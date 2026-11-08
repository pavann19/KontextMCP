> Historical design document. Claims and measurements below predate the current hardening pass and are not current verification evidence. Use [README](../README.md), [hardening scope](hardening.md), and the generated reports for current behavior.

# KontextMCP — Production Deployment & Hardening Guide

**Target Environment:** Local-First Enterprise Server / Docker Compose  
**Security Posture:** Production Hardened  
**Zero-Cloud Dependency:** 100% executable offline with local Ollama, PostgreSQL, and Qdrant.

---

## 1. Quick Start with Docker Compose

Deploy the complete platform stack with a single command:

```bash
docker compose -f docker/docker-compose.yml up -d
```

### Services Deployed:
| Service | Image | Internal Port | Host Port | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `kontext-app` | `kontextmcp/app:latest` | 8000 | `8000` | FastAPI Gateway & LangGraph Agent |
| `postgres` | `postgres:16-alpine` | 5432 | `5432` | Relational DB & Audit Ledger |
| `qdrant` | `qdrant/qdrant:v1.9.0` | 6333 | `6333` | Dense Vector Storage |
| `ollama` | `ollama/ollama:latest` | 11434 | `11434` | Local Offline LLM Inference |
| `langfuse` | `langfuse/langfuse:2` | 3000 | `3000` | Tracing & Observability UI |

---

## 2. Environment Configuration (`.env`)

Create `.env` based on `.env.example`:

```bash
cp .env.example .env
```

### Essential Configuration Keys:
```ini
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Databases
DATABASE_URL=postgresql://kontext_user:kontext_password@postgres:5432/kontext_enterprise_db
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION_NAME=eu_ai_act_bilingual

# Inference & Tracing
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral:7b
LANGFUSE_PUBLIC_KEY=pk-lf-local-demo
LANGFUSE_SECRET_KEY=sk-lf-local-demo
LANGFUSE_HOST=http://langfuse:3000

# Security & Audit
AUDIT_LOG_PATH=data/audit_log.jsonl
AUDIT_CHECKPOINT_KEY=enterprise-vault-key-replace-in-production
ALLOW_ROLE_HEADER_OVERRIDE=false
```

---

## 3. Production Hardening Checklist

- [x] **Disable Unauthenticated Role Headers:** Set `ENVIRONMENT=production` and `ALLOW_ROLE_HEADER_OVERRIDE=false`.
- [x] **Rotate API Keys:** Replace demo API keys in `app/core/security.py` with cryptographically generated random keys stored in enterprise secret manager.
- [x] **Secure Audit Checkpoint Key:** Set a strong secret key for `AUDIT_CHECKPOINT_KEY` to guarantee external HMAC signature integrity.
- [x] **Export Audit Ledger to WORM Storage:** Periodically sync `data/audit_log.jsonl` and `data/audit_checkpoints.json` to an append-only external bucket or immutable syslog server.
- [x] **Verify Database Migrations:** Run `init_db()` and seed enterprise schema using `scripts/seed_database.py`.
- [x] **Set Resource Limits:** Ensure Docker Compose sets memory and CPU bounds for `ollama` and `qdrant` to prevent host resource starvation.

---

## 4. Operational Health & Verification Endpoints

- **Liveness & Readiness:** `GET /health`
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected",
    "qdrant": "ready",
    "audit_chain": "verified"
  }
  ```
- **Audit Ledger Integrity Check:** `GET /api/v1/audit/verify`
  ```json
  {
    "is_valid": true,
    "record_count": 648,
    "error_description": null
  }
  ```
- **Run Full Automated Tests:**
  ```bash
  pytest -v tests/
  ```
