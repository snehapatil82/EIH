export interface CodeChange {
  id: string;
  task_id: string;
  file_path: string;
  change_type: 'modify' | 'add' | 'delete';
  original_content?: string;
  modified_content: string;
  diff: string;
  explanation?: string;
  applied: boolean;
  created_at: string;
}

export interface ValidationResult {
  id: string;
  task_id: string;
  iteration: number;
  status: 'passed' | 'failed' | 'warning';
  syntax_passed: boolean;
  imports_passed: boolean;
  tests_passed: boolean;
  requirements_passed: boolean;
  details: {
    syntax_errors?: string[];
    test_output?: string;
    files_validated?: string[];
  };
  error_summary?: string;
  created_at: string;
}

export interface ReviewComment {
  file: string;
  severity: 'info' | 'low' | 'medium' | 'high';
  message: string;
}

export interface ReviewResult {
  id: string;
  task_id: string;
  status: 'approved' | 'changes_requested';
  quality_score: number;
  security_score: number;
  maintainability_score: number;
  comments: ReviewComment[];
  summary?: string;
  created_at: string;
}

export interface Diagram {
  diagram_type: string;
  mermaid_code: string;
  description: string;
}

export interface TaskDiagram {
  id: string;
  task_id: string;
  diagram_type: string;
  mermaid_code: string;
  description?: string;
  created_at: string;
}


export interface BenchmarkData {
  summary: {
    total_tasks_evaluated: number;
    single_agent_count: number;
    multi_agent_count: number;
  };
  single_agent_metrics: {
    avg_latency_seconds: number;
    avg_retry_count: number;
    validation_pass_rate: number;
    avg_quality_score: number;
    avg_security_score: number;
    suitability: string;
  };
  multi_agent_metrics: {
    avg_latency_seconds: number;
    avg_retry_count: number;
    validation_pass_rate: number;
    avg_quality_score: number;
    avg_security_score: number;
    suitability: string;
  };
  comparison_matrix: Array<{
    dimension: string;
    single_agent: string;
    multi_agent: string;
  }>;
}
