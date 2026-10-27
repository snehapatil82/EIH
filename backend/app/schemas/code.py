from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class CodeChangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    file_path: str
    change_type: str # modify | add | delete
    original_content: Optional[str] = None
    modified_content: str
    diff: str
    explanation: Optional[str] = None
    applied: bool
    created_at: datetime

class ValidationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    iteration: int
    status: str
    syntax_passed: bool
    imports_passed: bool
    tests_passed: bool
    requirements_passed: bool
    details: Dict[str, Any] = {}
    error_summary: Optional[str] = None
    created_at: datetime

class ReviewResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    status: str
    quality_score: int
    security_score: int
    maintainability_score: int
    comments: List[Dict[str, Any]] = []
    summary: Optional[str] = None
    created_at: datetime

class ArchitectureDiagramResponse(BaseModel):
    diagram_type: str # architecture | sequence | component | er
    mermaid_code: str
    description: str

class TaskDiagramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    diagram_type: str
    mermaid_code: str
    description: Optional[str] = None
    created_at: datetime

class ResearchMetricsResponse(BaseModel):
    task_id: str
    workflow_type: str
    complexity: str
    execution_time_seconds: float
    retrieval_latency_seconds: float
    total_tokens: int
    retry_iterations: int
    validation_status: str
    review_score: int
