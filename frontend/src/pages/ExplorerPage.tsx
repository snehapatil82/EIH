import React, { useState, useEffect } from 'react';
import {
  FolderTree,
  FileCode,
  Layers,
  Search,
  Cpu,
  Sparkles,
  Package,
  Code2,
  LayoutDashboard,
  Compass,
  ArrowLeft,
  Server,
  Database,
  CheckCircle2,
  FolderGit2,
  Terminal,
  FileText,
} from 'lucide-react';
import {
  Repository,
  FileTreeItem,
  FileContent,
  CodeEntity,
  Dependency,
  Framework,
  RepositoryOverview,
} from '../types/repository';
import { repositoryService } from '../services/repositoryService';
import { FileTreeView } from '../components/repository/FileTreeView';
import { CodeViewer } from '../components/repository/CodeViewer';
import { SymbolInspector } from '../components/repository/SymbolInspector';
import { DependencyInspector } from '../components/repository/DependencyInspector';
import { FrameworkInspector } from '../components/repository/FrameworkInspector';
import { LanguageBreakdown } from '../components/repository/LanguageBreakdown';
import { RepoOverviewDashboard } from '../components/repository/RepoOverviewDashboard';
import { RepositoryStructureView } from '../components/repository/RepositoryStructureView';
import { Spinner } from '../components/common/Spinner';
import { Badge } from '../components/common/Badge';

interface ExplorerPageProps {
  selectedRepo: Repository | null;
}

type ExplorerTab = 'overview' | 'files' | 'structure' | 'dependencies' | 'languages' | 'frameworks' | 'symbols';
type RightTabType = 'symbols' | 'dependencies' | 'frameworks' | 'languages' | 'structure';

