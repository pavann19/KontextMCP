"""Real independent Inspector CLI client using only disposable public fixtures."""
import json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory(prefix="kontext-inspector-") as temporary:
        data=Path(temporary)
        for name in ("raw","chunks"):shutil.copytree(ROOT/"data"/name,data/name)
        env={**os.environ,"DATA_DIR":str(data),"RAW_DATA_DIR":str(data/"raw"),"CHUNKS_DIR":str(data/"chunks"),"QDRANT_STORAGE_DIR":str(data/"vectors"),"QDRANT_PREFER_LOCAL":"false","QDRANT_HOST":"","AUDIT_LOG_PATH":str(data/"audit.jsonl"),"DATABASE_URL":"sqlite:///"+(data/"records.db").as_posix(),"API_KEYS":"{}","MCP_API_KEY":"","MCP_CATALOG_PATH":str(data/"catalog.json"),"MCP_CLIENT_CONFIG_PATH":str(data/"client.json"),"LANGFUSE_ENABLED":"false","CORPUS_VARIANT":"curated"}
        subprocess.run([sys.executable,"-m","app.db.seed_data"],cwd=ROOT,env=env,capture_output=True,check=True,timeout=30)
        prefix=[shutil.which("npx.cmd") if os.name=="nt" else shutil.which("npx"),"-y","-p","node@24.22.1","-p","@modelcontextprotocol/inspector@2.14.0","mcp-inspector","--cli","--client-config",str(data/"client.json"),"--cwd",str(ROOT)]
        for key in ("DATA_DIR","RAW_DATA_DIR","CHUNKS_DIR","QDRANT_STORAGE_DIR","QDRANT_PREFER_LOCAL","QDRANT_HOST","AUDIT_LOG_PATH","DATABASE_URL","API_KEYS","MCP_API_KEY","LANGFUSE_ENABLED","CORPUS_VARIANT"):
            if env[key]:prefix.extend(["-e",key+"="+env[key]])
        result=subprocess.run(prefix+["--method","tools/list",sys.executable,"-m","scripts.start_mcp"],cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=120)
        (ROOT/"artifacts/reports/inspector-output.txt").write_text(result.stdout+result.stderr,encoding="utf-8")
        assert result.returncode==0,result.stderr
        parsed=json.loads(result.stdout)
        assert {t["name"] for t in parsed["tools"]}=={"search_eu_ai_act_provisions","query_ai_system_compliance"}
        report={"status":"PASS","client":"MCP Inspector CLI 2.14.0","requested_node":"24.22.1","transport":"stdio","public_tools":len(parsed["tools"]),"desktop_ui":"UNVERIFIED; VS Code workspace config supplied separately"}
        (ROOT/"artifacts/reports/inspector_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps(report))
if __name__=="__main__":main()
