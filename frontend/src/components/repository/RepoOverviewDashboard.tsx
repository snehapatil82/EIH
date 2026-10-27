import React from 'react';
import {
  FolderTree,
  FileCode,
  Layers,
  Sparkles,
  Package,
  Code2,
  Server,
  Database,
  Cpu,
  ArrowRight,
  GitBranch,
  Terminal,
  Activity,
  Compass,
} from 'lucide-react';
import { RepositoryOverview, Framework, Dependency, CodeEntity } from '../../types/repository';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { LanguageBreakdown } from './LanguageBreakdown';
import { FrameworkInspector } from './FrameworkInspector';

interface RepoOverviewDashboardProps {
  overview: RepositoryOverview | null;
  onSelectFile: (filePath: string) => void;
  onSelectTab?: (tab: 'symbols' | 'dependencies' | 'frameworks' | 'languages' | 'structure') => void;
}

export const RepoOverviewDashboard: React.FC<RepoOverviewDashboardProps> = ({
  overview,
  onSelectFile,
  onSelectTab,
}) => {
  if (!overview) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-12 text-center text-slate-400">
        <Compass className="w-12 h-12 text-slate-600 mb-3 animate-pulse" />
        <h3 className="text-base font-semibold text-slate-200">Loading Repository Intelligence...</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Analyzing repository topology, frameworks, dependencies, and code AST...
        </p>
      </div>
    );
  }

  const {
    name,
    owner,
    url,
    default_branch,
    total_files,
    total_lines,
    total_directories,
    languages,
    language_percentages,
    frameworks,
    dependencies,
    entities_count,
    entity_counts_by_type,
    root_directories,
    key_entrypoints,
    manifest_files,
  } = overview;

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-slate-950/60 rounded-xl border border-slate-800">
      {/* Top Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-slate-100">{owner}/{name}</span>
            <Badge variant="cyan" size="sm">Indexed & Active</Badge>
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1">
              <GitBranch className="w-3.5 h-3.5 text-slate-500" />
              {default_branch}
            </span>
            <span>•</span>
            <span>{total_files} Files</span>
            <span>•</span>
            <span>{total_lines.toLocaleString()} LOC</span>
            <span>•</span>
            <span>{total_directories} Directories</span>
          </div>
        </div>

        {key_entrypoints && key_entrypoints.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-semibold uppercase">Entrypoint:</span>
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Terminal className="w-3.5 h-3.5 text-cyan-400" />}
              onClick={() => onSelectFile(key_entrypoints[0])}
            >
              {key_entrypoints[0]}
            </Button>
          </div>
        )}
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Languages</span>
            <Code2 className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">
            {Object.keys(languages || {}).length}
          </div>
          <div className="text-[11px] text-cyan-400 mt-1 truncate">
            Primary: {Object.keys(languages || {})[0] || 'N/A'}
          </div>
        </div>

        <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Frameworks</span>
            <Sparkles className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">
            {frameworks?.length || 0}
          </div>
          <div className="text-[11px] text-pink-400 mt-1 truncate">
            {frameworks?.[0]?.name || 'Standard stack'}
          </div>
        </div>

        <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Dependencies</span>
            <Package className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">
            {dependencies?.length || 0}
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 truncate">
            Packages indexed
          </div>
        </div>

        <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">AST Symbols</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">
            {entities_count || 0}
          </div>
          <div className="text-[11px] text-purple-400 mt-1 truncate">
            Functions & classes
          </div>
        </div>

        <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Structure</span>
            <FolderTree className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">
            {root_directories?.length || 0}
          </div>
          <div className="text-[11px] text-amber-400 mt-1 truncate">
            Root modules
          </div>
        </div>
      </div>

      {/* 2-Column Section: Frameworks & Programming Languages */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Frameworks & Tech Stack */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-pink-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Detected Frameworks & Libraries ({frameworks?.length || 0})
              </h4>
            </div>
            {onSelectTab && (
              <button
                onClick={() => onSelectTab('frameworks')}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
              >
                View all →
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {frameworks && frameworks.length > 0 ? (
              frameworks.slice(0, 6).map((fw) => (
                <div
                  key={fw.name}
                  className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-lg hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-100 truncate">{fw.name}</span>
                    {fw.version && (
                      <span className="text-[10px] font-mono text-cyan-300 bg-slate-800 px-1 rounded">
                        v{fw.version}
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-400 block truncate mt-0.5">
                    {fw.category}
                  </span>
                  <span className="text-[10px] text-slate-500 block truncate mt-1">
                    {fw.source}
                  </span>
                </div>
              ))
            ) : (
              <div className="col-span-2 p-6 text-center text-xs text-slate-500">
                No specific frameworks identified yet.
              </div>
            )}
          </div>
        </div>

        {/* Programming Languages Breakdown */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Programming Languages Breakdown
              </h4>
            </div>
            {onSelectTab && (
              <button
                onClick={() => onSelectTab('languages')}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
              >
                Details →
              </button>
            )}
          </div>

          <LanguageBreakdown
            languages={languages}
            languagePercentages={language_percentages}
          />
        </div>
      </div>

      {/* 2-Column Section: Repository Structure & Dependencies / Entrypoints */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Root Directory Structure & Module Topology */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderTree className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Repository Structure & Directory Topology
              </h4>
            </div>
            {onSelectTab && (
              <button
                onClick={() => onSelectTab('structure')}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
              >
                Structure →
              </button>
            )}
          </div>

          <div className="space-y-2">
            {root_directories && root_directories.length > 0 ? (
              root_directories.map((dir) => (
                <div
                  key={dir.path}
                  className="p-2.5 bg-slate-900/70 border border-slate-800 rounded-lg flex items-center justify-between gap-3 hover:bg-slate-850 transition-colors"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <FolderTree className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                      <span className="text-xs font-mono font-bold text-slate-200 truncate">
                        {dir.name}/
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 mt-1">
                      {dir.languages.map((l) => (
                        <span key={l} className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded">
                          {l}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="text-right font-mono text-[11px] text-slate-400 flex-shrink-0">
                    <div>{dir.file_count} files</div>
                    <div className="text-slate-500">{dir.line_count.toLocaleString()} lines</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-xs text-slate-500">
                Flat repository root directory.
              </div>
            )}
          </div>
        </div>

        {/* Key Entrypoints & Dependencies */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-4">
          {/* Key Entrypoints & Manifests */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Key Entrypoints & Manifests
              </h4>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {key_entrypoints?.map((entry) => (
                <button
                  key={entry}
                  onClick={() => onSelectFile(entry)}
                  className="flex items-center gap-1.5 text-xs font-mono bg-cyan-950/60 border border-cyan-800 text-cyan-300 px-2.5 py-1 rounded-lg hover:bg-cyan-900/60 transition-colors"
                >
                  <FileCode className="w-3 h-3 text-cyan-400" />
                  {entry}
                </button>
              ))}

              {manifest_files?.map((manifest) => (
                <button
                  key={manifest}
                  onClick={() => onSelectFile(manifest)}
                  className="flex items-center gap-1.5 text-xs font-mono bg-slate-900 border border-slate-700 text-slate-300 px-2.5 py-1 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  <Package className="w-3 h-3 text-emerald-400" />
                  {manifest}
                </button>
              ))}
            </div>
          </div>

          {/* Dependencies Quick Preview */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="w-4 h-4 text-emerald-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Dependencies ({dependencies?.length || 0})
                </h4>
              </div>
              {onSelectTab && (
                <button
                  onClick={() => onSelectTab('dependencies')}
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
                >
                  Inspect all →
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-1.5 max-h-[160px] overflow-y-auto pr-1">
              {dependencies && dependencies.length > 0 ? (
                dependencies.slice(0, 10).map((dep, i) => (
                  <div
                    key={`${dep.name}-${i}`}
                    className="p-1.5 bg-slate-900/60 border border-slate-800 rounded flex items-center justify-between gap-1 text-[11px] font-mono"
                  >
                    <span className="text-slate-200 truncate font-semibold">{dep.name}</span>
                    {dep.version && (
                      <span className="text-cyan-400 text-[10px] flex-shrink-0">{dep.version}</span>
                    )}
                  </div>
                ))
              ) : (
                <div className="col-span-2 text-center text-xs text-slate-500 py-2">
                  No manifest dependencies parsed yet.
                </div>
              )}
            </div>
          </div>

          {/* AST Entity Breakdown */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  AST Code Entities ({entities_count || 0})
                </h4>
              </div>
              {onSelectTab && (
                <button
                  onClick={() => onSelectTab('symbols')}
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
                >
                  Explore AST →
                </button>
              )}
            </div>

            <div className="flex flex-wrap gap-2 text-xs">
              {Object.entries(entity_counts_by_type || {}).map(([type, count]) => (
                <div
                  key={type}
                  className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-1.5 capitalize font-mono text-[11px]"
                >
                  <span className="text-purple-400 font-bold">{count}</span>
                  <span>{type}s</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
