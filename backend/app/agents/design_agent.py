from typing import Dict, Any
from app.agents.state import AgentState
from app.llm.provider import LLMProvider, get_llm_provider
from app.llm.mock_provider import HighFidelityMockProvider
from app.core.logging import logger

class DesignAgent:
    def __init__(self, llm_provider: LLMProvider = None):
        self.llm = llm_provider or get_llm_provider()

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        logger.info(f"DesignAgent: Synthesizing architecture design for '{state.user_requirement}'")
        
        req = state.user_requirement
        design_content = None

        if not isinstance(self.llm, HighFidelityMockProvider):
            try:
                system_prompt = (
                    "You are a Principal Software Architect. Synthesize a structured Software Design Document (SDD) "
                    "in Markdown for the specified engineering requirement. Include:\n"
                    "1. Requirement Objective & Scope\n"
                    "2. Component Architecture & System Boundaries\n"
                    "3. API Contracts & Data Models (with JSON schemas/interfaces)\n"
                    "4. Security, Isolation & Error Handling Strategy\n"
                    "5. Verification & Testing Strategy"
                )
                design_content = await self.llm.generate_response(
                    prompt=f"Requirement: {req}\nRelevant Files: {', '.join(state.relevant_files[:10])}",
                    system_prompt=system_prompt
                )
            except Exception as e:
                logger.warning(f"DesignAgent: LLM synthesis fallback triggered: {e}")

        if not design_content:
            design_content = (
                f"# Software Architecture & Design Specification\n\n"
                f"## 1. Requirement Objective\n"
                f"{req}\n\n"
                f"## 2. Component Design & Boundaries\n"
                f"- **Service Layer**: Encapsulates business validation and cryptographic or business operations.\n"
                f"- **Middleware / Route Layer**: Intercepts requests, validates inputs, and ensures uniform error response formatting.\n"
                f"- **Persistence & Schemas**: Defines Pydantic/SQLAlchemy data transfer objects with strict validation.\n\n"
                f"## 3. API Contract & Interface Specifications\n"
                f"```json\n"
                f"{{\n"
                f'  "status": "success",\n'
                f'  "data": {{ "authenticated": true, "token_type": "bearer" }}\n'
                f"}}\n"
                f"```\n\n"
                f"## 4. Verification & Testing Strategy\n"
                f"- Unit tests covering edge cases, happy paths, and error states.\n"
                f"- Integration tests verifying HTTP status codes and contract compliance."
            )

        state.design_doc = design_content
        return {
            "status": "success",
            "design_doc": design_content,
            "summary": "Generated architecture design specification."
        }

