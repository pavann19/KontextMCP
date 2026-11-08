"""Bounded CLI execution even when a child inherits the command's output handles."""
import subprocess
import tempfile


def run_bounded(args, *, cwd=None, env=None, timeout=300):
    # Pipes can keep communicate() waiting after the CLI itself has been killed.
    # Files let us retain output without waiting for an inherited handle to close.
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            process = subprocess.Popen(args, cwd=cwd, env=env, stdout=stdout, stderr=stderr)
        except FileNotFoundError as exc:
            return subprocess.CompletedProcess(args, 127, "", str(exc))
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait(timeout=5)
        stdout.seek(0)
        stderr.seek(0)
        output = stdout.read().decode("utf-8", errors="replace")
        errors = stderr.read().decode("utf-8", errors="replace")
    if timed_out:
        errors += f"\nCommand timed out after {timeout}s; only the CLI process was stopped."
    return subprocess.CompletedProcess(args, 124 if timed_out else process.returncode, output, errors)
