import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base

class DocumentationItem(Base):
    """
    Represents a managed technical document for a repository.
    Tracks generation state, ground truth validation, citations, and change impact.
    """
    __tablename__ = "documentation_items"

    id = Column(String(36), primary_key=True, index=True) # UUID
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    doc_type = Column(String(100), nullable=False, index=True) # readme, api_documentation, etc.
    title = Column(String(255), nullable=False)
    category = Column(String(50), default="technical") # project | technical
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False, default="")
    status = Column(String(50), default="not_generated") # up_to_date | update_recommended | outdated | not_generated
    coverage_score = Column(Float, default=0.0) # 0.0 - 100.0%
    validation_status = Column(String(50), default="unvalidated") # passed | warning | failed | unvalidated
    validation_details = Column(JSON, default=dict) # {"verified_claims": 18, "verified_files": 7, "verified_apis": 5, ...}
    citations = Column(JSON, default=list) # [{"file_path": "...", "start_line": 1, "end_line": 50, "snippet": "..."}]
    affected_files = Column(JSON, default=list) # list of files that triggered outdated status
    impact_reason = Column(Text, nullable=True)
    last_generated_at = Column(DateTime, nullable=True)
    is_ai_generated = Column(Boolean, default=False)
    source_file = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="documentations")
    versions = relationship("DocumentationVersion", back_populates="documentation", cascade="all, delete-orphan", order_by="DocumentationVersion.created_at.desc()")


class DocumentationVersion(Base):
    """
    Version history for documentation edits, regenerations, and revisions.
    """
    __tablename__ = "documentation_versions"

    id = Column(String(36), primary_key=True, index=True)
    documentation_id = Column(String(36), ForeignKey("documentation_items.id"), nullable=False, index=True)
    version_tag = Column(String(50), nullable=False) # e.g. v1.0, v1.1
    content = Column(Text, nullable=False)
    change_summary = Column(String(255), nullable=True)
    validation_status = Column(String(50), default="unvalidated")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    documentation = relationship("DocumentationItem", back_populates="versions")


class DocumentationGap(Base):
    """
    Identified documentation gap or missing technical specification in the repository.
    """
    __tablename__ = "documentation_gaps"

    id = Column(String(36), primary_key=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String(512), nullable=True)
    gap_type = Column(String(100), nullable=False) # undocumented_module | undocumented_api | missing_readme_section | missing_env | ...
    severity = Column(String(50), default="medium") # high | medium | low
    status = Column(String(50), default="open") # open | resolved
    suggested_doc_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    repository = relationship("Repository", back_populates="documentation_gaps")
