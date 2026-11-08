import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.api import routes_benchmark as benchmark
from app.mcp.permissions import UserContext

USER = UserContext(username="operator", role="auditor", department="legal", clearance_level=3)


def test_no_benchmark_work_is_launched_from_missing_report_gets(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark.settings, "DATA_DIR", tmp_path)
    def forbidden(*args, **kwargs): raise AssertionError("GET started benchmark work")
    monkeypatch.setattr(benchmark, "run_all_evaluations", forbidden)
    for function in (benchmark.get_latest_benchmark_report, benchmark.get_latest_benchmark_json):
        with pytest.raises(HTTPException) as failure:
            function(USER)
        assert failure.value.status_code == 404


def test_production_benchmark_execution_disabled(monkeypatch):
    monkeypatch.setattr(benchmark.settings, "ENVIRONMENT", "production")
    with pytest.raises(HTTPException) as failure:
        benchmark.execute_benchmark_suite(None, USER)
    assert failure.value.status_code == 403


def test_host_filter_covers_rest_routes():
    with TestClient(app) as client:
        assert client.get("/api/v1/tools/list", headers={"Host": "unapproved.example"}).status_code == 400
