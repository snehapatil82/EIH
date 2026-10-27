from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class Citation(BaseModel):
    file_path: str = Field(..., description="Repository relative file path")
    start_line: Optional[int] = Field(None, description="Starting line number")
    end_line: Optional[int] = Field(None, description="Ending line number")
    snippet: str = Field(..., description="Relevant code snippet or markdown chunk")
    score: Optional[float] = Field(None, description="Retrieval similarity score")

class ChatRequest(BaseModel):
    question: str = Field(..., description="Natural language question about repository")
    conversation_id: Optional[str] = Field(None, description="Optional existing conversation ID")

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    citations: List[Citation] = []
    created_at: datetime

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    title: str
    messages: List[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

class ChatAnswerResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: List[Citation] = []
    latency_seconds: float = 0.0
    tokens_used: int = 0
