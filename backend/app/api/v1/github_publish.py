"""
GitHub Publishing API — handles commit, branch creation, push, and PR creation
using the server-side GitHub token. Tokens are never exposed to the frontend.

Flow:
  1. GET  /tasks/{id}/github/status   — current repo/branch info
  2. GET  /tasks/{id}/github/diff     — git diff of workspace vs repo HEAD
  3. POST /tasks/{id}/github/branches — list remote branches
  4. POST /tasks/{id}/github/publish  — commit + push (requires explicit confirmation flag)
"""
import re
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field

import app.models
from app.database.connection import get_db
from app.models.task import EngineeringTask
from app.models.repository import Repository
from app.models.changes import CodeChange
from app.core.config import settings
from app.core.logging import logger
from app.core.security import validate_safe_path
from app.sandbox.secret_redactor import redact

router = APIRouter(prefix="/tasks/{task_id}/github", tags=["GitHub Publishing"])

# ─── Schemas ───────────────────────────────────────────────────────────────────

class PublishRequest(BaseModel):
    branch_name: str = Field(..., description="Target branch name (new or existing)")
    commit_message: str = Field(..., description="Commit message for the push")
    confirmed: bool = Field(False, description="Must be true — explicit user confirmation gate")
    create_pr: bool = Field(False, description="Create a pull request after push if supported")
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None


class BranchesRequest(BaseModel):
    pass


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _get_git_token() -> str:
    """
    Returns the GitHub token from server-side config.
    Raises if not configured — never prompts the user for a token in chat.
    """
    token = getattr(settings, "GITHUB_TOKEN", None)
    if not token:
        raise HTTPException(
            status_code=401,
            detail=(
                "GitHub token not configured on the server. "
                "Set GITHUB_TOKEN in backend/.env to enable publishing. "
                "Never paste tokens in chat or terminal commands."
            ),
        )
    return token


def _validate_branch_name(name: str) -> str:
    """Validate branch name against git naming rules."""
    # Reject names with disallowed patterns
    if not re.match(r'^[a-zA-Z0-9._\-/]+$', name):
        raise HTTPException(
            status_code=400,
            detail="Invalid branch name. Use only alphanumeric characters, '.', '_', '-', '/'.",
        )
    if name.startswith(".") or name.endswith(".") or name.endswith(".lock"):
        raise HTTPException(status_code=400, detail="Invalid branch name format")
    if ".." in name or " " in name or "~" in name:
        raise HTTPException(status_code=400, detail="Invalid branch name format")
    return name.strip()


def _safe_run_git(args: List[str], cwd: Path) -> tuple[str, str, int]:
    """Run a git command in a subprocess (no shell). Returns (stdout, stderr, returncode)."""
    import subprocess
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return redact(result.stdout.strip()), redact(result.stderr.strip()), result.returncode


async def _get_task_and_repo(task_id: str, db: AsyncSession):
    """Fetch task and its parent repository, raise 404 if not found."""
    task_res = await db.execute(select(EngineeringTask).where(EngineeringTask.id == task_id))
    task = task_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    repo_res = await db.execute(select(Repository).where(Repository.id == task.repository_id))
    repo = repo_res.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return task, repo


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def get_github_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return current Git status of the repository: current branch, latest commit SHA,
    remote URL (sanitized), and whether a GitHub token is configured.
    """
    task, repo = await _get_task_and_repo(task_id, db)
    repo_path = Path(repo.local_path)

    current_branch_out, _, _ = _safe_run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    head_sha_out, _, _ = _safe_run_git(["rev-parse", "HEAD"], repo_path)
    remote_url_out, _, _ = _safe_run_git(["remote", "get-url", "origin"], repo_path)

    # Sanitize remote URL: strip embedded credentials
    sanitized_url = re.sub(r"https://[^@]+@", "https://", remote_url_out)

    token_configured = bool(getattr(settings, "GITHUB_TOKEN", None))

    # Count changed files in workspace vs repo
    ws_path = Path(task.workspace_path) if task.workspace_path else None
    changed_files_count = 0
    if ws_path and ws_path.exists():
        changes_res = await db.execute(
            select(CodeChange).where(CodeChange.task_id == task_id)
        )
        changed_files_count = len(changes_res.scalars().all())

    return {
        "task_id": task_id,
        "repository_name": repo.name,
        "repository_owner": repo.owner,
        "remote_url": sanitized_url,
        "current_branch": current_branch_out or repo.default_branch,
        "default_branch": repo.default_branch,
        "head_commit_sha": head_sha_out[:12] if head_sha_out else None,
        "suggested_branch": task.branch_name or f"agent-task-{task_id[:8]}",
        "changed_files_count": changed_files_count,
        "token_configured": token_configured,
    }


@router.get("/diff")
async def get_git_diff(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return per-file diffs between the workspace (AI-modified files) and repo HEAD.
    Reuses CodeChange records already stored by the agent workflow.
    """
    task, repo = await _get_task_and_repo(task_id, db)

    changes_res = await db.execute(
        select(CodeChange).where(CodeChange.task_id == task_id).order_by(CodeChange.created_at.asc())
    )
    changes = changes_res.scalars().all()

    return {
        "task_id": task_id,
        "total_changed_files": len(changes),
        "changes": [
            {
                "file_path": c.file_path,
                "change_type": c.change_type,
                "diff": c.diff,
                "explanation": c.explanation,
                "applied": c.applied,
            }
            for c in changes
        ],
    }


