import uuid
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

import app.models  # Ensures all SQLAlchemy mappers are configured
from app.core.config import settings
from app.database.connection import get_db, AsyncSessionLocal
from app.models.repository import Repository
from app.models.task import EngineeringTask, TaskStep, AgentLog
from app.models.changes import CodeChange, ValidationResult, ReviewResult, TaskDiagram
from app.schemas.task import TaskCreateRequest, EngineeringTaskResponse
from app.agents.state import AgentState
from app.agents.orchestrator import OrchestratorAgent
from app.repository.workspace_manager import WorkspaceManager
from app.core.logging import logger
from fastapi.responses import StreamingResponse
import json

router = APIRouter(tags=["Engineering Tasks"])

orchestrator = OrchestratorAgent()
workspace_manager = WorkspaceManager()

async def run_task_in_background(task_id: str, repo_id: str, requirement: str, repo_path: str, workflow_pref: str):
    """Executes the agentic workflow and persists all results and logs to the database."""
    async with AsyncSessionLocal() as db:
        # Create staging workspace
        ws_path = workspace_manager.create_task_workspace(task_id, Path(repo_path))
        
        state = AgentState(
            task_id=task_id,
            repository_id=repo_id,
            repository_path=repo_path,
            workspace_path=str(ws_path),
            user_requirement=requirement,
            workflow_type="single_agent" if workflow_pref == "single_agent" else "multi_agent"
        )

        # Mark task as running immediately
        res = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
        task_obj = res.scalars().first()
        if task_obj:
            task_obj.status = "running"
            task_obj.active_agent = "requirement_agent"
            await db.commit()

        # Real-time progress callback to persist steps and logs to database as agents execute
        async def on_progress(current_state: AgentState, agent_name: str, level: str, message: str):
            async with AsyncSessionLocal() as session:
                t_res = await session.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
                t_entity = t_res.scalars().first()
                if not t_entity:
                    return
                t_entity.active_agent = agent_name
                t_entity.status = current_state.status
                t_entity.complexity = current_state.complexity
                t_entity.retry_count = current_state.retry_count

                # Save log entry
                log_obj = AgentLog(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    agent_name=agent_name,
                    level=level,
                    message=message,
                    metadata_json={}
                )
                session.add(log_obj)

                # If steps have been created in plan, update or insert TaskStep records
                if current_state.task_plan:
                    steps_res = await session.execute(
                        select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.order)
                    )
                    existing_steps = {s.order: s for s in steps_res.scalars().all()}
                    
                    for p in current_state.task_plan:
                        step_order = p["step"]
                        step_agent = p["agent"]
                        step_title = p["title"]
                        
                        if step_agent == agent_name:
                            step_status = "running"
                        elif any(l["agent_name"] == step_agent and l["level"] == "ACTION" for l in current_state.logs):
                            step_status = "completed"
                        else:
                            step_status = "pending"

                        if step_order in existing_steps:
                            existing_steps[step_order].status = step_status
                        else:
                            new_step = TaskStep(
                                id=str(uuid.uuid4()),
                                task_id=task_id,
                                order=step_order,
                                agent_name=step_agent,
                                title=step_title,
                                status=step_status
                            )
                            session.add(new_step)

                await session.commit()

        try:
            state = await orchestrator.execute_task_workflow(state, progress_callback=on_progress)

            # Re-fetch task object for final persistence
            res = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
            task_obj = res.scalars().first()
            if task_obj:
                task_obj.status = state.status
                task_obj.complexity = state.complexity
                task_obj.active_agent = state.active_agent
                task_obj.retry_count = state.retry_count
                task_obj.summary = f"Workflow finished with {len(state.proposed_changes)} proposed changes."

                # Ensure all plan steps are marked completed
                steps_res = await db.execute(select(TaskStep).where(TaskStep.task_id == task_id))
                existing_steps = {s.order: s for s in steps_res.scalars().all()}
                for p in state.task_plan:
                    if p["step"] in existing_steps:
                        existing_steps[p["step"]].status = "completed"
                    else:
                        db.add(TaskStep(
                            id=str(uuid.uuid4()),
                            task_id=task_id,
                            order=p["step"],
                            agent_name=p["agent"],
                            title=p["title"],
                            status="completed"
                        ))

                # Clear previous changes and diagrams for this task if revision/re-run
                from sqlalchemy import delete
                await db.execute(delete(CodeChange).where(CodeChange.task_id == task_id))
                await db.execute(delete(TaskDiagram).where(TaskDiagram.task_id == task_id))

                # Save Proposed Changes
                for c in state.proposed_changes:
                    change_obj = CodeChange(
                        id=str(uuid.uuid4()),
                        task_id=task_id,
                        file_path=c["file_path"],
                        change_type=c["change_type"],
                        original_content=c.get("original_content"),
                        modified_content=c["modified_content"],
                        diff=c["diff"],
                        explanation=c.get("explanation")
                    )
                    db.add(change_obj)

                # Save Diagrams
                for d in state.diagrams:
                    diag_obj = TaskDiagram(
                        id=str(uuid.uuid4()),
                        task_id=task_id,
                        diagram_type=d.get("type", "architecture"),
                        mermaid_code=d.get("mermaid_code", ""),
                        description=d.get("description", "")
                    )
                    db.add(diag_obj)

                # Save Validation Result
                val_data = state.validation_results
                val_obj = ValidationResult(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    iteration=state.retry_count + 1,
                    status=val_data.get("status", "passed"),
                    syntax_passed=val_data.get("syntax_passed", True),
                    imports_passed=val_data.get("imports_passed", True),
                    tests_passed=val_data.get("tests_passed", True),
                    requirements_passed=val_data.get("requirements_passed", True),
                    details=val_data.get("details", {}),
                    error_summary=val_data.get("error_summary")
                )
                db.add(val_obj)

                # Save Review Result
                rev_data = state.review_results
                rev_obj = ReviewResult(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    status=rev_data.get("status", "approved"),
                    quality_score=rev_data.get("quality_score", 90),
                    security_score=rev_data.get("security_score", 95),
                    maintainability_score=rev_data.get("maintainability_score", 90),
                    comments=rev_data.get("comments", []),
                    summary=rev_data.get("summary")
                )
                db.add(rev_obj)

                await db.commit()
                logger.info(f"Task {task_id} state successfully saved to database.")
        except Exception as e:
            logger.error(f"Task {task_id} workflow failed: {e}", exc_info=True)
            res = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
            task_obj = res.scalars().first()
            if task_obj:
                task_obj.status = "failed"
                task_obj.summary = f"Error: {str(e)}"
                error_log = AgentLog(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    agent_name="orchestrator",
                    level="ERROR",
                    message=f"Workflow failed: {str(e)}",
                    metadata_json={}
                )
                db.add(error_log)
                await db.commit()

