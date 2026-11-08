"""Refresh the evidence index without promoting historical checks to current passes."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.generate_all_reports import source_digest
from scripts.validate_docker import source_fingerprint

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "artifacts" / "reports"


def main():
    previous_path = REPORTS / "implementation_manifest.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    docker_runs = sorted((ROOT / "artifacts" / "docker").glob("*/report.json"))
    latest = docker_runs[-1]
    docker = json.loads(latest.read_text(encoding="utf-8"))
    docker["source_current"] = docker.get("source_sha256") == source_fingerprint()
    if docker.get("status") == "PASS" and not docker["source_current"]:
        docker["status"] = "REVALIDATION_REQUIRED"
    docker["raw_report"] = latest.relative_to(ROOT).as_posix()
    docker["historical_passing_report"] = previous.get("historical_docker_report")
    (REPORTS / "docker_validation.json").write_text(json.dumps(docker, indent=2), encoding="utf-8")
    reports = {}
    for name in previous["reports"]:
        path = REPORTS / name
        content = path.read_bytes()
        reports[name] = {"sha256": hashlib.sha256(content).hexdigest(),
                         "status": json.loads(content).get("status", "UNVERIFIED"),
                         "path": path.relative_to(ROOT).as_posix()}
    native = json.loads((REPORTS / "run_manifest.json").read_text(encoding="utf-8"))
    current = native.get("source_sha256") == source_digest()
    native_pass = native.get("status") == "PASS" and current
    remaining = dict(previous["remaining_requirements"])
    remaining["locked_container_validation"] = docker["status"]
    remaining["desktop_UI_invocation"] = reports["desktop_mcp_validation.json"]["status"]
    remaining["langfuse_live_ingestion_readback"] = reports["langfuse_validation.json"]["status"]
    report = {**previous, "timestamp": datetime.now(timezone.utc).isoformat(),
              "status": "NATIVE_VERIFIED_EXTERNAL_GAPS_REMAIN" if native_pass else "NATIVE_REVALIDATION_REQUIRED",
              "native_source_current": current, "reports": reports,
              "remaining_requirements": remaining,
              "docker_check_count": len(docker.get("checks", [])),
              "dependency_locks": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                   for path in ROOT.glob("requirements*.lock")},
              "docker_check_count_scope": "Latest Docker attempt only; historical results kept separately"}
    previous_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "native_source_current": current,
                      "docker_status": docker["status"]}))
    return 0 if native_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