@router.get("/branches")
async def list_branches(task_id: str, db: AsyncSession = Depends(get_db)):
    """List all remote branches for the repository."""
    task, repo = await _get_task_and_repo(task_id, db)
    repo_path = Path(repo.local_path)

    # Fetch without exposing token (use stored remote, token in git credential store)
    stdout, stderr, rc = _safe_run_git(["branch", "-r", "--format", "%(refname:short)"], repo_path)
    branches = [b.replace("origin/", "").strip() for b in stdout.splitlines() if b.strip()]

    return {
        "repository": repo.name,
        "branches": branches,
    }


@router.post("/publish")
async def publish_to_github(
    task_id: str,
    req: PublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Commit AI-generated changes and push to GitHub.

    IMPORTANT GATES:
    - req.confirmed MUST be True — enforced here on the backend.
    - Token is never sent from the client; it lives in server env only.
    - Direct push to protected branches (main, master, develop) is blocked unless
      the suggested branch matches the task's pre-assigned feature branch.
    """
    # ─── Gate 1: Explicit confirmation ────────────────────────────────────────
    if not req.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Publishing blocked: set 'confirmed': true to explicitly approve this push.",
        )

    # ─── Gate 2: Token ────────────────────────────────────────────────────────
    token = _get_git_token()

    # ─── Gate 3: Branch name validation ───────────────────────────────────────
    branch_name = _validate_branch_name(req.branch_name)

    # ─── Gate 4: Protected branch check ───────────────────────────────────────
    PROTECTED_BRANCHES = {"main", "master", "develop", "production", "release"}
    if branch_name in PROTECTED_BRANCHES:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Direct push to '{branch_name}' is not allowed. "
                f"Use a feature branch and create a pull request."
            ),
        )

    task, repo = await _get_task_and_repo(task_id, db)

    if not task.workspace_path:
        raise HTTPException(status_code=400, detail="Task workspace not found")

    repo_path = Path(repo.local_path)
    ws_path = Path(task.workspace_path)

    if not ws_path.exists():
        raise HTTPException(status_code=400, detail="Workspace directory no longer exists")

    # ─── Fetch approved changes ────────────────────────────────────────────────
    changes_res = await db.execute(
        select(CodeChange).where(CodeChange.task_id == task_id)
    )
    changes = changes_res.scalars().all()
    if not changes:
        raise HTTPException(status_code=400, detail="No code changes found for this task")

    try:
        # ─── 1. Create / checkout feature branch ──────────────────────────────
        existing_branches_out, _, _ = _safe_run_git(["branch", "--list", branch_name], repo_path)
        if existing_branches_out:
            # Branch exists locally — switch to it
            _safe_run_git(["checkout", branch_name], repo_path)
        else:
            # Create new branch from current HEAD
            _, _, rc = _safe_run_git(["checkout", "-b", branch_name], repo_path)
            if rc != 0:
                raise HTTPException(status_code=500, detail=f"Failed to create branch '{branch_name}'")

        # ─── 2. Apply workspace files to the repo path ────────────────────────
        import shutil, os
        applied_files: List[str] = []
        for change in changes:
            target_file = repo_path / change.file_path
            ws_file = ws_path / change.file_path

            if change.change_type == "delete":
                if target_file.exists():
                    target_file.unlink()
                    applied_files.append(change.file_path)
            elif ws_file.exists():
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ws_file, target_file)
                applied_files.append(change.file_path)

        if not applied_files:
            raise HTTPException(status_code=400, detail="No files could be applied from workspace")

        # ─── 3. Stage all changes ─────────────────────────────────────────────
        _safe_run_git(["add", "--all"], repo_path)

        # ─── 4. Commit ────────────────────────────────────────────────────────
        commit_msg = req.commit_message.strip()
        if not commit_msg:
            commit_msg = f"chore: AI-generated changes for task {task_id[:8]}"

        commit_out, commit_err, rc = _safe_run_git(
            ["commit", "--message", commit_msg, "--author", "Engineering Intelligence Hub <eih@noreply.local>"],
            repo_path,
        )
        if rc != 0:
            # Nothing to commit?
            if "nothing to commit" in commit_out.lower() or "nothing to commit" in commit_err.lower():
                raise HTTPException(status_code=400, detail="Nothing to commit — workspace matches repository state")
            raise HTTPException(status_code=500, detail=f"Commit failed: {commit_err}")

        # ─── 5. Extract commit SHA ────────────────────────────────────────────
        sha_out, _, _ = _safe_run_git(["rev-parse", "HEAD"], repo_path)
        commit_sha = sha_out[:12] if sha_out else "unknown"

        # ─── 6. Push using token (injected into URL, not exposed to client) ───
        remote_url_out, _, _ = _safe_run_git(["remote", "get-url", "origin"], repo_path)
        # Build authenticated URL
        base_url = re.sub(r"https://([^@]+@)?", "", remote_url_out).strip()
        auth_url = f"https://{token}@{base_url}"

        push_out, push_err, push_rc = _safe_run_git(
            ["push", auth_url, f"HEAD:refs/heads/{branch_name}"],
            repo_path,
        )
        if push_rc != 0:
            raise HTTPException(status_code=500, detail=f"Push failed: {redact(push_err)}")

        # ─── 7. Mark changes as applied ───────────────────────────────────────
        for c in changes:
            c.applied = True
        task.status = "approved"
        task.summary = f"Pushed {len(applied_files)} files to branch '{branch_name}' (commit {commit_sha})"
        await db.commit()

        # ─── 8. Optionally create PR via GitHub API ────────────────────────────
        pr_url = None
        if req.create_pr:
            try:
                pr_url = await _create_pull_request(
                    token=token,
                    owner=repo.owner,
                    repo_name=repo.name,
                    head_branch=branch_name,
                    base_branch=repo.default_branch,
                    title=req.pr_title or commit_msg,
                    body=req.pr_body or f"Automated PR from Engineering Intelligence Hub task {task_id[:8]}",
                )
            except Exception as pr_err:
                logger.warning(f"PR creation failed (push succeeded): {pr_err}")

        # Build commit link
        sanitized_remote = re.sub(r"https://[^@]+@", "https://", remote_url_out)
        sanitized_remote = sanitized_remote.rstrip("/").replace(".git", "")
        commit_url = f"{sanitized_remote}/commit/{sha_out}" if sha_out else None

        return {
            "status": "success",
            "task_id": task_id,
            "branch": branch_name,
            "commit_sha": commit_sha,
            "commit_url": commit_url,
            "files_pushed": len(applied_files),
            "pr_url": pr_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub publish failed for task {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Publishing failed: {redact(str(e))}")


async def _create_pull_request(
    token: str,
    owner: str,
    repo_name: str,
    head_branch: str,
    base_branch: str,
    title: str,
    body: str,
) -> Optional[str]:
    """Create a GitHub PR via the REST API. Returns the PR HTML URL."""
    import httpx

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "title": title[:256],
        "body": body[:65536],
        "head": head_branch,
        "base": base_branch,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"https://api.github.com/repos/{owner}/{repo_name}/pulls",
            headers=headers,
            json=payload,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("html_url")
        raise Exception(f"GitHub API error {resp.status_code}: {resp.text[:200]}")
