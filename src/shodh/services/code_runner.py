import os
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RunnerStatus(str, Enum):
    COMPLETED = "completed"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    OUTPUT_LIMIT_EXCEEDED = "output_limit_exceeded"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


@dataclass
class RunnerResult:
    status: RunnerStatus
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    exit_code: int | None = None


def run_python(
    source_code: str,
    stdin: str = "",
    time_limit_ms: int = 2000,
    memory_limit_mb: int = 256,
    output_limit_bytes: int = 65536,
) -> RunnerResult:

    # Validate limits
    if not 100 <= time_limit_ms <= 60000:
        raise ValueError("Invalid time limit")

    if not 32 <= memory_limit_mb <= 2048:
        raise ValueError("Invalid memory limit")

    if output_limit_bytes <= 0:
        raise ValueError("Invalid output limit")

    if len(source_code.encode("utf-8")) > 256 * 1024:
        raise ValueError("Source code too large")

    # Detect syntax errors
    try:
        compile(source_code, "main.py", "exec")
    except (SyntaxError, ValueError) as exc:
        return RunnerResult(
            status=RunnerStatus.COMPILATION_ERROR,
            stderr=str(exc)[:4000],
        )

    container_name = f"shodh-{uuid.uuid4().hex}"
    container_id = None

    try:
        with tempfile.TemporaryDirectory(prefix="shodh-") as tmp:

            directory = Path(tmp)
            os.chmod(directory, 0o755)

            source_file = directory / "main.py"
            source_file.write_text(source_code, encoding="utf-8")
            source_file.chmod(0o444)

            try:
                # Create isolated container
                create_command = [
                    "docker",
                    "create",

                    # Keep stdin open
                    "--interactive",

                    # Security restrictions
                    "--network", "none",
                    "--cpus", "1",
                    "--memory", f"{memory_limit_mb}m",
                    "--memory-swap", f"{memory_limit_mb}m",
                    "--pids-limit", "32",
                    "--read-only",
                    "--tmpfs",
                    "/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
                    "--cap-drop", "ALL",
                    "--security-opt", "no-new-privileges:true",
                    "--user", "65534:65534",

                    # Working directory
                    "--workdir", "/workspace",

                    # Only submitted source is mounted
                    "--mount",
                    f"type=bind,src={directory},dst=/workspace,readonly",

                    "--log-driver", "none",

                    # Environment
                    "--env", "PYTHONDONTWRITEBYTECODE=1",
                    "--env", "PYTHONUNBUFFERED=1",

                    "--name", container_name,

                    "python:3.12-slim",
                    "python", "-B", "/workspace/main.py",
                ]

                created = subprocess.run(
                    create_command,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )

                if created.returncode != 0:
                    return RunnerResult(
                        status=RunnerStatus.INFRASTRUCTURE_ERROR,
                        stderr=created.stderr[:4000],
                    )

                container_id = created.stdout.strip()

                if not container_id:
                    return RunnerResult(
                        status=RunnerStatus.INFRASTRUCTURE_ERROR,
                        stderr="Docker did not return a container ID",
                    )

                # Start container and attach stdin/stdout/stderr
                started = time.monotonic()

                process = subprocess.Popen(
                    [
                        "docker",
                        "start",
                        "--attach",
                        "--interactive",
                        container_id,
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                stdout_data = bytearray()
                stderr_data = bytearray()

                total_output = [0]
                lock = threading.Lock()
                output_exceeded = threading.Event()

                # Read stdout and stderr without blocking
                def drain(stream, destination):
                    while True:
                        chunk = stream.read(4096)

                        if not chunk:
                            break

                        with lock:
                            remaining = max(
                                0,
                                output_limit_bytes - total_output[0],
                            )

                            accepted = chunk[:remaining]

                            destination.extend(accepted)
                            total_output[0] += len(accepted)

                            if len(chunk) > remaining:
                                output_exceeded.set()

                # Forward test input to Python stdin
                def send_input():
                    try:
                        process.stdin.write(stdin.encode("utf-8"))
                        process.stdin.close()
                    except (BrokenPipeError, OSError):
                        pass

                readers = [
                    threading.Thread(
                        target=drain,
                        args=(process.stdout, stdout_data),
                        daemon=True,
                    ),
                    threading.Thread(
                        target=drain,
                        args=(process.stderr, stderr_data),
                        daemon=True,
                    ),
                ]

                for reader in readers:
                    reader.start()

                writer = threading.Thread(
                    target=send_input,
                    daemon=True,
                )
                writer.start()

                # Enforce wall-clock timeout
                deadline = started + (time_limit_ms / 1000)
                timed_out = False

                while process.poll() is None:

                    if output_exceeded.is_set():
                        break

                    if time.monotonic() >= deadline:
                        timed_out = True
                        break

                    time.sleep(0.01)

                # Stop execution when a limit is exceeded
                if timed_out or output_exceeded.is_set():
                    subprocess.run(
                        ["docker", "kill", container_id],
                        capture_output=True,
                        timeout=5,
                        check=False,
                    )

                try:
                    exit_code = process.wait(timeout=5)

                except subprocess.TimeoutExpired:
                    process.kill()
                    exit_code = process.wait()

                for reader in readers:
                    reader.join(timeout=2)

                writer.join(timeout=2)

                execution_time_ms = int(
                    (time.monotonic() - started) * 1000
                )

                # Check whether Docker killed the container for OOM
                oom_check = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        "--format={{.State.OOMKilled}}",
                        container_id,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )

                oom_killed = oom_check.stdout.strip() == "true"

                # Determine execution result
                if timed_out:
                    status = RunnerStatus.TIME_LIMIT_EXCEEDED

                elif output_exceeded.is_set():
                    status = RunnerStatus.OUTPUT_LIMIT_EXCEEDED

                elif oom_killed:
                    status = RunnerStatus.MEMORY_LIMIT_EXCEEDED

                elif exit_code == 0:
                    status = RunnerStatus.COMPLETED

                else:
                    status = RunnerStatus.RUNTIME_ERROR

                return RunnerResult(
                    status=status,
                    stdout=stdout_data.decode(
                        "utf-8",
                        errors="replace",
                    ),
                    stderr=stderr_data.decode(
                        "utf-8",
                        errors="replace",
                    ),
                    execution_time_ms=execution_time_ms,
                    exit_code=exit_code,
                )

            except (OSError, subprocess.SubprocessError) as exc:
                return RunnerResult(
                    status=RunnerStatus.INFRASTRUCTURE_ERROR,
                    stderr=str(exc)[:4000],
                )

            finally:
                # Always remove the container before deleting temp files
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", container_name],
                        capture_output=True,
                        timeout=5,
                        check=False,
                    )
                except subprocess.SubprocessError:
                    pass

    except OSError as exc:
        return RunnerResult(
            status=RunnerStatus.INFRASTRUCTURE_ERROR,
            stderr=str(exc)[:4000],
        )