@router.post("/repositories/{repository_id}/tasks", response_model=EngineeringTaskResponse)
async def create_engineering_task(
    repository_id: str,
    req: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    task_id = str(uuid.uuid4())
    task_obj = EngineeringTask(
        id=task_id,
        repository_id=repository_id,
        title=req.requirement[:80],
        requirement=req.requirement,
        status="planning",
        complexity="MEDIUM",
        workflow_type=req.workflow_preference or "multi_agent",
        workspace_path=str(settings.WORKSPACES_DIR / task_id),
        branch_name=f"agent-task-{task_id[:8]}"
    )
    db.add(task_obj)
    await db.commit()

    # Re-query with eager loading to avoid lazy-load errors in async SQLAlchemy
    result_task = await db.execute(
        select(EngineeringTask)
        .where(EngineeringTask.id == task_id)
        .options(
            selectinload(EngineeringTask.steps),
            selectinload(EngineeringTask.logs)
        )
    )
    task_obj = result_task.scalars().first()

    # Launch background task execution
    background_tasks.add_task(
        run_task_in_background,
        task_id,
        repo.id,
        req.requirement,
        repo.local_path,
        req.workflow_preference
    )

    return task_obj

@router.get("/tasks/{task_id}", response_model=EngineeringTaskResponse)
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EngineeringTask)
        .where(EngineeringTask.id == task_id)
        .options(
            selectinload(EngineeringTask.steps),
            selectinload(EngineeringTask.logs)
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/repositories/{repository_id}/tasks", response_model=List[EngineeringTaskResponse])
async def list_repository_tasks(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EngineeringTask)
        .where(EngineeringTask.repository_id == repository_id)
        .options(
            selectinload(EngineeringTask.steps),
            selectinload(EngineeringTask.logs)
        )
        .order_by(EngineeringTask.created_at.desc())
    )
    return result.scalars().all()

@router.get("/tasks/{task_id}/stream")
async def stream_task_progress(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Streams live task status updates and agent logs via Server-Sent Events (SSE).
    """
    async def event_generator():
        last_log_count = 0
        terminal_statuses = {"waiting_approval", "approved", "rejected", "failed", "completed"}
        
        while True:
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(EngineeringTask)
                    .where(EngineeringTask.id == task_id)
                    .options(
                        selectinload(EngineeringTask.steps),
                        selectinload(EngineeringTask.logs)
                    )
                )
                task = res.scalars().first()
                if not task:
                    yield f"event: error\ndata: {json.dumps({'error': 'Task not found'})}\n\n"
                    break

                new_logs = task.logs[last_log_count:]
                last_log_count = len(task.logs)

                payload = {
                    "task_id": task.id,
                    "status": task.status,
                    "active_agent": task.active_agent,
                    "retry_count": task.retry_count,
                    "steps": [
                        {
                            "id": s.id,
                            "order": s.order,
                            "title": s.title,
                            "agent_name": s.agent_name,
                            "status": s.status,
                            "description": s.description or ""
                        }
                        for s in task.steps
                    ],
                    "new_logs": [
                        {
                            "id": l.id,
                            "agent_name": l.agent_name,
                            "level": l.level,
                            "message": l.message,
                            "metadata_json": l.metadata_json or {},
                            "created_at": l.created_at.isoformat() if l.created_at else None
                        }
                        for l in new_logs
                    ]
                }
                yield f"event: update\ndata: {json.dumps(payload)}\n\n"

                if task.status in terminal_statuses:
                    yield f"event: complete\ndata: {json.dumps({'status': task.status})}\n\n"
                    break

            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

