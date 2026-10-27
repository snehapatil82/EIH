import difflib
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import logger
from app.core.security import validate_safe_path

class WorkspaceManager:
    def __init__(self, workspaces_base_dir: Optional[Path] = None):
        self.base_dir = workspaces_base_dir or settings.WORKSPACES_DIR

    def create_task_workspace(self, task_id: str, source_repo_path: Path) -> Path:
        """
        Creates an isolated staging copy of the source repository for a specific engineering task.
        """
        task_workspace = self.base_dir / task_id
        validate_safe_path(task_workspace, self.base_dir)

        if task_workspace.exists():
            shutil.rmtree(task_workspace, ignore_errors=True)

        logger.info(f"Creating isolated staging workspace at {task_workspace} from {source_repo_path}")
        # Copy repository files to workspace ignoring .git to avoid lock issues
        shutil.copytree(
            source_repo_path,
            task_workspace,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv")
        )
        return task_workspace

    def get_workspace_file_content(self, workspace_path: Path, rel_file_path: str) -> Optional[str]:
        target_path = workspace_path / rel_file_path
        validate_safe_path(target_path, workspace_path)

        if not target_path.exists() or not target_path.is_file():
            return None
        try:
            return target_path.read_text(encoding="utf-8")
        except Exception:
            return None

    def write_workspace_file(self, workspace_path: Path, rel_file_path: str, content: str) -> Path:
        target_path = workspace_path / rel_file_path
        validate_safe_path(target_path, workspace_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return target_path

    def delete_workspace_file(self, workspace_path: Path, rel_file_path: str) -> bool:
        target_path = workspace_path / rel_file_path
        validate_safe_path(target_path, workspace_path)

        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False

    def generate_diff(self, original_content: Optional[str], modified_content: str, file_path: str) -> str:
        """
        Generates standard unified diff format.
        """
        orig_lines = (original_content or "").splitlines(keepends=True)
        mod_lines = modified_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        return "".join(diff)

    def apply_workspace_to_repository(self, workspace_path: Path, target_repo_path: Path) -> int:
        """
        Applies changes from workspace back to the target repository after human approval.
        Returns count of files updated/added.
        """
        validate_safe_path(workspace_path, self.base_dir)
        count = 0

        for root, _, files in os.walk(workspace_path):
            for f in files:
                ws_file = Path(root) / f
                rel_path = ws_file.relative_to(workspace_path)
                target_file = target_repo_path / rel_path

                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ws_file, target_file)
                count += 1

        logger.info(f"Successfully applied {count} files from workspace {workspace_path} to repository {target_repo_path}")
        return count

    def cleanup_workspace(self, task_id: str):
        task_workspace = self.base_dir / task_id
        if task_workspace.exists():
            shutil.rmtree(task_workspace, ignore_errors=True)
