import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, index=True) # UUID
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False, unique=True, index=True)
    local_path = Column(String(512), nullable=False)
    default_branch = Column(String(100), default="main")
    status = Column(String(50), default="pending") # pending | cloning | indexed | error
    languages = Column(JSON, default=dict) # {"Python": 80, "TypeScript": 20}
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
    code_entities = relationship("CodeEntity", back_populates="repository", cascade="all, delete-orphan")
    dependencies = relationship("Dependency", back_populates="repository", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="repository", cascade="all, delete-orphan")
    tasks = relationship("EngineeringTask", back_populates="repository", cascade="all, delete-orphan")
    documentations = relationship("DocumentationItem", back_populates="repository", cascade="all, delete-orphan")
    documentation_gaps = relationship("DocumentationGap", back_populates="repository", cascade="all, delete-orphan")

class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id = Column(String(36), primary_key=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    path = Column(String(512), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    extension = Column(String(50), nullable=True)
    language = Column(String(50), nullable=True)
    size_bytes = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    summary = Column(Text, nullable=True)

    repository = relationship("Repository", back_populates="files")
    entities = relationship("CodeEntity", back_populates="file", cascade="all, delete-orphan")

class CodeEntity(Base):
    __tablename__ = "code_entities"

    id = Column(String(36), primary_key=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    file_id = Column(String(36), ForeignKey("repository_files.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False) # function | class | method | endpoint | module
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    signature = Column(Text, nullable=True)
    docstring = Column(Text, nullable=True)
    decorators = Column(JSON, default=list)
    calls = Column(JSON, default=list) # symbols called within this entity

    repository = relationship("Repository", back_populates="code_entities")
    file = relationship("RepositoryFile", back_populates="entities")

class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(String(36), primary_key=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=True)
    ecosystem = Column(String(50), nullable=False) # pip | npm | go | cargo
    source_file = Column(String(255), nullable=False)

    repository = relationship("Repository", back_populates="dependencies")
