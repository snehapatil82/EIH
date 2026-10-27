from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class TaskCreateRequest(BaseModel):
    requirement: str = Field(..., description="Software engineering requirement or feature request")
    workflow_preference: Optional[str] = Field("auto", description="auto | single_agent | multi_agent")

class TaskStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order: int
    agent_name: str
    title: str
    description: Optional[str] = None
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AgentLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_name: str
    level: str
    message: str
    metadata_json: Dict[str, Any] = {}
    created_at: datetime

class TaskRevisionRequest(BaseModel):
    feedback: str = Field(..., description="Revision feedback or specific changes requested by developer")

class EngineeringTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    title: str
    requirement: str
    status: str
    complexity: str
    workflow_type: str
    active_agent: Optional[str] = None
    retry_count: int
    max_retries: int
    branch_name: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    steps: List[TaskStepResponse] = []
    logs: List[AgentLogResponse] = []
