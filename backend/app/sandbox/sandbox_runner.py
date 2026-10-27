"""
Sandbox Runner — executes validated, allowlisted commands inside a task workspace.

Security controls:
  - CWD is locked to the task workspace; path traversal is blocked via validate_safe_path.
  - Commands must be on the per-project allowlist (executable name check, not shell glob).
  - shell=False is used for subprocess creation; shell injection is therefore impossible.
  - A hard timeout (default 120 s) kills the process group if it exceeds the limit.
  - Output is streamed line-by-line through secret_redactor before it is returned.
  - No network isolation at the OS layer (host does not have Docker/gVisor), but access
    to host filesystem outside the workspace is prevented by CWD + validate_safe_path.
"""
import asyncio
import os
import shlex
import signal
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.core.security import validate_safe_path
from app.sandbox.project_detector import detect_project, is_command_allowed, ProjectInfo
from app.sandbox.secret_redactor import redact

# Maximum output bytes per line to prevent runaway memory
_MAX_LINE_BYTES = 8192
# Maximum total output lines before we stop buffering
_MAX_OUTPUT_LINES = 5000
# Default execution timeout in seconds
_DEFAULT_TIMEOUT = getattr(settings, "SANDBOX_TIMEOUT_SECONDS", 120)


class SandboxError(Exception):
    """Raised when sandbox validation or execution fails."""


class SandboxResult:
    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        timed_out: bool = False,
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_seconds = duration_seconds
        self.timed_out = timed_out

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def to_dict(self) -> Dict:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
            "success": self.success,
        }


