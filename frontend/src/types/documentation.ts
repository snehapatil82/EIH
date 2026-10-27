export interface CitationItem {
  file_path: string;
  start_line?: number;
  end_line?: number;
  snippet?: string;
  claim?: string;
  score?: number;
}

export interface ValidationClaim {
  type: string;
  reference: string;
  exists: boolean;
  details?: string;
  line_number?: number;
}

export interface ValidationDetails {
  verified_claims: number;
  verified_files: number;
  verified_apis: number;
  outdated_references: number;
  unsupported_claims: number;
  claims: ValidationClaim[];
  warnings: string[];
  auto_corrected?: boolean;
}

export type DocStatus = 'up_to_date' | 'update_recommended' | 'outdated' | 'not_generated';
export type DocValidationStatus = 'passed' | 'warning' | 'failed' | 'unvalidated';

export interface DocumentationItem {
  id: string;
  repository_id: string;
  doc_type: string;
  title: string;
  category: 'project' | 'technical';
  description?: string;
  content: string;
  status: DocStatus;
  coverage_score: number;
  validation_status: DocValidationStatus;
  validation_details: ValidationDetails;
  citations: CitationItem[];
  affected_files: string[];
  impact_reason?: string | null;
  last_generated_at?: string | null;
  is_ai_generated?: boolean;
  source_file?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentationVersion {
  id: string;
  documentation_id: string;
  version_tag: string;
  content: string;
  change_summary?: string;
  validation_status: string;
  created_at: string;
}

export interface DocumentationGap {
  id: string;
  repository_id: string;
  title: string;
  description: string;
  file_path?: string;
  gap_type: string;
  severity: 'high' | 'medium' | 'low';
  status: 'open' | 'resolved';
  suggested_doc_type?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentationDashboard {
  repository_name: string;
  default_branch: string;
  last_analyzed?: string | null;
  files_analyzed: number;
  modules_count: number;
  coverage_score: number;
  total_documents: number;
  up_to_date_count: number;
  outdated_count: number;
  update_recommended_count: number;
  not_generated_count: number;
  gaps_count: number;
  recent_activity: Array<{
    id: string;
    doc_type: string;
    title: string;
    action: string;
    status: DocStatus;
    validation_status: DocValidationStatus;
    timestamp: string;
  }>;
}

export interface DocumentationCoverage {
  coverage_percentage: number;
  total_modules: number;
  documented_modules: string[];
  undocumented_modules: string[];
  total_endpoints: number;
  documented_endpoints: string[];
  undocumented_endpoints: string[];
  outdated_documents: string[];
  missing_config_docs: string[];
}

export interface DocumentationValidationResult {
  status: DocValidationStatus;
  passed: boolean;
  verified_claims: number;
  verified_files: number;
  verified_apis: number;
  outdated_references: number;
  unsupported_claims: number;
  claims: ValidationClaim[];
  warnings: string[];
  corrected_content?: string;
}

export interface DocumentationAIActionResult {
  action: string;
  result: string;
  explanation: string;
}

export interface DocumentationSearchMatch {
  document_id: string;
  doc_type: string;
  title: string;
  category: string;
  status: DocStatus;
  score: number;
  snippet: string;
}

export interface DocumentationSearchResponse {
  query: string;
  total_matches: number;
  results: DocumentationSearchMatch[];
}

export interface ChangeImpactSyncResponse {
  affected_documents_count: number;
  affected_documents: Array<{
    id: string;
    doc_type: string;
    title: string;
    reasons: string[];
    affected_files: string[];
  }>;
  summary: string;
}