export const ExplorerPage: React.FC<ExplorerPageProps> = ({ selectedRepo }) => {
  const [treeItems, setTreeItems] = useState<FileTreeItem[]>([]);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [entities, setEntities] = useState<CodeEntity[]>([]);
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [overview, setOverview] = useState<RepositoryOverview | null>(null);
  const [highlightLine, setHighlightLine] = useState<number | undefined>();
  const [isLoadingTree, setIsLoadingTree] = useState(false);
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [isLoadingOverview, setIsLoadingOverview] = useState(false);
  const [activeMainTab, setActiveMainTab] = useState<ExplorerTab>('files');
  const [activeRightTab, setActiveRightTab] = useState<RightTabType>('symbols');

  useEffect(() => {
    if (!selectedRepo) return;

    const loadRepoData = async () => {
      setIsLoadingTree(true);
      setIsLoadingOverview(true);
      try {
        const [tree, allEntities, allDeps, repoOverview, fws] = await Promise.allSettled([
          repositoryService.getFileTree(selectedRepo.id),
          repositoryService.getEntities(selectedRepo.id),
          repositoryService.getDependencies(selectedRepo.id),
          repositoryService.getOverview(selectedRepo.id),
          repositoryService.getFrameworks(selectedRepo.id),
        ]);

        if (tree.status === 'fulfilled') setTreeItems(tree.value);
        if (allEntities.status === 'fulfilled') setEntities(allEntities.value);
        if (allDeps.status === 'fulfilled') setDependencies(allDeps.value);
        if (repoOverview.status === 'fulfilled') setOverview(repoOverview.value);
        if (fws.status === 'fulfilled') setFrameworks(fws.value);
      } catch (err) {
        console.error('Failed to load repo explorer data:', err);
      } finally {
        setIsLoadingTree(false);
        setIsLoadingOverview(false);
      }
    };

    loadRepoData();
  }, [selectedRepo]);

  const handleSelectFile = async (path: string) => {
    if (!selectedRepo) return;
    setSelectedFilePath(path);
    setActiveMainTab('files');
    setIsLoadingFile(true);
    setHighlightLine(undefined);
    try {
      const content = await repositoryService.getFileContent(selectedRepo.id, path);
      setFileContent(content);
    } catch (err) {
      console.error('Failed to load file content:', err);
      setFileContent(null);
    } finally {
      setIsLoadingFile(false);
    }
  };

  const handleSelectSymbol = (entity: CodeEntity) => {
    if (selectedFilePath !== entity.file_path) {
      handleSelectFile(entity.file_path).then(() => {
        setHighlightLine(entity.start_line);
      });
    } else {
      setHighlightLine(entity.start_line);
    }
  };

  if (!selectedRepo) {
    return (
      <div className="p-12 text-center text-slate-400">
        Please select or connect a repository first to explore its codebase.
      </div>
    );
  }

  const fileEntities = selectedFilePath
    ? entities.filter((e) => e.file_path === selectedFilePath)
    : entities;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col p-4 gap-3 overflow-hidden">
      {/* Explorer Header with Meta Badges & Navigation Tabs */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 px-1 pb-1">
        {/* Repo Title & Main Dimension Switcher */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm md:text-base font-bold text-slate-100 truncate">
              {selectedRepo.owner}/{selectedRepo.name}
            </h2>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveMainTab('overview')}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeMainTab === 'overview'
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-700 shadow-sm font-semibold'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              Overview
            </button>

            <button
              onClick={() => setActiveMainTab('files')}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeMainTab === 'files'
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-700 shadow-sm font-semibold'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              <FileCode className="w-3.5 h-3.5 text-blue-400" />
              Files & Code
            </button>

            <button
              onClick={() => setActiveMainTab('structure')}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeMainTab === 'structure'
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-700 shadow-sm font-semibold'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              <FolderTree className="w-3.5 h-3.5 text-amber-400" />
              Structure
            </button>

            <button
              onClick={() => setActiveMainTab('symbols')}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeMainTab === 'symbols'
                  ? 'bg-purple-950 text-purple-300 border-purple-700 shadow-sm font-semibold'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              Symbols
            </button>

            <button
              onClick={() => setActiveMainTab('dependencies')}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeMainTab === 'dependencies'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-700 shadow-sm font-semibold'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              <Package className="w-3.5 h-3.5 text-emerald-400" />
              Dependencies
            </button>

            <button
              onClick={() => setActiveMainTab('frameworks')}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeMainTab === 'frameworks'
                  ? 'bg-pink-950 text-pink-300 border-pink-700 shadow-sm font-semibold'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-pink-400" />
              Frameworks
            </button>

            <button
              onClick={() => setActiveMainTab('languages')}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeMainTab === 'languages'
                  ? 'bg-cyan-950 text-cyan-300 border-cyan-700 shadow-sm font-semibold'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              <Code2 className="w-3.5 h-3.5 text-cyan-400" />
              Languages
            </button>
          </div>
        </div>
      </div>

      {/* Layout: flex-row so center naturally fills remaining space without dynamic grid classes */}
      <div className="flex-1 flex flex-row gap-4 min-h-0">
        {/* Left Column: fixed width file tree */}
        <div className="w-72 flex-shrink-0 bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex flex-col overflow-hidden shadow-lg">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-800 mb-2.5">
            <div className="flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Repository Files
              </span>
            </div>

            <button
              onClick={() => setActiveMainTab('structure')}
              title="View Repository Structure"
              className="text-[11px] text-amber-400 hover:text-amber-300 font-medium"
            >
              Structure
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {isLoadingTree ? (
              <div className="flex justify-center p-8">
                <Spinner size="md" />
              </div>
            ) : (
              <FileTreeView
                items={treeItems}
                selectedFilePath={selectedFilePath}
                onSelectFile={handleSelectFile}
              />
            )}
          </div>
        </div>

        {/* Center Column: fills all remaining space */}
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          {activeMainTab === 'overview' ? (
            <RepoOverviewDashboard
              overview={overview}
              onSelectFile={handleSelectFile}
              onSelectTab={(tab) => {
                setActiveMainTab(tab as ExplorerTab);
                setActiveRightTab(tab as RightTabType);
              }}
            />
          ) : activeMainTab === 'structure' ? (
            <div className="h-full overflow-y-auto p-5 bg-slate-950/60 border border-slate-800 rounded-xl">
              <RepositoryStructureView
                rootDirectories={overview?.root_directories || []}
                treeItems={treeItems}
                totalFiles={selectedRepo.total_files}
                totalLines={selectedRepo.total_lines}
                onSelectFile={handleSelectFile}
              />
            </div>
          ) : activeMainTab === 'dependencies' ? (
            <div className="h-full overflow-y-auto p-5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
                <Package className="w-5 h-5 text-emerald-400" />
                <div>
                  <h3 className="text-sm font-bold text-slate-100">Package Dependencies</h3>
                  <p className="text-xs text-slate-400">
                    {dependencies.length || overview?.dependencies_count || 0} libraries and dependencies indexed from manifests
                  </p>
                </div>
              </div>
              <DependencyInspector
                dependencies={dependencies.length > 0 ? dependencies : (overview?.dependencies || [])}
                onOpenSourceFile={handleSelectFile}
              />
            </div>
          ) : activeMainTab === 'languages' ? (
            <div className="h-full overflow-y-auto p-5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
                <Code2 className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-sm font-bold text-slate-100">Programming Languages Breakdown</h3>
                  <p className="text-xs text-slate-400">
                    Calculated code volume and lines across all file extensions
                  </p>
                </div>
              </div>
              <LanguageBreakdown
                languages={overview?.languages || selectedRepo.languages || {}}
                languagePercentages={overview?.language_percentages}
              />
            </div>
          ) : activeMainTab === 'frameworks' ? (
            <div className="h-full overflow-y-auto p-5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
                <Sparkles className="w-5 h-5 text-pink-400" />
                <div>
                  <h3 className="text-sm font-bold text-slate-100">Detected Frameworks & Tech Stack</h3>
                  <p className="text-xs text-slate-400">
                    Automated stack identification from dependencies, configuration files, and code structures
                  </p>
                </div>
              </div>
              <FrameworkInspector
                frameworks={frameworks.length > 0 ? frameworks : (overview?.frameworks || [])}
              />
            </div>
          ) : activeMainTab === 'symbols' ? (
            <div className="h-full overflow-y-auto p-5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
                <Cpu className="w-5 h-5 text-purple-400" />
                <div>
                  <h3 className="text-sm font-bold text-slate-100">AST Code Entities & Symbols</h3>
                  <p className="text-xs text-slate-400">
                    {entities.length} functions, classes, and methods parsed via Tree-sitter & AST engines
                  </p>
                </div>
              </div>
              <SymbolInspector
                entities={entities}
                onSelectSymbol={handleSelectSymbol}
              />
            </div>
          ) : isLoadingFile ? (
            <div className="h-full flex items-center justify-center bg-slate-950 rounded-xl border border-slate-800">
              <Spinner size="lg" />
            </div>
          ) : selectedFilePath && fileContent ? (
            <div className="h-full flex flex-col min-h-0 space-y-2">
              <div className="flex items-center justify-between px-2 text-xs">
                <button
                  onClick={() => setActiveMainTab('overview')}
                  className="flex items-center gap-1.5 text-slate-400 hover:text-cyan-300 transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Repository Overview
                </button>

                <span className="font-mono text-slate-400 text-[11px]">
                  {fileContent.path} • {fileContent.line_count} lines • {fileContent.language || 'Plain Text'}
                </span>
              </div>

              <div className="flex-1 min-h-0">
                <CodeViewer file={fileContent} highlightLine={highlightLine} />
              </div>
            </div>
          ) : (
            /* Rich Quick-Start Hub when in Files mode and no file is clicked yet */
            <div className="h-full overflow-y-auto p-6 bg-slate-950/60 border border-slate-800 rounded-xl space-y-6">
              <div className="text-center space-y-2 pb-4 border-b border-slate-800">
                <FolderGit2 className="w-12 h-12 text-cyan-400 mx-auto" />
                <h3 className="text-base font-bold text-slate-100">
                  {selectedRepo.owner}/{selectedRepo.name} Codebase
                </h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Select any file from the file tree on the left, or explore key repository entrypoints and dimensions below.
                </p>
              </div>

              {/* Key Entrypoints & Manifests */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
                  <Terminal className="w-4 h-4 text-emerald-400" />
                  <span>Key Entrypoints & Configurations</span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {overview?.key_entrypoints?.map((entry) => (
                    <button
                      key={entry}
                      onClick={() => handleSelectFile(entry)}
                      className="flex items-center gap-1.5 text-xs font-mono bg-cyan-950/70 border border-cyan-800 text-cyan-300 px-3 py-1.5 rounded-lg hover:bg-cyan-900 transition-all shadow-sm"
                    >
                      <FileCode className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{entry}</span>
                    </button>
                  ))}

                  {overview?.manifest_files?.map((manifest) => (
                    <button
                      key={manifest}
                      onClick={() => handleSelectFile(manifest)}
                      className="flex items-center gap-1.5 text-xs font-mono bg-slate-900 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-all shadow-sm"
                    >
                      <Package className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{manifest}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick Dimension Cards Grid */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div
                  onClick={() => setActiveMainTab('structure')}
                  className="p-3.5 bg-slate-900/60 border border-slate-800 hover:border-amber-500/50 rounded-xl cursor-pointer transition-all group"
                >
                  <div className="flex items-center gap-2 text-amber-400 mb-1">
                    <FolderTree className="w-4 h-4" />
                    <span className="text-xs font-bold">Repository Structure</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {overview?.root_directories?.length || 0} root directories & topology
                  </p>
                </div>

                <div
                  onClick={() => setActiveMainTab('dependencies')}
                  className="p-3.5 bg-slate-900/60 border border-slate-800 hover:border-emerald-500/50 rounded-xl cursor-pointer transition-all group"
                >
                  <div className="flex items-center gap-2 text-emerald-400 mb-1">
                    <Package className="w-4 h-4" />
                    <span className="text-xs font-bold">Dependencies</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {dependencies.length || overview?.dependencies_count || 0} packages indexed
                  </p>
                </div>

                <div
                  onClick={() => setActiveMainTab('frameworks')}
                  className="p-3.5 bg-slate-900/60 border border-slate-800 hover:border-pink-500/50 rounded-xl cursor-pointer transition-all group"
                >
                  <div className="flex items-center gap-2 text-pink-400 mb-1">
                    <Sparkles className="w-4 h-4" />
                    <span className="text-xs font-bold">Frameworks</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {frameworks.length || overview?.frameworks?.length || 0} frameworks detected
                  </p>
                </div>

                <div
                  onClick={() => setActiveMainTab('languages')}
                  className="p-3.5 bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 rounded-xl cursor-pointer transition-all group"
                >
                  <div className="flex items-center gap-2 text-cyan-400 mb-1">
                    <Code2 className="w-4 h-4" />
                    <span className="text-xs font-bold">Programming Languages</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {Object.keys(overview?.languages || selectedRepo.languages || {}).length} languages detected
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
