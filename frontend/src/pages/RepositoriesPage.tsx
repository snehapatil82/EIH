import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  Plus,
  RefreshCw,
  ExternalLink,
  GitBranch,
  Layers,
  ArrowRight,
  Sparkles,
  FolderTree,
  FileCode,
  Package,
  Code2,
  Cpu,
  LayoutDashboard,
  MessageSquareCode,
  Bot,
} from 'lucide-react';
import {
  Repository,
  RepositoryOverview,
  FileTreeItem,
  FileContent,
  Dependency,
  CodeEntity,
  Framework,
} from '../types/repository';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Spinner } from '../components/common/Spinner';
import { RepoConnectorModal } from '../components/repository/RepoConnectorModal';
import { RepoOverviewDashboard } from '../components/repository/RepoOverviewDashboard';
import { RepositoryStructureView } from '../components/repository/RepositoryStructureView';
import { FileTreeView } from '../components/repository/FileTreeView';
import { CodeViewer } from '../components/repository/CodeViewer';
import { DependencyInspector } from '../components/repository/DependencyInspector';
import { FrameworkInspector } from '../components/repository/FrameworkInspector';
import { LanguageBreakdown } from '../components/repository/LanguageBreakdown';
import { SymbolInspector } from '../components/repository/SymbolInspector';
import { repositoryService } from '../services/repositoryService';

interface RepositoriesPageProps {
  repositories: Repository[];
  selectedRepo: Repository | null;
  onSelectRepo: (repo: Repository) => void;
  onConnectRepo: (url: string, branch?: string) => Promise<void>;
  isLoading: boolean;
  onRefresh: () => Promise<void>;
}

type TabType = 'overview' | 'structure' | 'files' | 'dependencies' | 'languages' | 'frameworks' | 'symbols';

