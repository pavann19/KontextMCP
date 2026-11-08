import sys
import time

from scripts.process_runner import run_bounded


def test_timeout_does_not_wait_for_inherited_output_handle():
    child = "import time; time.sleep(3)"
    parent = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
        "print('started',flush=True); time.sleep(20)"
    )
    start = time.monotonic()
    result = run_bounded([sys.executable, "-c", parent], timeout=1)
    assert time.monotonic() - start < 2.8
    assert result.returncode == 124
    assert "started" in result.stdout
    assert "only the CLI process" in result.stderr


def test_command_failure_retains_both_streams():
    result = run_bounded([sys.executable, "-c",
                          "import sys; print('output'); print('failure',file=sys.stderr); sys.exit(7)"])
    assert result.returncode == 7
    assert result.stdout.strip() == "output"
    assert result.stderr.strip() == "failure"


def test_docker_preflight_reports_blocker_before_starting_resources(tmp_path, monkeypatch):
    import json
    import subprocess
    from scripts import validate_docker

    calls = []

    def unavailable(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1, "", "Engine unavailable")

    monkeypatch.setattr(validate_docker, "ROOT", tmp_path)
    monkeypatch.setattr(validate_docker, "run_bounded", unavailable)
    monkeypatch.setattr(validate_docker.shutil, "disk_usage",
                        lambda path: type("Usage", (), {"free": 10 * 1024**3})())
    assert validate_docker.main() == 1
    report = json.loads(next(tmp_path.glob("artifacts/docker/*/report.json")).read_text())
    assert report["status"] == "BLOCKED_DOCKER"
    assert report["cleanup"] == "NOT_REQUIRED"
    assert calls == [["docker", "info", "--format", "{{.ServerVersion}}"]]
