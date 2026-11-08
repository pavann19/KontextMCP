"""Evaluate a frozen, disjoint local question set without altering earlier experiments."""
import hashlib,json,os,shutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/"data/evaluation/heldout_v1.json"
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest==(ROOT/"data/evaluation/heldout_v1.sha256").read_text().strip()
    dataset=json.loads(source.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="kontext-holdout-") as temporary:
        data=Path(temporary)
        for name in ("raw","chunks"):shutil.copytree(ROOT/"data"/name,data/name)
        os.environ.update({"DATA_DIR":str(data),"RAW_DATA_DIR":str(data/"raw"),"CHUNKS_DIR":str(data/"chunks"),"QDRANT_PREFER_LOCAL":"false","QDRANT_HOST":"","AUDIT_LOG_PATH":str(data/"audit.jsonl"),"DATABASE_URL":"sqlite:///"+(data/"records.db").as_posix(),"LANGFUSE_ENABLED":"false","CORPUS_VARIANT":"curated","SYNTHESIS_MODE":"extractive"})
        from app.db.session import init_db,engine
        init_db()
        from app.agent.graph import run_agent_query
        from app.evaluation.benchmark_dataset import generate_benchmark_dataset
        from app.evaluation.evaluator import BenchmarkEvaluator
        known={" ".join(item.query.casefold().split()) for item in generate_benchmark_dataset()}
        assert not any(" ".join(row["query"].casefold().split()) in known for row in dataset["items"])
        results=[]
        for item in dataset["items"]:
            state=run_agent_query(item["query"],target_language=item["language"])
            matches=any(BenchmarkEvaluator._matches_expected_article(c["article_id"],item["expected_article_id"]) for c in state.citations)
            results.append({**item,"expected_article_returned":matches,"grounding_status":state.grounding_status,"citations":state.citations})
        from app.agent import nodes
        nodes._hybrid_retriever.dense.client.close();engine.dispose()
    report={"status":"MEASURED","dataset_sha256":digest,"queries":len(results),"overlap_with_fixed_benchmark":0,"expected_article_returned_rate":sum(r["expected_article_returned"] for r in results)/len(results),"source_verified_answers":sum(r["grounding_status"]=="SOURCE_VERIFIED" for r in results),"annotation_review":"UNVERIFIED: agent-authored expectations, not independent human/legal review","results":results}
    (ROOT/"artifacts/reports/heldout_evaluation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))
if __name__=="__main__":main()
