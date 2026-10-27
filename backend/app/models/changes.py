import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base

class CodeChange(Base):
    __tablename__ = "code_changes"

    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    change_type = Column(String(50), nullable=False) # modify | add | delete
    original_content = Column(Text, nullable=True)
    modified_content = Column(Text, nullable=False)
    diff = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("EngineeringTask", back_populates="changes")

class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False, index=True)
    iteration = Column(Integer, default=1)
    status = Column(String(50), nullable=False) # passed | failed | warning
    syntax_passed = Column(Boolean, default=False)
    imports_passed = Column(Boolean, default=False)
    tests_passed = Column(Boolean, default=False)
    requirements_passed = Column(Boolean, default=False)
    details = Column(JSON, default=dict) # {"syntax_errors": [], "test_output": "...", "lint_errors": []}
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("EngineeringTask", back_populates="validation_results")

class ReviewResult(Base):
    __tablename__ = "review_results"

    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False, index=True)
    status = Column(String(50), default="approved") # approved | changes_requested
    quality_score = Column(Integer, default=90) # 0-100
    security_score = Column(Integer, default=95)
    maintainability_score = Column(Integer, default=90)
    comments = Column(JSON, default=list) # [{"file": "...", "severity": "info", "message": "..."}]
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("EngineeringTask", back_populates="review_results")

class TaskDiagram(Base):
    __tablename__ = "task_diagrams"

    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False, index=True)
    diagram_type = Column(String(50), nullable=False) # architecture | sequence | flowchart
    mermaid_code = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("EngineeringTask", back_populates="diagrams")

