"""Audit both complete version locks with an isolated, explicitly supplied auditor."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from scripts.process_runner import run_bounded

ROOT = Path(__file__).resolve().parents[1]


def main():
    interpreter = os.environ.get("KONTEXT_AUDIT_PYTHON")
    if not interpreter:
        raise RuntimeError("Set KONTEXT_AUDIT_PYTHON to an isolated environment with requirements-audit.txt installed.")
    reports = ROOT / "artifacts" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    results = []
    for name, lock in (("app", "requirements-linux.lock"), ("sdk", "requirements-mcp-client.lock"),
                       ("bootstrap", "requirements-bootstrap.lock")):
        output = reports / ("dependency-audit-"+name+".json")
        # Remove no history: an incomplete run writes a distinct failure marker.
        result = run_bounded([interpreter, "-m", "pip_audit", "--no-deps", "--disable-pip",
            "-r", str(ROOT/lock), "-f", "json", "-o", str(output)], timeout=180)
        raw = json.loads(output.read_text(encoding="utf-8")) if output.exists() and result.returncode in (0, 1) else {}
        findings = sorted({v["id"] for d in raw.get("dependencies", []) for v in d.get("vulns", [])})
        skipped = [d["name"] for d in raw.get("dependencies", []) if d.get("skip_reason")]
        passed = result.returncode == 0 and bool(raw.get("dependencies")) and not findings and not skipped
        results.append({"lock": lock, "lock_sha256": hashlib.sha256((ROOT/lock).read_bytes()).hexdigest(),
            "status": "PASS" if passed else "FAIL", "exit_code": result.returncode,
            "packages": len(raw.get("dependencies", [])), "unique_advisories": findings,
            "skipped_packages": skipped, "raw_report": output.relative_to(ROOT).as_posix()})
    report = {"status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(), "tool": "pip-audit 2.10.1",
        "scope": "Known Python package advisories for version-locked app and SDK dependencies at query time",
        "limitations": "Not a container OS scan, penetration test, zero-day guarantee or hashed-wheel attestation.",
        "results": results}
    (reports/"dependency_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