export const RepositoriesPage: React.FC<RepositoriesPageProps> = ({
  repositories,
  selectedRepo,
  onSelectRepo,
  onConnectRepo,
  isLoading,
  onRefresh,
}) => {
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reindexingId, setReindexingId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Selected Repository Intelligence Data
  const [overview, setOverview] = useState<RepositoryOverview | null>(null);
  const [treeItems, setTreeItems] = useState<FileTreeItem[]>([]);
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [entities, setEntities] = useState<CodeEntity[]>([]);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [isLoadingFile, setIsLoadingFile] = useState(false);

  useEffect(() => {
    if (!selectedRepo) {
      setOverview(null);
      setTreeItems([]);
      setDependencies([]);
      setEntities([]);
      setFrameworks([]);
      setSelectedFilePath(null);
      setFileContent(null);
      return;
    }

    const loadRepoDetails = async () => {
      setIsLoadingDetails(true);
      try {
        const [overviewRes, treeRes, depsRes, entsRes, fwsRes] = await Promise.allSettled([
          repositoryService.getOverview(selectedRepo.id),
          repositoryService.getFileTree(selectedRepo.id),
          repositoryService.getDependencies(selectedRepo.id),
          repositoryService.getEntities(selectedRepo.id),
          repositoryService.getFrameworks(selectedRepo.id),
        ]);

        if (overviewRes.status === 'fulfilled') setOverview(overviewRes.value);
        if (treeRes.status === 'fulfilled') setTreeItems(treeRes.value);
        if (depsRes.status === 'fulfilled') setDependencies(depsRes.value);
        if (entsRes.status === 'fulfilled') setEntities(entsRes.value);
        if (fwsRes.status === 'fulfilled') setFrameworks(fwsRes.value);
      } catch (err) {
        console.error('Failed to load repo details:', err);
      } finally {
        setIsLoadingDetails(false);
      }
    };

    loadRepoDetails();
  }, [selectedRepo]);

  const handleSelectFile = async (path: string) => {
    if (!selectedRepo) return;
    setSelectedFilePath(path);
    setActiveTab('files');
    setIsLoadingFile(true);
    try {
      const content = await repositoryService.getFileContent(selectedRepo.id, path);
      setFileContent(content);
    } catch (err) {
      console.error('Failed to fetch file content:', err);
      setFileContent(null);
    } finally {
      setIsLoadingFile(false);
    }
  };

  const handleReindex = async (repoId: string) => {
    setReindexingId(repoId);
    try {
      await repositoryService.reindex(repoId);
      await onRefresh();
    } catch (err) {
      console.error('Reindexing failed:', err);
    } finally {
      setReindexingId(null);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-cyan-400" />
            Repository Intelligence & Management
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Connect, inspect repository structure, files, dependencies, programming languages, frameworks, and AST code symbols.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
            onClick={onRefresh}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setIsModalOpen(true)}
          >
            Connect Repository
          </Button>
        </div>
      </div>

      {/* Connected Repositories Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Connected Repositories ({repositories.length})
          </div>
          <span className="text-[11px] text-slate-500">
            Click any repository row to inspect its full architecture and dependencies below
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Repository</th>
                <th className="py-3 px-4">Default Branch</th>
                <th className="py-3 px-4">Files & Lines</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Languages</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {repositories.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No repositories connected yet. Click "Connect Repository" to begin.
                  </td>
                </tr>
              ) : (
                repositories.map((repo) => {
                  const isSelected = selectedRepo?.id === repo.id;
                  const isReindexing = reindexingId === repo.id;

                  return (
                    <tr
                      key={repo.id}
                      onClick={() => onSelectRepo(repo)}
                      className={`hover:bg-slate-850 cursor-pointer transition-colors ${
                        isSelected ? 'bg-cyan-950/40 border-l-2 border-l-cyan-400' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-semibold text-slate-100">
                        <div className="flex items-center gap-2.5">
                          <FolderGit2 className={`w-4 h-4 ${isSelected ? 'text-cyan-400' : 'text-slate-400'} flex-shrink-0`} />
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="hover:text-cyan-300">{repo.owner}/{repo.name}</span>
                              {isSelected && <Badge variant="cyan" size="sm">ACTIVE SELECTION</Badge>}
                            </div>
                            <span className="text-[11px] text-slate-500 font-normal font-mono">
                              {repo.url}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4 font-mono text-slate-300">
                        <div className="flex items-center gap-1.5">
                          <GitBranch className="w-3.5 h-3.5 text-slate-500" />
                          <span>{repo.default_branch}</span>
                        </div>
                      </td>

                      <td className="py-3 px-4 font-mono text-slate-300">
                        <div>{repo.total_files} files</div>
                        <div className="text-[11px] text-slate-500">{repo.total_lines?.toLocaleString()} lines</div>
                      </td>

                      <td className="py-3 px-4">
                        <Badge variant={repo.status === 'indexed' ? 'success' : 'info'} size="sm">
                          {repo.status.toUpperCase()}
                        </Badge>
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {Object.entries(repo.languages || {}).slice(0, 3).map(([lang]) => (
                            <span key={lang} className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">
                              {lang}
                            </span>
                          ))}
                        </div>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="outline"
                            size="sm"
                            isLoading={isReindexing}
                            onClick={() => handleReindex(repo.id)}
                          >
                            Re-index
                          </Button>

                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                              onSelectRepo(repo);
                              navigate('/explorer');
                            }}
                            rightIcon={<ArrowRight className="w-3 h-3" />}
                          >
                            Explore
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Repository Comprehensive Intelligence Section */}
      {selectedRepo && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-2xl">
          {/* Active Repo Top Bar with Navigation Tabs */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-cyan-950 border border-cyan-800 rounded-xl text-cyan-400">
                <FolderGit2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-100">
                    {selectedRepo.owner}/{selectedRepo.name}
                  </h3>
                  <Badge variant="cyan">Selected Repository</Badge>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400 font-mono mt-0.5">
                  <span>Branch: <strong>{selectedRepo.default_branch}</strong></span>
                  <span>•</span>
                  <span>{selectedRepo.total_files} Files</span>
                  <span>•</span>
                  <span>{selectedRepo.total_lines?.toLocaleString()} LOC</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2 flex-wrap">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<MessageSquareCode className="w-3.5 h-3.5 text-blue-400" />}
                onClick={() => navigate('/chat')}
              >
                Chat RAG
              </Button>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Bot className="w-3.5 h-3.5 text-emerald-400" />}
                onClick={() => navigate('/tasks')}
              >
                Autonomous Tasks
              </Button>
              <Button
                variant="primary"
                size="sm"
                leftIcon={<FolderTree className="w-3.5 h-3.5" />}
                onClick={() => navigate('/explorer')}
              >
                Full Code Explorer
              </Button>
            </div>
          </div>

          {/* Dimension Selector Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none border-b border-slate-800">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'overview'
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <LayoutDashboard className="w-4 h-4 text-cyan-400" />
              <span>Overview</span>
            </button>

            <button
              onClick={() => setActiveTab('structure')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'structure'
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <FolderTree className="w-4 h-4 text-amber-400" />
              <span>Repository Structure</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono rounded bg-slate-800 text-slate-300">
                {overview?.root_directories?.length || 0}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('files')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'files'
                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <FileCode className="w-4 h-4 text-blue-400" />
              <span>Files ({selectedRepo.total_files})</span>
            </button>

            <button
              onClick={() => setActiveTab('dependencies')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'dependencies'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Package className="w-4 h-4 text-emerald-400" />
              <span>Dependencies</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono rounded bg-slate-800 text-slate-300">
                {dependencies.length || overview?.dependencies_count || 0}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('languages')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'languages'
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Code2 className="w-4 h-4 text-cyan-400" />
              <span>Programming Languages</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono rounded bg-slate-800 text-slate-300">
                {Object.keys(overview?.languages || selectedRepo.languages || {}).length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('frameworks')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'frameworks'
                  ? 'bg-pink-500/10 text-pink-400 border border-pink-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Sparkles className="w-4 h-4 text-pink-400" />
              <span>Frameworks & Libraries</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono rounded bg-slate-800 text-slate-300">
                {frameworks.length || overview?.frameworks?.length || 0}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('symbols')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === 'symbols'
                  ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Cpu className="w-4 h-4 text-purple-400" />
              <span>AST Symbols</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono rounded bg-slate-800 text-slate-300">
                {entities.length || overview?.entities_count || 0}
              </span>
            </button>
          </div>

          {/* Active Tab View Content */}
          <div>
            {isLoadingDetails ? (
              <div className="py-16 flex flex-col items-center justify-center">
                <Spinner size="lg" />
                <span className="text-xs text-slate-400 mt-3">Loading repository intelligence data...</span>
              </div>
            ) : (
              <>
                {/* 1. OVERVIEW */}
                {activeTab === 'overview' && (
                  <RepoOverviewDashboard
                    overview={overview}
                    onSelectFile={handleSelectFile}
                    onSelectTab={(tab) => setActiveTab(tab as TabType)}
                  />
                )}

                {/* 2. REPOSITORY STRUCTURE */}
                {activeTab === 'structure' && (
                  <RepositoryStructureView
                    rootDirectories={overview?.root_directories || []}
                    treeItems={treeItems}
                    totalFiles={selectedRepo.total_files}
                    totalLines={selectedRepo.total_lines}
                    onSelectFile={handleSelectFile}
                  />
                )}

                {/* 3. FILES & SOURCE CODE */}
                {activeTab === 'files' && (
                  <div className="grid grid-cols-12 gap-4 min-h-[500px]">
                    <div className="col-span-12 md:col-span-4 bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex flex-col overflow-hidden max-h-[550px]">
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-300 pb-2 mb-2 border-b border-slate-800 flex items-center gap-2">
                        <FolderTree className="w-4 h-4 text-cyan-400" />
                        <span>Repository Tree</span>
                      </div>
                      <div className="flex-1 overflow-y-auto">
                        <FileTreeView
                          items={treeItems}
                          selectedFilePath={selectedFilePath}
                          onSelectFile={handleSelectFile}
                        />
                      </div>
                    </div>

                    <div className="col-span-12 md:col-span-8 flex flex-col min-h-[500px]">
                      {isLoadingFile ? (
                        <div className="h-full flex items-center justify-center bg-slate-950 rounded-xl border border-slate-800">
                          <Spinner size="lg" />
                        </div>
                      ) : selectedFilePath && fileContent ? (
                        <div className="h-full flex flex-col space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-400 px-2 font-mono">
                            <span>{fileContent.path}</span>
                            <span>{fileContent.line_count} lines • {fileContent.language}</span>
                          </div>
                          <div className="flex-1 min-h-[460px]">
                            <CodeViewer file={fileContent} />
                          </div>
                        </div>
                      ) : (
                        <div className="h-full flex flex-col items-center justify-center p-12 bg-slate-950/40 rounded-xl border border-dashed border-slate-800 text-center text-slate-400">
                          <FileCode className="w-12 h-12 text-slate-600 mb-3" />
                          <h4 className="text-sm font-semibold text-slate-200">No file selected</h4>
                          <p className="text-xs text-slate-500 mt-1 max-w-sm">
                            Select any file from the repository tree on the left to inspect its syntax-highlighted code.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 4. DEPENDENCIES */}
                {activeTab === 'dependencies' && (
                  <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5">
                    <DependencyInspector
                      dependencies={dependencies.length > 0 ? dependencies : (overview?.dependencies || [])}
                      onOpenSourceFile={handleSelectFile}
                    />
                  </div>
                )}

                {/* 5. PROGRAMMING LANGUAGES */}
                {activeTab === 'languages' && (
                  <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 max-w-3xl">
                    <LanguageBreakdown
                      languages={overview?.languages || selectedRepo.languages || {}}
                      languagePercentages={overview?.language_percentages}
                    />
                  </div>
                )}

                {/* 6. FRAMEWORKS & LIBRARIES */}
                {activeTab === 'frameworks' && (
                  <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5">
                    <FrameworkInspector
                      frameworks={frameworks.length > 0 ? frameworks : (overview?.frameworks || [])}
                    />
                  </div>
                )}

                {/* 7. AST SYMBOLS */}
                {activeTab === 'symbols' && (
                  <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5">
                    <SymbolInspector
                      entities={entities}
                      onSelectSymbol={(sym) => handleSelectFile(sym.file_path)}
                    />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      <RepoConnectorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConnect={onConnectRepo}
        isLoading={isLoading}
      />
    </div>
  );
};
