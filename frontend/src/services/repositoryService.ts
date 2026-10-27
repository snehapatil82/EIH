import { apiClient } from './api';
import { Repository, FileTreeItem, FileContent, CodeEntity, Dependency } from '../types/repository';

export const repositoryService = {
  async list(): Promise<Repository[]> {
    const res = await apiClient.get<Repository[]>('/repositories');
    return res.data;
  },

  async get(id: string): Promise<Repository> {
    const res = await apiClient.get<Repository>(`/repositories/${id}`);
    return res.data;
  },

  async connect(url: string, branch?: string): Promise<Repository> {
    const res = await apiClient.post<Repository>('/repositories', { url, branch });
    return res.data;
  },

  async getFileTree(repoId: string): Promise<FileTreeItem[]> {
    const res = await apiClient.get<FileTreeItem[]>(`/repositories/${repoId}/files/tree`);
    return res.data;
  },

  async getFileContent(repoId: string, path: string): Promise<FileContent> {
    const res = await apiClient.get<FileContent>(`/repositories/${repoId}/file-content`, {
      params: { path },
    });
    return res.data;
  },

  async getEntities(repoId: string): Promise<CodeEntity[]> {
    const res = await apiClient.get<CodeEntity[]>(`/repositories/${repoId}/entities`);
    return res.data;
  },

  async getDependencies(repoId: string): Promise<Dependency[]> {
    const res = await apiClient.get<Dependency[]>(`/repositories/${repoId}/dependencies`);
    return res.data;
  },

  async getArchitecture(
    repoId: string,
    viewMode: import('../types/repository').DiagramViewMode = 'code',
    workflowDescription?: string
  ): Promise<import('../types/repository').DiagramResponse> {
    const res = await apiClient.get<import('../types/repository').DiagramResponse>(`/repositories/${repoId}/architecture`, {
      params: { view_mode: viewMode, workflow_description: workflowDescription || undefined },
    });
    return res.data;
  },

  async getDiagram(
    repoId: string,
    type: import('../types/repository').DiagramType,
    viewMode: import('../types/repository').DiagramViewMode = 'code',
    workflowDescription?: string
  ): Promise<import('../types/repository').DiagramResponse> {
    const endpoint =
      type === 'architecture'
        ? `/repositories/${repoId}/architecture`
        : `/repositories/${repoId}/diagrams/${type}`;
    const res = await apiClient.get<import('../types/repository').DiagramResponse>(endpoint, {
      params: { view_mode: viewMode, workflow_description: workflowDescription || undefined },
    });
    return res.data;
  },

  async getOverview(repoId: string): Promise<import('../types/repository').RepositoryOverview> {
    const res = await apiClient.get<import('../types/repository').RepositoryOverview>(`/repositories/${repoId}/overview`);
    return res.data;
  },

  async getFrameworks(repoId: string): Promise<import('../types/repository').Framework[]> {
    const res = await apiClient.get<import('../types/repository').Framework[]>(`/repositories/${repoId}/frameworks`);
    return res.data;
  },

  async reindex(repoId: string): Promise<{ status: string; indexed_chunks: number }> {
    const res = await apiClient.post(`/repositories/${repoId}/index`);
    return res.data;
  },

  async getCallGraphFunctions(
    repoId: string,
    search?: string,
    filePath?: string
  ): Promise<import('../types/repository').CallGraphFunctionSummary[]> {
    const res = await apiClient.get<import('../types/repository').CallGraphFunctionSummary[]>(
      `/repositories/${repoId}/call-graph/functions`,
      { params: { search: search || undefined, file_path: filePath || undefined } }
    );
    return res.data;
  },

  async getCallGraph(
    repoId: string,
    functionId?: string,
    mode: 'calls_from' | 'called_by' | 'full' = 'calls_from',
    depth: number = 2
  ): Promise<import('../types/repository').CallGraphResponse> {
    const res = await apiClient.get<import('../types/repository').CallGraphResponse>(
      `/repositories/${repoId}/call-graph`,
      { params: { function_id: functionId || undefined, mode, depth } }
    );
    return res.data;
  },

  async getFunctionDetails(
    repoId: string,
    functionId: string
  ): Promise<import('../types/repository').CallGraphNodeItem> {
    const res = await apiClient.get<import('../types/repository').CallGraphNodeItem>(
      `/repositories/${repoId}/call-graph/functions/${encodeURIComponent(functionId)}`
    );
    return res.data;
  },

  async getFunctionCallers(
    repoId: string,
    functionId: string
  ): Promise<import('../types/repository').CallGraphEdgeItem[]> {
    const res = await apiClient.get<import('../types/repository').CallGraphEdgeItem[]>(
      `/repositories/${repoId}/call-graph/functions/${encodeURIComponent(functionId)}/callers`
    );
    return res.data;
  },

  async getFunctionCalls(
    repoId: string,
    functionId: string
  ): Promise<import('../types/repository').CallGraphEdgeItem[]> {
    const res = await apiClient.get<import('../types/repository').CallGraphEdgeItem[]>(
      `/repositories/${repoId}/call-graph/functions/${encodeURIComponent(functionId)}/calls`
    );
    return res.data;
  },

  async refreshCallGraph(
    repoId: string
  ): Promise<{ status: string; repository_id: string; function_count: number }> {
    const res = await apiClient.post<{ status: string; repository_id: string; function_count: number }>(
      `/repositories/${repoId}/call-graph/refresh`
    );
    return res.data;
  },
};
