from pathlib import Path
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.code_intelligence.ast_parser import PythonASTParser
from app.core.logging import logger

class CodeUnderstandingAgent:
    def __init__(self):
        self.parser = PythonASTParser()

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        target_dir = Path(state.repository_path) if state.repository_path and Path(state.repository_path).exists() else Path(state.workspace_path)
        logger.info(f"CodeUnderstandingAgent: Parsing symbols in directory {target_dir}")
        
        symbols_found = []
        endpoints_found = []

        for p in target_dir.rglob("*.py"):
            if ".venv" in p.parts or "__pycache__" in p.parts or "node_modules" in p.parts:
                continue
            try:
                rel = str(p.relative_to(target_dir)).replace("\\", "/")
                content = p.read_text(encoding="utf-8")
                res = self.parser.parse_source(content, rel)
                for ent in res.get("entities", []):
                    symbols_found.append({
                        "name": ent["name"],
                        "type": ent["entity_type"],
                        "file": rel,
                        "lines": f"{ent['start_line']}-{ent['end_line']}"
                    })
                endpoints_found.extend(res.get("endpoints", []))
            except Exception:
                continue

        return {
            "status": "success",
            "symbols_count": len(symbols_found),
            "endpoints_count": len(endpoints_found),
            "key_symbols": symbols_found[:15],
            "endpoints": endpoints_found[:10]
        }
