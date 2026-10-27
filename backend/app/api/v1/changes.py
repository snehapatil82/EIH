from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import app.models
from app.database.connection import get_db
from app.models.task import EngineeringTask
from app.models.repository import Repository
from app.models.changes import CodeChange, ValidationResult, ReviewResult, TaskDiagram
from app.schemas.code import (
    CodeChangeResponse,
    ValidationResultResponse,
    ReviewResultResponse,
    TaskDiagramResponse
)
from app.schemas.task import TaskRevisionRequest
from app.repository.workspace_manager import WorkspaceManager
from app.core.logging import logger

router = APIRouter(prefix="/tasks/{task_id}", tags=["Code Changes & Approvals"])

workspace_manager = WorkspaceManager()

@router.get("/changes", response_model=List[CodeChangeResponse])
async def get_task_code_changes(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CodeChange).where(CodeChange.task_id == task_id)
    )
    return result.scalars().all()

@router.get("/validation", response_model=List[ValidationResultResponse])
async def get_task_validation_results(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ValidationResult).where(ValidationResult.task_id == task_id).order_by(ValidationResult.iteration.desc())
    )
    return result.scalars().all()

@router.get("/review", response_model=List[ReviewResultResponse])
async def get_task_review_results(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ReviewResult).where(ReviewResult.task_id == task_id).order_by(ReviewResult.created_at.desc())
    )
    return result.scalars().all()

@router.get("/diagrams", response_model=List[TaskDiagramResponse])
async def get_task_diagrams(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TaskDiagram).where(TaskDiagram.task_id == task_id).order_by(TaskDiagram.created_at.asc())
    )
    return result.scalars().all()

@router.post("/approve")
async def approve_task_changes(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Human-in-the-loop Gate:
    Applies the staged code changes to the original repository.
    """
    task_res = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
    task = task_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    repo_res = await db.execute(select(Repository).where(Repository.id == task.repository_id))
    repo = repo_res.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    ws_path = Path(task.workspace_path)
    repo_path = Path(repo.local_path)

    if not ws_path.exists():
        raise HTTPException(status_code=400, detail="Workspace directory no longer exists")

    # Apply changes
    applied_count = workspace_manager.apply_workspace_to_repository(ws_path, repo_path)

    # Update code changes status
    changes_res = await db.execute(select(CodeChange).where(CodeChange.task_id == task_id))
    all_changes = changes_res.scalars().all()
    changed_file_paths = []
    for ch in all_changes:
        ch.applied = True
        changed_file_paths.append(ch.file_path)

    task.status = "approved"
    task.summary = f"Approved and applied {applied_count} files to repository."
    await db.commit()

    # Automatically trigger Documentation Change Impact Analysis
    try:
        from app.services.documentation_service import DocumentationIntelligenceService
        doc_service = DocumentationIntelligenceService()
        await doc_service.sync_change_impact(repo, changed_file_paths, db)
    except Exception as doc_err:
        logger.warning(f"Documentation change impact sync warning: {doc_err}")

    return {
        "status": "success",
        "task_id": task_id,
        "action": "approved",
        "files_applied": applied_count
    }


@router.post("/reject")
async def reject_task_changes(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Human-in-the-loop Gate:
    Rejects the proposed changes and safely deletes the workspace.
    """
    task_res = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
    task = task_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    workspace_manager.cleanup_workspace(task_id)
    task.status = "rejected"
    task.summary = "Proposed changes were rejected by the user."
    await db.commit()

    return {
        "status": "success",
        "task_id": task_id,
        "action": "rejected"
    }

@router.post("/revise")
async def revise_task_changes(
    task_id: str,
    req: TaskRevisionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Human-in-the-loop Gate:
    Requests revisions with feedback.
    """
    task_res = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
    task = task_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    repo_res = await db.execute(select(Repository).where(Repository.id == task.repository_id))
    repo = repo_res.scalars().first()

    # Append revision requirement
    revised_req = f"{task.requirement} [Revision note: {req.feedback}]"
    task.requirement = revised_req
    task.status = "running"
    await db.commit()

    from app.api.v1.tasks import run_task_in_background
    background_tasks.add_task(
        run_task_in_background,
        task_id,
        repo.id,
        revised_req,
        repo.local_path,
        task.workflow_type
    )

    return {
        "status": "success",
        "task_id": task_id,
        "action": "revision_started"
    }
