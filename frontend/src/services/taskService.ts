import { apiClient } from './api';
import { EngineeringTask } from '../types/task';
import { CodeChange, ValidationResult, ReviewResult, TaskDiagram } from '../types/changes';

export const taskService = {
  async create(repoId: string, requirement: string, workflowPreference: string = 'auto'): Promise<EngineeringTask> {
    const res = await apiClient.post<EngineeringTask>(`/repositories/${repoId}/tasks`, {
      requirement,
      workflow_preference: workflowPreference,
    });
    return res.data;
  },

  async get(taskId: string): Promise<EngineeringTask> {
    const res = await apiClient.get<EngineeringTask>(`/tasks/${taskId}`);
    return res.data;
  },

  async listForRepo(repoId: string): Promise<EngineeringTask[]> {
    const res = await apiClient.get<EngineeringTask[]>(`/repositories/${repoId}/tasks`);
    return res.data;
  },

  async getChanges(taskId: string): Promise<CodeChange[]> {
    const res = await apiClient.get<CodeChange[]>(`/tasks/${taskId}/changes`);
    return res.data;
  },

  async getValidation(taskId: string): Promise<ValidationResult[]> {
    const res = await apiClient.get<ValidationResult[]>(`/tasks/${taskId}/validation`);
    return res.data;
  },

  async getReview(taskId: string): Promise<ReviewResult[]> {
    const res = await apiClient.get<ReviewResult[]>(`/tasks/${taskId}/review`);
    return res.data;
  },

  async getDiagrams(taskId: string): Promise<TaskDiagram[]> {
    const res = await apiClient.get<TaskDiagram[]>(`/tasks/${taskId}/diagrams`);
    return res.data;
  },

  async approve(taskId: string): Promise<{ status: string; files_applied: number }> {
    const res = await apiClient.post(`/tasks/${taskId}/approve`);
    return res.data;
  },

  async reject(taskId: string): Promise<{ status: string }> {
    const res = await apiClient.post(`/tasks/${taskId}/reject`);
    return res.data;
  },

  async revise(taskId: string, feedback: string): Promise<{ status: string }> {
    const res = await apiClient.post(`/tasks/${taskId}/revise`, { feedback });
    return res.data;
  },

  streamTask(
    taskId: string,
    onUpdate: (data: any) => void,
    onComplete: (status: string) => void,
    onError: (error: any) => void
  ): () => void {
    const eventSource = new EventSource(`/api/v1/tasks/${taskId}/stream`);

    eventSource.addEventListener('update', (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (err) {
        console.error('Failed to parse SSE update data:', err);
      }
    });

    eventSource.addEventListener('complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        onComplete(data.status);
      } catch (err) {
        onComplete('completed');
      }
      eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
      onError(event);
      eventSource.close();
    });

    return () => {
      eventSource.close();
    };
  },
};

