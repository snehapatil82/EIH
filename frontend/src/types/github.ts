export interface GitHubStatus {
  task_id: string;
  repository_name: string;
  repository_owner: string;
  remote_url: string;
  current_branch: string;
  default_branch: string;
  head_commit_sha: string | null;
  suggested_branch: string;
  changed_files_count: number;
  token_configured: boolean;
}

export interface GitHubFileDiff {
  file_path: string;
  change_type: 'modify' | 'add' | 'delete';
  diff: string;
  explanation?: string;
  applied: boolean;
}

export interface GitHubDiffResult {
  task_id: string;
  total_changed_files: number;
  changes: GitHubFileDiff[];
}

export interface PublishRequest {
  branch_name: string;
  commit_message: string;
  confirmed: boolean;
  create_pr: boolean;
  pr_title?: string;
  pr_body?: string;
}

export interface PublishResult {
  status: string;
  task_id: string;
  branch: string;
  commit_sha: string;
  commit_url: string | null;
  files_pushed: number;
  pr_url: string | null;
}

export interface BranchListResult {
  repository: string;
  branches: string[];
}
