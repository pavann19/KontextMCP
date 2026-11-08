"""Preserve upstream deployment; validate actual trace ingestion/readback when reachable."""
import argparse,hashlib,json
from pathlib import Path
import httpx
from scripts.process_runner import run_bounded
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--host");parser.add_argument("--public-key");parser.add_argument("--secret-key");args=parser.parse_args()
    response=httpx.get("https://raw.githubusercontent.com/langfuse/langfuse/production/docker-compose.yml",timeout=30);response.raise_for_status()
    folder=ROOT/"docker/upstream";folder.mkdir(exist_ok=True)
    snapshot=folder/("langfuse-"+hashlib.sha256(response.content).hexdigest()+".yml");snapshot.write_bytes(response.content)
    engine=run_bounded(["docker","info","--format","{{.MemTotal}}"],timeout=20)
    memory=int(engine.stdout.strip()) if engine.returncode==0 else None
    report={"status":"BLOCKED_RESOURCE","configuration":"Official upstream Compose snapshot preserved; provision non-default secrets before use","upstream_sha256":hashlib.sha256(response.content).hexdigest(),"upstream_source":"https://github.com/langfuse/langfuse/blob/production/docker-compose.yml","configured_docker_memory_bytes":memory,"recommended_vm_memory_bytes":16*1024**3,"deployment_started":False,"reason":"Docker memory is below the upstream local/VM recommendation; host settings and existing services were preserved."}
    if args.host:
        if not args.public_key or not args.secret_key:raise ValueError("Both project keys are required")
        import uuid,time
        from datetime import datetime,timezone
        identifier=uuid.uuid4().hex
        batch={"batch":[{"id":uuid.uuid4().hex,"type":"trace-create","timestamp":datetime.now(timezone.utc).isoformat(),"body":{"id":identifier,"name":"kontext-live-validation","input":"[QUERY OMITTED]"}}]}
        sent=httpx.post(args.host.rstrip('/')+'/api/public/ingestion',auth=(args.public_key,args.secret_key),json=batch,timeout=15);sent.raise_for_status()
        for _ in range(30):
            received=httpx.get(args.host.rstrip('/')+'/api/public/traces/'+identifier,auth=(args.public_key,args.secret_key),timeout=10)
            if received.status_code==200:break
            time.sleep(1)
        report={"status":"PASS" if received.status_code==200 else "FAIL","trace_id":identifier,"ingestion_status":sent.status_code,"readback_status":received.status_code,"deployment_started":False,"scope":"Configured real Langfuse ingest and readback"}
    elif engine.returncode:
        report["status"]="BLOCKED_DOCKER";report["reason"]="Docker engine unavailable; no optional stack started."
        report["diagnostic"]=engine.stderr
    elif memory>=16*1024**3:
        report["status"]="REQUIRES_SERVICE_SETUP";report["reason"]="Provision secrets, start the preserved upstream stack and supply its project endpoint/keys to this validator."
    (ROOT/"artifacts/reports/langfuse_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report))
if __name__=="__main__":main()
