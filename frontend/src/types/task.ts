export interface TaskStep {
  id: string;
  order: number;
  agent_name: string;
  title: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  output?: Record<string, any>;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface AgentLog {
  id: string;
  agent_name: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'ACTION';
  message: string;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface EngineeringTask {
  id: string;
  repository_id: string;
  title: string;
  requirement: string;
  status: 'pending' | 'planning' | 'running' | 'waiting_approval' | 'approved' | 'rejected' | 'failed' | 'completed';
  complexity: 'SIMPLE' | 'MEDIUM' | 'COMPLEX';
  workflow_type: 'single_agent' | 'multi_agent';
  active_agent?: string;
  retry_count: number;
  max_retries: number;
  branch_name?: string;
  summary?: string;
  created_at: string;
  updated_at: string;
  steps: TaskStep[];
  logs: AgentLog[];
}
