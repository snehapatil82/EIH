export interface TerminalInfo {
  task_id: string;
  workspace_path: string;
  project_type: string;
  manifests: string[];
  allowed_commands: string[];
  suggested_commands: Array<{ label: string; cmd: string }>;
}

export interface TerminalOutputChunk {
  type: 'stdout' | 'stderr' | 'system' | 'error';
  line: string;
  elapsed: number;
  exit_code?: number;
  timed_out?: boolean;
}

export interface TerminalHistoryEntry {
  id: string;
  command: string;
  exit_code: number | null;
  stdout: string | null;
  stderr: string | null;
  duration_seconds: number | null;
  timed_out: boolean;
  created_at: string;
}

export interface RunCommandResult {
  session_id: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_seconds: number;
  timed_out: boolean;
  success: boolean;
}
