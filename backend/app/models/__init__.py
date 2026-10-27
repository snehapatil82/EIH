"""
SQLAlchemy models package initialization.
Import all models here to ensure that all declarative mappers are registered with Base.metadata
regardless of which module is imported first.
"""

from app.models.repository import Repository, RepositoryFile, CodeEntity
from app.models.chat import Conversation, Message
from app.models.task import EngineeringTask, TaskStep, AgentLog
from app.models.changes import CodeChange, ValidationResult, ReviewResult, TaskDiagram
from app.models.documentation import DocumentationItem, DocumentationGap
from app.models.terminal import TerminalSession

__all__ = [
    "Repository",
    "RepositoryFile",
    "CodeEntity",
    "Conversation",
    "Message",
    "EngineeringTask",
    "TaskStep",
    "AgentLog",
    "CodeChange",
    "ValidationResult",
    "ReviewResult",
    "TaskDiagram",
    "DocumentationItem",
    "DocumentationGap",
    "TerminalSession",
]
