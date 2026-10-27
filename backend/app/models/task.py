import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base

class EngineeringTask(Base):
    __tablename__ = "engineering_tasks"

    id = Column(String(36), primary_key=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    requirement = Column(Text, nullable=False)
    status = Column(String(50), default="pending") # pending | planning | running | waiting_approval | approved | rejected | failed | completed
    complexity = Column(String(50), default="MEDIUM") # SIMPLE | MEDIUM | COMPLEX
    workflow_type = Column(String(50), default="multi_agent") # single_agent | multi_agent
    active_agent = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    workspace_path = Column(String(512), nullable=True)
    branch_name = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan", order_by="TaskStep.order")
    logs = relationship("AgentLog", back_populates="task", cascade="all, delete-orphan", order_by="AgentLog.created_at")
    changes = relationship("CodeChange", back_populates="task", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="task", cascade="all, delete-orphan")
    review_results = relationship("ReviewResult", back_populates="task", cascade="all, delete-orphan")
    diagrams = relationship("TaskDiagram", back_populates="task", cascade="all, delete-orphan")

class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False, index=True)
    order = Column(Integer, nullable=False)
    agent_name = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending") # pending | running | completed | failed | skipped
    output = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    task = relationship("EngineeringTask", back_populates="steps")

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    level = Column(String(20), default="INFO") # INFO | WARNING | ERROR | ACTION
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("EngineeringTask", back_populates="logs")
