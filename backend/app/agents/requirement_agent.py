import json
import re
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.llm.provider import LLMProvider, get_llm_provider
from app.llm.mock_provider import HighFidelityMockProvider
from app.core.logging import logger

class RequirementAgent:
    def __init__(self, llm_provider: LLMProvider = None):
        self.llm = llm_provider or get_llm_provider()

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"RequirementAgent: Analyzing requirement '{state.user_requirement}'")
        
        req = state.user_requirement.lower()
        plan = []

        # Try LLM decomposition if not default mock provider
        if not isinstance(self.llm, HighFidelityMockProvider):
            try:
                system_prompt = (
                    "You are a Senior Software Engineering Lead. Decompose the given user requirement "
                    "into a sequential execution plan using available agents: 'repository_agent', "
                    "'code_understanding_agent', 'design_agent', 'diagram_agent', 'code_agent', "
                    "'test_agent', 'documentation_agent', 'validation_agent', 'review_agent'. "
                    "Output ONLY valid JSON as a list of objects with keys: step (int), title (str), agent (str)."
                )
                raw_response = await self.llm.generate_response(
                    prompt=f"Requirement: {state.user_requirement}",
                    system_prompt=system_prompt
                )
                json_match = re.search(r"\[.*\]", raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    if isinstance(parsed, list) and len(parsed) >= 3:
                        plan = parsed
                        logger.info(f"RequirementAgent: Generated dynamic plan with {len(plan)} steps via LLM.")
            except Exception as e:
                logger.warning(f"RequirementAgent: LLM planning fallback triggered due to: {e}")

        # Fallback to structured domain decomposition
        if not plan:
            is_user_auth = any(k in req for k in ["auth", "jwt", "login", "register", "registration", "signup", "password", "user"])
            is_testing = any(k in req for k in ["test", "unit test", "coverage", "pytest"]) and not any(k in req for k in ["add", "create", "implement"])
            is_docs_arch = any(k in req for k in ["sdd", "software design", "architecture diagram", "spec"]) or (("doc" in req or "diagram" in req) and not any(k in req for k in ["endpoint", "api", "create"]))

            if is_user_auth:
                plan = [
                    {"step": 1, "title": "Analyze Repository Security, Models & Auth Patterns", "agent": "repository_agent"},
                    {"step": 2, "title": "Extract Existing User & API Schema Context", "agent": "code_understanding_agent"},
                    {"step": 3, "title": "Design User Registration Architecture, Endpoints & Security", "agent": "design_agent"},
                    {"step": 4, "title": "Generate User Registration API, Service & Password Hashing", "agent": "code_agent"},
                    {"step": 5, "title": "Generate Unit & Integration Tests for Registration & Auth", "agent": "test_agent"},
                    {"step": 6, "title": "Generate Architecture & Sequence Diagrams for Auth Flow", "agent": "diagram_agent"},
                    {"step": 7, "title": "Generate API Documentation & OpenAPI Specification", "agent": "documentation_agent"},
                    {"step": 8, "title": "Validate Syntax, Imports & Sandbox Test Suite", "agent": "validation_agent"},
                    {"step": 9, "title": "Perform Security, Cryptography & Quality Audit", "agent": "review_agent"},
                ]
            elif is_testing:
                plan = [
                    {"step": 1, "title": "Analyze Repository Modules & Core File Topology", "agent": "repository_agent"},
                    {"step": 2, "title": "Extract Function Signatures, Classes & Symbol Trees", "agent": "code_understanding_agent"},
                    {"step": 3, "title": "Design Unit & Integration Test Architecture", "agent": "design_agent"},
                    {"step": 4, "title": "Generate Comprehensive Unit and Edge Case Tests", "agent": "test_agent"},
                    {"step": 5, "title": "Execute and Validate Pytest Suite in Sandbox", "agent": "validation_agent"},
                    {"step": 6, "title": "Generate Test Coverage & Quality Review Report", "agent": "review_agent"},
                ]
            elif is_docs_arch:
                plan = [
                    {"step": 1, "title": "Analyze Repository Structure, Dependencies & Components", "agent": "repository_agent"},
                    {"step": 2, "title": "Extract System Classes, Call Graphs & Interfaces", "agent": "code_understanding_agent"},
                    {"step": 3, "title": "Generate Comprehensive Mermaid Architecture Diagrams", "agent": "diagram_agent"},
                    {"step": 4, "title": "Synthesize Software Design Document (SDD) & Specification", "agent": "documentation_agent"},
                    {"step": 5, "title": "Review Architecture Documentation & Completeness", "agent": "review_agent"},
                ]
            else:
                plan = [
                    {"step": 1, "title": "Analyze Repository Context and Affected Files", "agent": "repository_agent"},
                    {"step": 2, "title": "Extract Existing Symbols & Interface Signatures", "agent": "code_understanding_agent"},
                    {"step": 3, "title": "Design Implementation Strategy & Architecture", "agent": "design_agent"},
                    {"step": 4, "title": "Generate Proposed Code Implementation & Endpoints", "agent": "code_agent"},
                    {"step": 5, "title": "Generate Unit & Functional Tests for Proposed Changes", "agent": "test_agent"},
                    {"step": 6, "title": "Generate Architecture & Interaction Diagrams", "agent": "diagram_agent"},
                    {"step": 7, "title": "Generate Feature Documentation & Usage Guides", "agent": "documentation_agent"},
                    {"step": 8, "title": "Validate Syntax, Imports, and Sandbox Execution", "agent": "validation_agent"},
                    {"step": 9, "title": "Perform Code Quality & Security Audit", "agent": "review_agent"},
                ]

        state.task_plan = plan
        return {
            "status": "success",
            "plan": plan,
            "summary": f"Decomposed requirement into {len(plan)} structured engineering tasks."
        }