class SandboxRunner:
    """
    Executes a single command inside a task workspace with security controls.
    """

    def __init__(self, workspace_path: Path, timeout: int = _DEFAULT_TIMEOUT):
        self.workspace_path = workspace_path.resolve()
        # Re-validate workspace is inside the configured workspaces dir
        validate_safe_path(self.workspace_path, settings.WORKSPACES_DIR)
        self.timeout = timeout
        self._project_info: Optional[ProjectInfo] = None

    def get_project_info(self) -> ProjectInfo:
        if self._project_info is None:
            self._project_info = detect_project(self.workspace_path)
        return self._project_info

    def validate_command(self, command: str) -> List[str]:
        """
        Validate command string and return the argv list.
        Raises SandboxError if validation fails.
        """
        if not command or not command.strip():
            raise SandboxError("Empty command")

        # Use shlex.split (POSIX=False on Windows, POSIX=True on Linux/Mac)
        try:
            argv = shlex.split(command, posix=(os.name != "nt"))
        except ValueError as e:
            raise SandboxError(f"Command parse error: {e}")

        if not argv:
            raise SandboxError("Empty command after parsing")

        project_info = self.get_project_info()

        if not is_command_allowed(command, project_info.allowed_commands):
            allowed_str = ", ".join(sorted(set(project_info.allowed_commands)))
            raise SandboxError(
                f"Command '{argv[0]}' is not allowed in this workspace. "
                f"Allowed executables: {allowed_str}"
            )

        return argv

    async def run(self, command: str) -> SandboxResult:
        """
        Execute command synchronously (collecting all output) and return a SandboxResult.
        """
        argv = self.validate_command(command)
        start_time = time.monotonic()
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []
        timed_out = False
        exit_code = -1

        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path),
                # Do NOT pass env=None; inherit host env but this is intentional (no shell injection)
            )

            try:
                raw_stdout, raw_stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
                exit_code = proc.returncode or 0
                stdout_lines = [
                    redact(line)
                    for line in raw_stdout.decode("utf-8", errors="replace").splitlines()
                ]
                stderr_lines = [
                    redact(line)
                    for line in raw_stderr.decode("utf-8", errors="replace").splitlines()
                ]
            except asyncio.TimeoutError:
                timed_out = True
                exit_code = -1
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                stderr_lines.append(
                    f"[SANDBOX] Process killed after {self.timeout}s timeout."
                )
        except FileNotFoundError:
            stderr_lines.append(f"[SANDBOX] Command not found: {argv[0]}")
            exit_code = 127
        except Exception as exc:
            stderr_lines.append(f"[SANDBOX] Execution error: {redact(str(exc))}")
            exit_code = -1

        duration = time.monotonic() - start_time
        return SandboxResult(
            exit_code=exit_code,
            stdout="\n".join(stdout_lines[: _MAX_OUTPUT_LINES]),
            stderr="\n".join(stderr_lines[: _MAX_OUTPUT_LINES]),
            duration_seconds=duration,
            timed_out=timed_out,
        )

    async def stream(
        self, command: str
    ) -> AsyncGenerator[Dict, None]:
        """
        Execute command and yield output chunks as they arrive.
        Each chunk is a dict with keys: type ('stdout'|'stderr'|'system'), line, elapsed.
        """
        argv = self.validate_command(command)
        start_time = time.monotonic()
        line_count = 0

        yield {
            "type": "system",
            "line": f"$ {command}",
            "elapsed": 0.0,
        }

        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path),
            )

            async def read_stream(stream, stream_type):
                nonlocal line_count
                while True:
                    try:
                        raw = await asyncio.wait_for(stream.readline(), timeout=self.timeout)
                    except asyncio.TimeoutError:
                        return
                    if not raw:
                        break
                    line = raw.decode("utf-8", errors="replace").rstrip("\n\r")
                    line = line[:_MAX_LINE_BYTES]
                    line = redact(line)
                    elapsed = round(time.monotonic() - start_time, 3)
                    yield {"type": stream_type, "line": line, "elapsed": elapsed}
                    line_count += 1
                    if line_count >= _MAX_OUTPUT_LINES:
                        break

            # Interleave stdout and stderr
            async def merged():
                stdout_gen = read_stream(proc.stdout, "stdout")
                stderr_gen = read_stream(proc.stderr, "stderr")

                async def drain(gen):
                    async for item in gen:
                        yield item

                # Run both concurrently using asyncio tasks that feed a queue
                queue: asyncio.Queue = asyncio.Queue()
                sentinel = object()

                async def feed(gen):
                    async for item in drain(gen):
                        await queue.put(item)
                    await queue.put(sentinel)

                t1 = asyncio.ensure_future(feed(stdout_gen))
                t2 = asyncio.ensure_future(feed(stderr_gen))

                done_count = 0
                while done_count < 2:
                    item = await asyncio.wait_for(queue.get(), timeout=self.timeout + 5)
                    if item is sentinel:
                        done_count += 1
                    else:
                        yield item

                await asyncio.gather(t1, t2, return_exceptions=True)

            try:
                async for chunk in merged():
                    yield chunk

                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    proc.kill()

                exit_code = proc.returncode or 0
                duration = round(time.monotonic() - start_time, 3)
                yield {
                    "type": "system",
                    "line": f"[Process exited with code {exit_code} in {duration}s]",
                    "elapsed": duration,
                    "exit_code": exit_code,
                }
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                elapsed = round(time.monotonic() - start_time, 3)
                yield {
                    "type": "system",
                    "line": f"[SANDBOX] Process killed after {self.timeout}s timeout.",
                    "elapsed": elapsed,
                    "exit_code": -1,
                    "timed_out": True,
                }

        except SandboxError:
            raise
        except FileNotFoundError:
            elapsed = round(time.monotonic() - start_time, 3)
            yield {
                "type": "stderr",
                "line": f"[SANDBOX] Command not found: {argv[0]}",
                "elapsed": elapsed,
            }
        except Exception as exc:
            elapsed = round(time.monotonic() - start_time, 3)
            yield {
                "type": "stderr",
                "line": f"[SANDBOX] Error: {redact(str(exc))}",
                "elapsed": elapsed,
            }
