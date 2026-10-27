export interface Repository {
  id: string;
  name: string;
  owner: string;
  url: string;
  default_branch: string;
  status: 'pending' | 'cloned' | 'indexed' | 'error';
  languages: Record<string, number>;
  total_files: number;
  total_lines: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface FileTreeItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  language?: string;
  children?: FileTreeItem[];
}

export interface FileContent {
  path: string;
  filename: string;
  language?: string;
  size_bytes: number;
  line_count: number;
  content: string;
}

export interface CodeEntity {
  id: string;
  file_path: string;
  name: string;
  entity_type: 'function' | 'class' | 'method' | 'endpoint' | 'module';
  start_line: number;
  end_line: number;
  signature?: string;
  docstring?: string;
  decorators: string[];
  calls: string[];
}

export interface Dependency {
  id: string;
  name: string;
  version?: string;
  ecosystem: string;
  source_file: string;
}

export interface Framework {
  name: string;
  category: string;
  version?: string;
  source: string;
  icon?: string;
  confidence?: string;
}

export interface DirectorySummary {
  name: string;
  path: string;
  file_count: number;
  line_count: number;
  languages: string[];
}

export interface RepositoryOverview {
  repository_id: string;
  name: string;
  owner: string;
  url: string;
  default_branch: string;
  status: string;
  total_files: number;
  total_lines: number;
  total_directories: number;
  languages: Record<string, number>;
  language_percentages: Record<string, number>;
  frameworks: Framework[];
  dependencies_count: number;
  dependencies: Dependency[];
  entities_count: number;
  entity_counts_by_type: Record<string, number>;
  root_directories: DirectorySummary[];
  manifest_files: string[];
  key_entrypoints: string[];
}

export type DiagramViewMode = 'code' | 'workflow';
export type DiagramType = 'architecture' | 'sequence' | 'flowchart' | 'uml' | 'dependency' | 'er' | 'usecase' | 'state' | 'dfd' | 'callflow';

export interface DiagramNodeEvidence {
  id: string;
  label: string;
  evidence_type: string;
  source_file?: string;
  line_range?: string;
  entity_name?: string;
  confidence: 'verified' | 'inferred';
  details?: string;
}

export interface DiagramResponse {
  diagram_type: string;
  view_mode: DiagramViewMode;
  mermaid_code: string;
  description: string;
  summary?: string;
  components_involved?: string[];
  key_relationships?: string[];
  source_references?: string[];
  evidence_status?: 'verified' | 'partial' | 'unverified';
  evidence_limitations?: string;
  nodes_evidence?: DiagramNodeEvidence[];
}

export interface CallGraphFunctionSummary {
  id: string;
  name: string;
  full_name: string;
  file_path: string;
  start_line: number;
  end_line: number;
  enclosing_class?: string | null;
  signature?: string | null;
  caller_count: number;
  callee_count: number;
  is_async: boolean;
}

export interface CallGraphEdgeItem {
  caller_id: string;
  caller_name: string;
  callee_raw_name: string;
  callee_symbol_name: string;
  callee_id?: string | null;
  call_site_line: number;
  lexical_order: number;
  source_file: string;
  target_file?: string | null;
  is_conditional: boolean;
  branch_condition?: string | null;
  is_loop: boolean;
  is_exception: boolean;
  is_async: boolean;
  is_recursive: boolean;
  is_dynamic: boolean;
  is_external: boolean;
  is_resolved: boolean;
}

export interface CallGraphNodeItem {
  id: string;
  name: string;
  full_name: string;
  file_path: string;
  start_line: number;
  end_line: number;
  enclosing_class?: string | null;
  enclosing_module: string;
  parameters: Array<{ name: string; type_annotation?: string; default_value?: string }>;
  is_async: boolean;
  docstring?: string | null;
  decorators: string[];
  language: string;
  caller_count: number;
  callee_count: number;
}

export interface CallGraphResponse {
  repository_id: string;
  root_function_id: string;
  root_function_name: string;
  mode: 'calls_from' | 'called_by' | 'full';
  depth: number;
  mermaid_code: string;
  nodes: CallGraphNodeItem[];
  edges: CallGraphEdgeItem[];
  explanation: {
    summary: string;
    function_name: string;
    full_name: string;
    file_path: string;
    line_range: string;
    parameters: Array<{ name: string; type_annotation?: string; default_value?: string }>;
    docstring?: string;
    outgoing_calls_breakdown: Array<{
      callee: string;
      line: number;
      order: number;
      execution_nature: string;
    }>;
    incoming_callers: Array<{
      caller: string;
      file: string;
      line: number;
      condition: string;
    }>;
    control_flow_narrative: string;
    static_limitations: string;
    components_involved: string[];
    total_nodes: number;
    total_edges: number;
  };
  stats: {
    total_nodes: number;
    total_edges: number;
    external_calls: number;
    conditional_calls: number;
    async_calls: number;
    loop_calls: number;
  };
}


