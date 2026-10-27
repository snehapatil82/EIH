import { apiClient } from './api';
import {
  DocumentationDashboard,
  DocumentationItem,
  DocumentationCoverage,
  DocumentationGap,
  DocumentationVersion,
  DocumentationValidationResult,
  DocumentationAIActionResult,
  DocumentationSearchResponse,
  ChangeImpactSyncResponse
} from '../types/documentation';

export const documentationService = {
  async getDashboard(repositoryId: string): Promise<DocumentationDashboard> {
    const res = await apiClient.get<DocumentationDashboard>(`/repositories/${repositoryId}/documentation/dashboard`);
    return res.data;
  },

  async list(repositoryId: string): Promise<DocumentationItem[]> {
    const res = await apiClient.get<DocumentationItem[]>(`/repositories/${repositoryId}/documentation`);
    return res.data;
  },

  async getCoverage(repositoryId: string): Promise<DocumentationCoverage> {
    const res = await apiClient.get<DocumentationCoverage>(`/repositories/${repositoryId}/documentation/coverage`);
    return res.data;
  },

  async getGaps(repositoryId: string): Promise<DocumentationGap[]> {
    const res = await apiClient.get<DocumentationGap[]>(`/repositories/${repositoryId}/documentation/gaps`);
    return res.data;
  },

  async scanGaps(repositoryId: string): Promise<DocumentationGap[]> {
    const res = await apiClient.post<DocumentationGap[]>(`/repositories/${repositoryId}/documentation/gaps/scan`);
    return res.data;
  },

  async resolveGap(repositoryId: string, gapId: string): Promise<DocumentationItem> {
    const res = await apiClient.post<DocumentationItem>(
      `/repositories/${repositoryId}/documentation/gaps/${gapId}/resolve`
    );
    return res.data;
  },

  async getByType(repositoryId: string, docType: string): Promise<DocumentationItem> {
    const res = await apiClient.get<DocumentationItem>(`/repositories/${repositoryId}/documentation/item/${docType}`);
    return res.data;
  },

  async generate(
    repositoryId: string,
    docType: string,
    customInstructions?: string
  ): Promise<DocumentationItem> {
    const res = await apiClient.post<DocumentationItem>(`/repositories/${repositoryId}/documentation/generate`, {
      doc_type: docType,
      custom_instructions: customInstructions,
    });
    return res.data;
  },

  async update(
    repositoryId: string,
    docId: string,
    content: string,
    changeSummary?: string
  ): Promise<DocumentationItem> {
    const res = await apiClient.put<DocumentationItem>(`/repositories/${repositoryId}/documentation/${docId}`, {
      content,
      change_summary: changeSummary,
    });
    return res.data;
  },

  async validate(repositoryId: string, docId: string): Promise<DocumentationValidationResult> {
    const res = await apiClient.post<DocumentationValidationResult>(
      `/repositories/${repositoryId}/documentation/${docId}/validate`
    );
    return res.data;
  },

  async regenerate(repositoryId: string, docId: string): Promise<DocumentationItem> {
    const res = await apiClient.post<DocumentationItem>(
      `/repositories/${repositoryId}/documentation/${docId}/regenerate`
    );
    return res.data;
  },

  async getVersions(repositoryId: string, docId: string): Promise<DocumentationVersion[]> {
    const res = await apiClient.get<DocumentationVersion[]>(
      `/repositories/${repositoryId}/documentation/${docId}/versions`
    );
    return res.data;
  },

  async revertVersion(
    repositoryId: string,
    docId: string,
    versionId: string
  ): Promise<DocumentationItem> {
    const res = await apiClient.post<DocumentationItem>(
      `/repositories/${repositoryId}/documentation/${docId}/revert/${versionId}`
    );
    return res.data;
  },

  async executeAIAction(
    repositoryId: string,
    docId: string,
    action: string,
    selectedText?: string,
    instruction?: string
  ): Promise<DocumentationAIActionResult> {
    const res = await apiClient.post<DocumentationAIActionResult>(
      `/repositories/${repositoryId}/documentation/${docId}/ai-action`,
      {
        action,
        selected_text: selectedText,
        instruction,
      }
    );
    return res.data;
  },

  async search(repositoryId: string, query: string): Promise<DocumentationSearchResponse> {
    const res = await apiClient.post<DocumentationSearchResponse>(
      `/repositories/${repositoryId}/documentation/search?query=${encodeURIComponent(query)}`
    );
    return res.data;
  },

  async syncChangeImpact(
    repositoryId: string,
    changedFiles?: string[]
  ): Promise<ChangeImpactSyncResponse> {
    const res = await apiClient.post<ChangeImpactSyncResponse>(
      `/repositories/${repositoryId}/documentation/sync-impact`,
      { changed_files: changedFiles }
    );
    return res.data;
  },
};
