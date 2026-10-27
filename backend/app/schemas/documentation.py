import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class CitationItem(BaseModel):
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    snippet: Optional[str] = None
    claim: Optional[str] = None
    score: Optional[float] = None

class ValidationClaimItem(BaseModel):
    type: str # file | entity | api | config | command
    reference: str
    exists: bool
    details: Optional[str] = None
    line_number: Optional[int] = None

class ValidationDetails(BaseModel):
    verified_claims: int = 0
    verified_files: int = 0
    verified_apis: int = 0
    outdated_references: int = 0
    unsupported_claims: int = 0
    claims: List[Dict[str, Any]] = []
    warnings: List[str] = []
    auto_corrected: bool = False

class DocumentationVersionResponse(BaseModel):
    id: str
    documentation_id: str
    version_tag: str
    content: str
    change_summary: Optional[str] = None
    validation_status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentationItemResponse(BaseModel):
    id: str
    repository_id: str
    doc_type: str
    title: str
    category: str
    description: Optional[str] = None
    content: str
    status: str # up_to_date | update_recommended | outdated | not_generated
    coverage_score: float = 0.0
    validation_status: str
    validation_details: Dict[str, Any] = {}
    citations: List[Dict[str, Any]] = []
    affected_files: List[str] = []
    impact_reason: Optional[str] = None
    last_generated_at: Optional[datetime.datetime] = None
    is_ai_generated: bool = False
    source_file: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentationGapResponse(BaseModel):
    id: str
    repository_id: str
    title: str
    description: str
    file_path: Optional[str] = None
    gap_type: str
    severity: str
    status: str
    suggested_doc_type: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentationGenerateRequest(BaseModel):
    doc_type: str
    custom_instructions: Optional[str] = None

class DocumentationUpdateRequest(BaseModel):
    content: str
    change_summary: Optional[str] = "Manual user revision"

class DocumentationAIActionRequest(BaseModel):
    action: str # summarize | expand | simplify | find_inconsistencies | explain_section | update_from_code
    selected_text: Optional[str] = None
    instruction: Optional[str] = None

class DocumentationAIActionResponse(BaseModel):
    action: str
    result: str
    explanation: str

class DocumentationDashboardResponse(BaseModel):
    repository_name: str
    default_branch: str
    last_analyzed: Optional[str] = None
    files_analyzed: int
    modules_count: int
    coverage_score: float
    total_documents: int
    up_to_date_count: int
    outdated_count: int
    update_recommended_count: int
    not_generated_count: int
    gaps_count: int
    recent_activity: List[Dict[str, Any]] = []

class DocumentationCoverageResponse(BaseModel):
    coverage_percentage: float
    total_modules: int
    documented_modules: List[str]
    undocumented_modules: List[str]
    total_endpoints: int
    documented_endpoints: List[str]
    undocumented_endpoints: List[str]
    outdated_documents: List[str]
    missing_config_docs: List[str]

class DocumentationValidationResponse(BaseModel):
    status: str
    passed: bool
    verified_claims: int
    verified_files: int
    verified_apis: int
    outdated_references: int
    unsupported_claims: int
    claims: List[Dict[str, Any]]
    warnings: List[str]
    corrected_content: Optional[str] = None

class ChangeImpactSyncRequest(BaseModel):
    changed_files: Optional[List[str]] = None

class ChangeImpactSyncResponse(BaseModel):
    affected_documents_count: int
    affected_documents: List[Dict[str, Any]]
    summary: str

class DocumentationSearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[Dict[str, Any]]
