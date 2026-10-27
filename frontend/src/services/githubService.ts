import { apiClient } from './api';
import {
  GitHubStatus,
  GitHubDiffResult,
  BranchListResult,
  PublishRequest,
  PublishResult,
} from '../types/github';

export const githubService = {
  async getStatus(taskId: string): Promise<GitHubStatus> {
    const res = await apiClient.get<GitHubStatus>(`/tasks/${taskId}/github/status`);
    return res.data;
  },

  async getDiff(taskId: string): Promise<GitHubDiffResult> {
    const res = await apiClient.get<GitHubDiffResult>(`/tasks/${taskId}/github/diff`);
    return res.data;
  },

  async listBranches(taskId: string): Promise<BranchListResult> {
    const res = await apiClient.get<BranchListResult>(`/tasks/${taskId}/github/branches`);
    return res.data;
  },

  async publish(taskId: string, req: PublishRequest): Promise<PublishResult> {
    const res = await apiClient.post<PublishResult>(`/tasks/${taskId}/github/publish`, req);
    return res.data;
  },
};
