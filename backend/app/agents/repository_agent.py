from pathlib import Path
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.repository.file_scanner import FileScanner
from app.core.logging import logger

class RepositoryAnalysisAgent:
    def __init__(self):
        self.scanner = FileScanner()

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"RepositoryAnalysisAgent: Scanning repository at {state.repository_path}")
        repo_dir = Path(state.repository_path)
        
        files_data, language_stats, total_files, total_lines = self.scanner.scan_repository(repo_dir)
        
        # Identify key files and frameworks
        key_files = []
        frameworks = []

        file_paths = [f["path"] for f in files_data]
        for p in file_paths:
            p_lower = p.lower()
            if any(k in p_lower for k in ["main.py", "app.py", "index.ts", "server.js", "manage.py", "router"]):
                key_files.append(p)
            if "fastapi" in p_lower or "flask" in p_lower or "django" in p_lower:
                frameworks.append(p.split("/")[0])

        state.relevant_files = file_paths[:20] # Top files for context

        return {
            "status": "success",
            "total_files": total_files,
            "total_lines": total_lines,
            "languages": language_stats,
            "key_files": key_files,
            "frameworks": list(set(frameworks))
        }
