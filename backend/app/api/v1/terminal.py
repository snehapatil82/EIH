"""
Terminal API — executes validated project commands inside isolated task workspaces
and streams output via Server-Sent Events.
"""
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

import app.models  # Ensure all mappers registered
from app.database.connection import get_db, AsyncSessionLocal
from app.models.task import EngineeringTask
from app.models.terminal import TerminalSession
from app.sandbox.sandbox_runner import SandboxRunner, SandboxError
from app.sandbox.project_detector import detect_project
from app.core.logging import logger
from app.core.config import settings

router = APIRouter(prefix="/tasks/{task_id}/terminal", tags=["Integrated Terminal"])


# ─── Request / Response Schemas ────────────────────────────────────────────────

class RunCommandRequest(BaseModel):
    command: str
    timeout: Optional[int] = None  # override default; capped at SANDBOX_TIMEOUT_SECONDS


class TerminalHistoryEntry(BaseModel):
    id: str
    command: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    duration_seconds: Optional[int]
    timed_out: bool
    created_at: str


# ─── Helpers ───────────────────────────────────────────────────────────────────

async def _get_task_workspace(task_id: str, db: AsyncSession) -> Path:
    """Resolve and validate the workspace path for a given task."""
    result = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.workspace_path:
        raise HTTPException(status_code=400, detail="Task workspace has not been created yet")

    ws_path = Path(task.workspace_path)
    if not ws_path.exists():
        raise HTTPException(status_code=400, detail="Task workspace directory does not exist")

    return ws_path


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/info")
async def get_terminal_info(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return project type, detected manifests, allowed commands, and suggested quick-commands
    for the task workspace.
    """
    ws_path = await _get_task_workspace(task_id, db)
    info = detect_project(ws_path)
    return {
        "task_id": task_id,
        "workspace_path": str(ws_path),
        "project_type": info.project_type,
        "manifests": info.manifests,
        "allowed_commands": sorted(info.allowed_commands),
        "suggested_commands": info.suggested_commands,
    }


@router.post("/run")
async def run_command(
    task_id: str,
    req: RunCommandRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a single validated command in the task workspace and return the full result.
    Not for long-running commands — use /stream for those.
    """
    ws_path = await _get_task_workspace(task_id, db)

    max_timeout = getattr(settings, "SANDBOX_TIMEOUT_SECONDS", 120)
    timeout = min(req.timeout or max_timeout, max_timeout)

    runner = SandboxRunner(ws_path, timeout=timeout)

    try:
        result = await runner.run(req.command)
    except SandboxError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Persist to history
    session_id = str(uuid.uuid4())
    entry = TerminalSession(
        id=session_id,
        task_id=task_id,
        command=req.command,
        exit_code=result.exit_code,
        stdout=result.stdout[:16384],   # cap stored output
        stderr=result.stderr[:4096],
        duration_seconds=int(result.duration_seconds),
        timed_out=result.timed_out,
    )
    db.add(entry)
    await db.commit()

    return {
        "session_id": session_id,
        **result.to_dict(),
    }


@router.get("/stream")
async def stream_command(
    task_id: str,
    command: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a command and stream output line-by-line via Server-Sent Events.
    Each SSE event data is JSON: {type, line, elapsed, exit_code?, timed_out?}
    """
    ws_path = await _get_task_workspace(task_id, db)
    max_timeout = getattr(settings, "SANDBOX_TIMEOUT_SECONDS", 120)

    runner = SandboxRunner(ws_path, timeout=max_timeout)

    # Validate before starting the stream so we can return 400 synchronously
    try:
        runner.validate_command(command)
    except SandboxError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def event_generator():
        session_id = str(uuid.uuid4())
        stdout_buf: List[str] = []
        stderr_buf: List[str] = []
        final_exit_code = -1
        timed_out = False

        try:
            async for chunk in runner.stream(command):
                payload = json.dumps(chunk)
                yield f"event: output\ndata: {payload}\n\n"

                if chunk["type"] == "stdout":
                    stdout_buf.append(chunk["line"])
                elif chunk["type"] == "stderr":
                    stderr_buf.append(chunk["line"])
                elif chunk["type"] == "system":
                    if "exit_code" in chunk:
                        final_exit_code = chunk["exit_code"]
                    if chunk.get("timed_out"):
                        timed_out = True
        except SandboxError as e:
            err_payload = json.dumps({"type": "error", "line": str(e), "elapsed": 0.0})
            yield f"event: error\ndata: {err_payload}\n\n"
        except Exception as e:
            logger.error(f"Terminal stream error for task {task_id}: {e}", exc_info=True)
            err_payload = json.dumps({"type": "error", "line": "Internal terminal error", "elapsed": 0.0})
            yield f"event: error\ndata: {err_payload}\n\n"
        finally:
            # Persist session to DB asynchronously
            try:
                async with AsyncSessionLocal() as session:
                    entry = TerminalSession(
                        id=session_id,
                        task_id=task_id,
                        command=command,
                        exit_code=final_exit_code,
                        stdout="\n".join(stdout_buf)[:16384],
                        stderr="\n".join(stderr_buf)[:4096],
                        duration_seconds=None,
                        timed_out=timed_out,
                    )
                    session.add(entry)
                    await session.commit()
            except Exception as db_err:
                logger.warning(f"Failed to persist terminal session: {db_err}")

            done_payload = json.dumps({"session_id": session_id})
            yield f"event: done\ndata: {done_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history", response_model=List[TerminalHistoryEntry])
async def get_terminal_history(task_id: str, db: AsyncSession = Depends(get_db)):
    """Return all previously executed commands for this task session."""
    # Verify task exists
    task_result = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
    if not task_result.scalars().first():
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(TerminalSession)
        .where(TerminalSession.task_id == task_id)
        .order_by(TerminalSession.created_at.asc())
    )
    sessions = result.scalars().all()

    return [
        TerminalHistoryEntry(
            id=s.id,
            command=s.command,
            exit_code=s.exit_code,
            stdout=s.stdout,
            stderr=s.stderr,
            duration_seconds=s.duration_seconds,
            timed_out=s.timed_out,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in sessions
    ]
