from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, HttpUrl, Field, ConfigDict

class RepositoryCreateRequest(BaseModel):
    url: str = Field(..., description="GitHub repository URL, e.g., https://github.com/fastapi/fastapi")
    branch: Optional[str] = Field(None, description="Optional branch or tag to clone")

class RepositoryFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    path: str
    filename: str
    extension: Optional[str] = None
    language: Optional[str] = None
    size_bytes: int
    line_count: int
    is_indexed: bool

class CodeEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_path: str
    name: str
    entity_type: str
    start_line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = []
    calls: List[str] = []

class DependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: Optional[str] = None
    ecosystem: str
    source_file: str

class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    owner: str
    url: str
    default_branch: str
    status: str
    languages: Dict[str, int] = {}
    total_files: int
    total_lines: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class RepositoryDetailResponse(RepositoryResponse):
    files: List[RepositoryFileResponse] = []
    dependencies: List[DependencyResponse] = []

class FileTreeItem(BaseModel):
    name: str
    path: str
    type: str # file | directory
    size: Optional[int] = None
    language: Optional[str] = None
    children: Optional[List['FileTreeItem']] = None

FileTreeItem.model_rebuild()

class FileContentResponse(BaseModel):
    path: str
    filename: str
    language: Optional[str] = None
    size_bytes: int
    line_count: int
    content: str

class FrameworkResponse(BaseModel):
    name: str
    category: str
    version: Optional[str] = None
    source: str
    icon: Optional[str] = "sparkles"
    confidence: Optional[str] = "high"

class DirectorySummary(BaseModel):
    name: str
    path: str
    file_count: int
    line_count: int
    languages: List[str] = []

class RepositoryOverviewResponse(BaseModel):
    repository_id: str
    name: str
    owner: str
    url: str
    default_branch: str
    status: str
    total_files: int
    total_lines: int
    total_directories: int
    languages: Dict[str, int] = {}
    language_percentages: Dict[str, float] = {}
    frameworks: List[FrameworkResponse] = []
    dependencies_count: int
    dependencies: List[DependencyResponse] = []
    entities_count: int
    entity_counts_by_type: Dict[str, int] = {}
    root_directories: List[DirectorySummary] = []
    manifest_files: List[str] = []
    key_entrypoints: List[str] = []

class DiagramNodeEvidence(BaseModel):
    id: str
    label: str
    evidence_type: str = "inferred"  # ui_route | api_endpoint | controller | model | business_logic | module | dependency | inferred
    source_file: Optional[str] = None
    line_range: Optional[str] = None
    entity_name: Optional[str] = None
    confidence: str = "verified"  # verified | inferred
    details: Optional[str] = None

class DiagramResponse(BaseModel):
    diagram_type: str
    view_mode: str = "code"  # code | workflow
    mermaid_code: str
    description: str
    summary: Optional[str] = None
    components_involved: List[str] = []
    key_relationships: List[str] = []
    source_references: List[str] = []
    evidence_status: str = "verified"  # verified | partial | unverified
    evidence_limitations: Optional[str] = None
    nodes_evidence: List[DiagramNodeEvidence] = []


class CallGraphFunctionSummary(BaseModel):
    id: str
    name: str
    full_name: str
    file_path: str
    start_line: int
    end_line: int
    enclosing_class: Optional[str] = None
    signature: Optional[str] = None
    caller_count: int = 0
    callee_count: int = 0
    is_async: bool = False


class CallGraphEdgeItem(BaseModel):
    caller_id: str
    caller_name: str
    callee_raw_name: str
    callee_symbol_name: str
    callee_id: Optional[str] = None
    call_site_line: int
    lexical_order: int = 0
    source_file: str
    target_file: Optional[str] = None
    is_conditional: bool = False
    branch_condition: Optional[str] = None
    is_loop: bool = False
    is_exception: bool = False
    is_async: bool = False
    is_recursive: bool = False
    is_dynamic: bool = False
    is_external: bool = False
    is_resolved: bool = False


class CallGraphNodeItem(BaseModel):
    id: str
    name: str
    full_name: str
    file_path: str
    start_line: int
    end_line: int
    enclosing_class: Optional[str] = None
    enclosing_module: str
    parameters: List[Dict[str, Any]] = []
    is_async: bool = False
    docstring: Optional[str] = None
    decorators: List[str] = []
    language: str = "Python"
    caller_count: int = 0
    callee_count: int = 0


class CallGraphResponse(BaseModel):
    repository_id: str
    root_function_id: str
    root_function_name: str
    mode: str
    depth: int
    mermaid_code: str
    nodes: List[CallGraphNodeItem]
    edges: List[CallGraphEdgeItem]
    explanation: Dict[str, Any]
    stats: Dict[str, Any]


