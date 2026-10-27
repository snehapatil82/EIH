import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import git
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import logger
from app.core.security import parse_github_url, validate_safe_path

class GitService:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.CLONED_REPOS_DIR

    def clone_repository(self, url: str, repo_id: str, branch: Optional[str] = None) -> Tuple[Path, str]:
        """
        Clones a GitHub repository to the local isolated storage.
        Returns (target_path, default_branch).
        """
        owner, repo_name = parse_github_url(url)
        target_dir = self.base_dir / repo_id
        validate_safe_path(target_dir, self.base_dir)

        # If already exists, remove it first to allow clean re-indexing
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Cloning {url} into {target_dir}...")
        try:
            clone_kwargs = {"depth": 1}
            if branch:
                clone_kwargs["branch"] = branch
            
            repo = git.Repo.clone_from(url, target_dir, **clone_kwargs)
            default_branch = repo.active_branch.name if not repo.head.is_detached else (branch or "main")
            return target_dir, default_branch
        except Exception as e:
            logger.error(f"Git clone failed for {url}: {e}")
            # Try fallback using subprocess git clone
            try:
                cmd = ["git", "clone", "--depth", "1"]
                if branch:
                    cmd.extend(["-b", branch])
                cmd.extend([url, str(target_dir)])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    raise Exception(result.stderr)
                return target_dir, branch or "main"
            except Exception as sub_e:
                if target_dir.exists():
                    shutil.rmtree(target_dir, ignore_errors=True)
                raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(sub_e)}")

    def get_repo_head_commit(self, repo_dir: Path) -> Optional[str]:
        try:
            repo = git.Repo(repo_dir)
            return repo.head.commit.hexsha
        except Exception:
            return None
