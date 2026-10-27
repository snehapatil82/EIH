from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    task_id: str
    repository_id: str
    repository_path: str
    workspace_path: str
    user_requirement: str
    complexity: str = "MEDIUM" # SIMPLE | MEDIUM | COMPLEX
    workflow_type: str = "multi_agent" # single_agent | multi_agent
    active_agent: str = "orchestrator"
    
    # Context & Plan
    relevant_files: List[str] = Field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    task_plan: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Generated Artifacts
    design_doc: Optional[str] = None
    proposed_changes: List[Dict[str, Any]] = Field(default_factory=list) # [{file_path, change_type, original_content, modified_content, diff, explanation}]
    generated_tests: List[Dict[str, Any]] = Field(default_factory=list)
    generated_documentation: List[Dict[str, Any]] = Field(default_factory=list)
    diagrams: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Validation & Review
    validation_results: Dict[str, Any] = Field(default_factory=lambda: {
        "status": "pending",
        "syntax_passed": False,
        "imports_passed": False,
        "tests_passed": False,
        "requirements_passed": False,
        "error_summary": None,
        "details": {}
    })
    review_results: Dict[str, Any] = Field(default_factory=lambda: {
        "status": "pending",
        "quality_score": 90,
        "security_score": 95,
        "maintainability_score": 90,
        "comments": [],
        "summary": None
    })
    
    # Loop & Lifecycle Control
    retry_count: int = 0
    max_retries: int = 3
    status: str = "planning" # planning | running | waiting_approval | approved | rejected | failed | completed
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    # Metrics
    execution_time_seconds: float = 0.0
    total_tokens: int = 0
