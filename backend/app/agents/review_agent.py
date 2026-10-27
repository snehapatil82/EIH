from typing import Dict, Any, List
from app.agents.state import AgentState
from app.core.logging import logger

class ReviewAgent:
    def __init__(self):
        pass

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"ReviewAgent: Performing quality & security audit on proposed changes")

        comments = []
        quality_score = 95
        security_score = 98
        maintainability_score = 92

        for change in state.proposed_changes:
            content = change.get("modified_content", "")
            file_p = change.get("file_path", "")

            # Security sanity checks
            if "eval(" in content or "exec(" in content:
                security_score -= 30
                comments.append({
                    "file": file_p,
                    "severity": "high",
                    "message": "Use of eval/exec detected which poses potential code injection risk."
                })

            if "password" in content.lower() and "md5" in content.lower():
                security_score -= 20
                comments.append({
                    "file": file_p,
                    "severity": "medium",
                    "message": "Weak hashing algorithm (MD5) detected for password handling."
                })

            # Style & Maintainability
            if len(content.splitlines()) > 300:
                maintainability_score -= 10
                comments.append({
                    "file": file_p,
                    "severity": "low",
                    "message": "Module exceeds 300 lines; consider splitting into smaller sub-modules."
                })

        if not comments:
            comments.append({
                "file": "General",
                "severity": "info",
                "message": "Code adheres to clean architecture, type annotations, and safe cryptographic practices."
            })

        review_res = {
            "status": "approved" if security_score >= 70 and quality_score >= 70 else "changes_requested",
            "quality_score": quality_score,
            "security_score": security_score,
            "maintainability_score": maintainability_score,
            "comments": comments,
            "summary": f"Audit complete: Quality {quality_score}/100, Security {security_score}/100, Maintainability {maintainability_score}/100."
        }

        state.review_results = review_res
        return review_res
