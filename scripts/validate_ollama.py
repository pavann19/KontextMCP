"""Real isolated local-model generation and guarded source-selection proof."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import httpx

ROOT=Path(__file__).resolve().parents[1]


def main():
    executable=shutil.which("ollama")
    if not executable: raise RuntimeError("Ollama executable is not installed")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
    url=f"http://127.0.0.1:{port}"
    env={**os.environ,"OLLAMA_HOST":f"127.0.0.1:{port}","OLLAMA_NUM_PARALLEL":"1","OLLAMA_MAX_LOADED_MODELS":"1"}
    with tempfile.TemporaryDirectory(prefix="kontext-ollama-") as temporary:
        log=Path(temporary)/"server.log"
        with log.open("w") as stream:
            process=subprocess.Popen([executable,"serve"],env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
            try:
                deadline=time.monotonic()+30
                while True:
                    try:
                        tags=httpx.get(url+"/api/tags",timeout=2).json()["models"];break
                    except (httpx.HTTPError,KeyError):
                        if time.monotonic()>deadline:raise RuntimeError("Ollama startup failed")
                        time.sleep(.2)
                candidates=sorted([m for m in tags if m.get("size",10**12)<1_500_000_000],key=lambda m:m["size"])
                model=candidates[0]["name"] if candidates else "qwen2.5:0.5b"
                if not candidates:
                    response=httpx.post(url+"/api/pull",json={"name":model,"stream":False},timeout=300);response.raise_for_status()
                response=httpx.post(url+"/api/generate",json={"model":model,"prompt":"Return the word READY.","stream":False,"options":{"num_predict":16},"keep_alive":"2m"},timeout=90)
                response.raise_for_status();generation=response.json();assert generation.get("response")
                loaded=httpx.get(url+"/api/ps",timeout=3).json()
                assert loaded.get("models")
                data=Path(temporary)/"data";data.mkdir()
                for name in ("raw","chunks"):shutil.copytree(ROOT/"data"/name,data/name)
                os.environ.update({"DATA_DIR":str(data),"RAW_DATA_DIR":str(data/"raw"),"CHUNKS_DIR":str(data/"chunks"),"QDRANT_PREFER_LOCAL":"false","QDRANT_HOST":"","AUDIT_LOG_PATH":str(data/"audit.jsonl"),"DATABASE_URL":"sqlite:///"+(data/"records.db").as_posix(),"LANGFUSE_ENABLED":"false","OLLAMA_BASE_URL":url,"OLLAMA_MODEL":model,"OLLAMA_REQUEST_TIMEOUT":"90","SYNTHESIS_MODE":"ollama_select"})
                from app.db.session import init_db,engine
                init_db()
                from app.agent.graph import run_agent_query
                state=run_agent_query("What does Article 9 require?")
                from app.evaluation.entailment import calibrate
                calibration=calibrate(url,model)
                (ROOT/"artifacts/reports/entailment_calibration.json").write_text(json.dumps(calibration,indent=2),encoding="utf-8")
                result={"status":"PASS" if state.synthesis_backend=="ollama_selection" and state.grounding_status=="SOURCE_VERIFIED" else "FAIL","model":model,"real_generation":True,"loaded_model_verified":True,"synthesis_backend":state.synthesis_backend,"grounding_status":state.grounding_status,"limitation":"One local model and bounded query. Model selects allowed sources; no free-form model legal claims are exposed."}
                (ROOT/"artifacts/reports/ollama_validation.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
                from app.agent import nodes
                nodes._hybrid_retriever.dense.client.close();engine.dispose()
                print(json.dumps(result));return 0 if result["status"]=="PASS" else 1
            finally:
                if os.name=="nt":subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True)
                else:process.terminate()
                process.wait(timeout=15)

if __name__=="__main__":raise SystemExit(main())
