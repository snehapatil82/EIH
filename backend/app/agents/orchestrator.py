import time
from typing import Dict, Any, List, Optional
from app.agents.state import AgentState
from app.agents.requirement_agent import RequirementAgent
from app.agents.repository_agent import RepositoryAnalysisAgent
from app.agents.code_understanding_agent import CodeUnderstandingAgent
from app.agents.design_agent import DesignAgent
from app.agents.code_agent import CodeGenerationAgent
from app.agents.test_agent import TestGenerationAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.diagram_agent import DiagramAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.review_agent import ReviewAgent
from app.core.logging import logger
from app.core.config import settings

class OrchestratorAgent:
    """
    Main Orchestrator Agent.
    Manages workflow routing, complexity classification, execution of specialized agents,
    and self-correction loops with human-in-the-loop gating.
    """
    def __init__(self):
        self.req_agent = RequirementAgent()
        self.repo_agent = RepositoryAnalysisAgent()
        self.code_understanding_agent = CodeUnderstandingAgent()
        self.design_agent = DesignAgent()
        self.code_agent = CodeGenerationAgent()
        self.test_agent = TestGenerationAgent()
        self.doc_agent = DocumentationAgent()
        self.diagram_agent = DiagramAgent()
        self.val_agent = ValidationAgent()
        self.review_agent = ReviewAgent()

    def classify_complexity(self, requirement: str) -> str:
        """
        Classifies task complexity into SIMPLE, MEDIUM, or COMPLEX.
        """
        req_lower = requirement.lower()
        word_count = len(requirement.split())

        # Simple informational or single-method lookups
        if any(w in req_lower for w in ["explain", "describe", "where is", "what is"]) and not any(w in req_lower for w in ["add", "create", "implement", "build", "refactor"]):
            return "SIMPLE"

        # Multi-objective or cross-cutting features are COMPLEX
        if (
            ("and" in req_lower or "," in req_lower)
            and any(k in req_lower for k in ["auth", "jwt", "doc", "test", "api", "database"])
        ) or any(k in req_lower for k in ["jwt", "authentication", "refactor", "sdd", "architecture"]):
            return "COMPLEX"

        # Single-target testing or isolated tweaks are MEDIUM
        if "test" in req_lower or "fix" in req_lower or word_count <= 8:
            return "MEDIUM"

        return "COMPLEX"

    async def execute_task_workflow(self, state: AgentState, progress_callback=None) -> AgentState:
        start_time = time.time()
        logger.info(f"Orchestrator: Beginning execution of Task {state.task_id} with requirement '{state.user_requirement}'")
        
        # 1. Complexity Classification
        state.complexity = self.classify_complexity(state.user_requirement)
        state.status = "running"
        await self._add_log(state, "orchestrator", "INFO", f"Task complexity classified as {state.complexity}", progress_callback=progress_callback)

        # 2. Requirement Decomposition
        state.active_agent = "requirement_agent"
        req_res = await self.req_agent.execute(state)
        await self._add_log(state, "requirement_agent", "ACTION", req_res.get("summary", "Decomposed requirement"), progress_callback=progress_callback)

        # 3. Repository Analysis
        state.active_agent = "repository_agent"
        repo_res = await self.repo_agent.execute(state)
        await self._add_log(state, "repository_agent", "ACTION", f"Scanned repository: {repo_res.get('total_files')} files identified.", progress_callback=progress_callback)

        # 4. Code Understanding
        state.active_agent = "code_understanding_agent"
        code_under_res = await self.code_understanding_agent.execute(state)
        await self._add_log(state, "code_understanding_agent", "ACTION", f"Extracted {code_under_res.get('symbols_count')} symbols and {code_under_res.get('endpoints_count')} endpoints.", progress_callback=progress_callback)

        # 5. System Design
        state.active_agent = "design_agent"
        design_res = await self.design_agent.execute(state)
        await self._add_log(state, "design_agent", "ACTION", "Formulated software architecture & API design.", progress_callback=progress_callback)

        # 6. Diagram Generation
        state.active_agent = "diagram_agent"
        diag_res = await self.diagram_agent.execute(state)
        await self._add_log(state, "diagram_agent", "ACTION", f"Generated {diag_res.get('diagrams_count')} Mermaid diagrams.", progress_callback=progress_callback)

        # Self-Correction Loop for Code Generation, Test Generation, and Validation
        max_retries = min(state.max_retries, settings.MAX_AGENT_RETRIES)
        for attempt in range(max_retries + 1):
            state.retry_count = attempt
            
            # Code Generation
            state.active_agent = "code_agent"
            code_res = await self.code_agent.execute(state)
            await self._add_log(state, "code_agent", "ACTION", f"Generated {code_res.get('changes_count')} proposed code changes.", progress_callback=progress_callback)

            # Test Generation
            state.active_agent = "test_agent"
            test_res = await self.test_agent.execute(state)
            await self._add_log(state, "test_agent", "ACTION", f"Generated test suites in {test_res.get('test_files')}.", progress_callback=progress_callback)

            # Documentation Generation
            state.active_agent = "documentation_agent"
            doc_res = await self.doc_agent.execute(state)
            await self._add_log(state, "documentation_agent", "ACTION", "Generated software specification documentation.", progress_callback=progress_callback)

            # Validation
            state.active_agent = "validation_agent"
            val_res = await self.val_agent.execute(state)
            
            if val_res.get("status") == "passed":
                await self._add_log(state, "validation_agent", "ACTION", "All syntax and sandbox test validations passed successfully.", progress_callback=progress_callback)
                break
            else:
                await self._add_log(state, "validation_agent", "WARNING", f"Validation failed on attempt {attempt + 1}: {val_res.get('error_summary')}. Triggering self-correction loop.", progress_callback=progress_callback)
                if attempt == max_retries:
                    await self._add_log(state, "orchestrator", "ERROR", f"Max retries ({max_retries}) exceeded.", progress_callback=progress_callback)

        # 7. Final Quality & Security Review
        state.active_agent = "review_agent"
        review_res = await self.review_agent.execute(state)
        await self._add_log(state, "review_agent", "ACTION", review_res.get("summary", "Review complete."), progress_callback=progress_callback)

        # 8. Human-in-the-loop Gating
        state.status = "waiting_approval"
        state.active_agent = "orchestrator"
        state.execution_time_seconds = round(time.time() - start_time, 2)
        await self._add_log(state, "orchestrator", "INFO", f"Task workflow finished in {state.execution_time_seconds}s. Waiting for human approval.", progress_callback=progress_callback)

        return state

    async def _add_log(self, state: AgentState, agent_name: str, level: str, message: str, meta: Optional[Dict] = None, progress_callback=None):
        log_entry = {
            "agent_name": agent_name,
            "level": level,
            "message": message,
            "metadata": meta or {},
            "timestamp": time.time()
        }
        state.logs.append(log_entry)
        logger.info(f"[{agent_name.upper()}] ({level}): {message}")
        if progress_callback:
            try:
                await progress_callback(state, agent_name, level, message)
            except Exception as cb_e:
                logger.debug(f"Progress callback exception ignored: {cb_e}")
