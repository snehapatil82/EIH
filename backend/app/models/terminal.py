"""
Terminal Session SQLAlchemy Model — tracks per-task terminal sessions and command history.
"""
import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base


class TerminalSession(Base):
    __tablename__ = "terminal_sessions"

    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("engineering_tasks.id"), nullable=False, index=True)
    command = Column(Text, nullable=False)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    timed_out = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("EngineeringTask", foreign_keys=[task_id])
