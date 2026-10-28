import { apiClient, API_BASE_URL } from './api';
import {
  TerminalInfo,
  TerminalHistoryEntry,
  RunCommandResult,
  TerminalOutputChunk,
} from '../types/terminal';

export const terminalService = {
  async getInfo(taskId: string): Promise<TerminalInfo> {
    const res = await apiClient.get<TerminalInfo>(`/tasks/${taskId}/terminal/info`);
    return res.data;
  },

  async run(taskId: string, command: string, timeout?: number): Promise<RunCommandResult> {
    const res = await apiClient.post<RunCommandResult>(`/tasks/${taskId}/terminal/run`, {
      command,
      timeout,
    });
    return res.data;
  },

  async getHistory(taskId: string): Promise<TerminalHistoryEntry[]> {
    const res = await apiClient.get<TerminalHistoryEntry[]>(`/tasks/${taskId}/terminal/history`);
    return res.data;
  },

  /**
   * Stream command output via SSE.
   * Returns a cleanup function to close the EventSource.
   */
  streamCommand(
    taskId: string,
    command: string,
    onOutput: (chunk: TerminalOutputChunk) => void,
    onDone: (sessionId: string) => void,
    onError: (error: string) => void,
  ): () => void {
    const encodedCmd = encodeURIComponent(command);
    const url = `${API_BASE_URL}/tasks/${taskId}/terminal/stream?command=${encodedCmd}`;
    const es = new EventSource(url);

    es.addEventListener('output', (event) => {
      try {
        const data: TerminalOutputChunk = JSON.parse(event.data);
        onOutput(data);
      } catch {
        // ignore parse errors
      }
    });

    es.addEventListener('error', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data || '{}');
        onError(data.line || 'Terminal error');
      } catch {
        onError('Terminal connection error');
      }
      es.close();
    });

    es.addEventListener('done', (event) => {
      try {
        const data = JSON.parse(event.data);
        onDone(data.session_id || '');
      } catch {
        onDone('');
      }
      es.close();
    });

    // Native onerror for connection failures
    es.onerror = () => {
      onError('Terminal stream connection lost');
      es.close();
    };

    return () => es.close();
  },
};
