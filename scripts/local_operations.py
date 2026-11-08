"""Bounded load, dependency outage and PostgreSQL restore checks on fixture projects."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import httpx


def validate_operations(compose,environment,output,base_url,officer,command,record):
    root=Path(__file__).resolve().parents[1]
    with httpx.Client(base_url=base_url,headers=officer,timeout=10,trust_env=False) as client:
        record("readiness",client.get("/ready").status_code==200)
        record("authenticated_metrics",client.get("/metrics").status_code==200 and "kontext_audit_outbox_pending" in client.get("/metrics").text)
        metrics_text=client.get("/metrics").text
        record("audit_delivery_health_metrics", all(name in metrics_text for name in (
            "kontext_audit_outbox_oldest_pending_seconds", "kontext_audit_outbox_failed_pending",
            "kontext_audit_outbox_attempts_total")))
    backup=output/"postgres-fixture.dump"
    with backup.open("wb") as stream:
        result=subprocess.run(compose+["exec","-T","postgres","pg_dump","-U","postgres","-Fc","enterprise_rag"],env=environment,stdout=stream,stderr=subprocess.PIPE,timeout=60)
    record("postgres_backup",result.returncode==0 and backup.stat().st_size>0)
    command(compose+["exec","-T","postgres","createdb","-U","postgres","kontext_restore_fixture"],"restore-create-db")
    command(compose+["cp",str(backup),"postgres:/tmp/kontext-fixture.dump"],"restore-copy")
    command(compose+["exec","-T","postgres","pg_restore","-U","postgres","-d","kontext_restore_fixture","/tmp/kontext-fixture.dump"],"restore-database")
    sql="SELECT count(*) FROM compliance_assessments;"
    original=command(compose+["exec","-T","postgres","psql","-U","postgres","-d","enterprise_rag","-Atc",sql],"backup-row-count").stdout.strip()
    restored=command(compose+["exec","-T","postgres","psql","-U","postgres","-d","kontext_restore_fixture","-Atc",sql],"restore-row-count").stdout.strip()
    record("postgres_restore_matches",original==restored)
    # Only this uniquely named fixture project's database is stopped.
    command(compose+["stop","postgres"],"database-outage")
    try:
        with httpx.Client(base_url=base_url,timeout=10,trust_env=False) as client:
            record("readiness_detects_database_outage",client.get("/ready").status_code==503)
    finally:command(compose+["start","postgres"],"database-recovery")
    deadline=time.monotonic()+60
    with httpx.Client(base_url=base_url,timeout=5,trust_env=False) as client:
        while time.monotonic()<deadline:
            if client.get("/ready").status_code==200:break
            time.sleep(.5)
        else:raise RuntimeError("Database did not recover within the bounded test")
    record("database_connection_recovery",True)
    command(compose+["stop","qdrant"],"vector-outage")
    try:
        with httpx.Client(base_url=base_url,timeout=15,trust_env=False) as client:
            record("readiness_detects_vector_outage",client.get("/ready").status_code==503)
    finally:command(compose+["start","qdrant"],"vector-recovery")
    time.sleep(2)
    with httpx.Client(base_url=base_url,timeout=15,trust_env=False) as client:
        record("vector_connection_recovery",client.get("/ready").status_code==200)
    sdk=Path(os.environ.get("MCP_SDK_PYTHON",str(root/".venv-mcp-sdk"/("Scripts/python.exe" if os.name=="nt" else "bin/python"))))
    checked=subprocess.run([str(sdk),str(root/"scripts/check_mcp_http_sdk.py"),"--url",base_url+"/mcp"],env={**environment,"KONTEXT_HTTP_TEST_KEY":officer["X-API-Key"]},capture_output=True,text=True,timeout=65)
    record("official_sdk_http",checked.returncode==0, None if checked.returncode==0 else checked.stderr[-1000:])
    if checked.returncode==0:(output/"mcp-http-sdk.json").write_text(checked.stdout,encoding="utf-8")
    duration=int(os.environ.get("KONTEXT_LOAD_DURATION_SECONDS","60"))
    if not 1<=duration<=3600:raise ValueError("Load duration must be between 1 and 3600 seconds")
    workers=4;deadline=time.monotonic()+duration
    def load_worker(number):
        values=[]
        with httpx.Client(base_url=base_url,timeout=15,trust_env=False) as client:
            while time.monotonic()<deadline:
                start=time.perf_counter();status_code=None;grounding_status=None
                try:
                    operation=len(values)%4
                    if operation<2:
                        response=client.get("/api/v1/search",params={"q":"Article 9 risk management","top_k":3,"method":"reranked"})
                        ok=response.status_code==200 and any(hit["article_id"]=="Article 9" for hit in response.json().get("hits",[]))
                    elif operation==2:
                        response=client.post("/api/v1/chat",json={"query":"What does Article 9 require?"})
                        grounding_status=response.json().get("grounding_status")
                        ok=response.status_code==200 and grounding_status=="SOURCE_VERIFIED"
                    else:
                        response=client.post("/api/v1/tools/call",headers=officer,json={"name":"query_ai_system_compliance","arguments":{"system_id":"SYS-HR-001"}})
                        ok=response.status_code==200 and not response.json().get("isError",True)
                    status_code=response.status_code
                except Exception:ok=False
                values.append({"worker":number,"latency_ms":(time.perf_counter()-start)*1000,"valid":ok,"operation":("search" if operation<2 else "chat" if operation==2 else "database_read"),"status_code":status_code,"grounding_status":grounding_status})
        return values
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        rows=[item for group in executor.map(load_worker,range(workers)) for item in group]
    elapsed=time.monotonic()-started
    import numpy as np
    report={"status":"PASS" if rows and all(row["valid"] for row in rows) else "FAIL","scope":"Bounded local mixed search/chat/authorized-database load, not production capacity or a long-duration soak","duration_seconds":elapsed,"configured_duration_seconds":duration,"concurrency":workers,"requests":len(rows),"invalid_responses":sum(not r["valid"] for r in rows),"observed_requests_per_second":len(rows)/elapsed,"p50_ms":float(np.percentile([r["latency_ms"] for r in rows],50)),"p95_ms":float(np.percentile([r["latency_ms"] for r in rows],95)),"samples":rows}
    (output/"bounded-load.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    record("bounded_concurrent_load",report["status"]=="PASS")
    command(compose+["ps","--format","json"],"operational-service-state")
