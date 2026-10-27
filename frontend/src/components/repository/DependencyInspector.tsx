import React, { useState } from 'react';
import { Package, Search, ExternalLink, FileCode, CheckCircle2 } from 'lucide-react';
import { Dependency } from '../../types/repository';
import { Badge } from '../common/Badge';

interface DependencyInspectorProps {
  dependencies: Dependency[];
  onSelectDependency?: (dep: Dependency) => void;
  onOpenSourceFile?: (sourceFile: string) => void;
}

const getEcosystemBadge = (ecosystem: string) => {
  switch (ecosystem.toLowerCase()) {
    case 'npm':
      return <Badge variant="danger" size="sm">npm</Badge>;
    case 'pip':
    case 'pypi':
      return <Badge variant="success" size="sm">pip</Badge>;
    case 'cargo':
      return <Badge variant="warning" size="sm">cargo</Badge>;
    case 'maven':
    case 'gradle':
      return <Badge variant="purple" size="sm">jvm</Badge>;
    default:
      return <Badge variant="cyan" size="sm">{ecosystem}</Badge>;
  }
};

export const DependencyInspector: React.FC<DependencyInspectorProps> = ({
  dependencies = [],
  onSelectDependency,
  onOpenSourceFile,
}) => {
  const [search, setSearch] = useState('');
  const [selectedEcosystem, setSelectedEcosystem] = useState<string | null>(null);

  const ecosystems = Array.from(new Set(dependencies.map((d) => d.ecosystem).filter(Boolean)));

  const filtered = dependencies.filter((dep) => {
    const matchesSearch =
      dep.name.toLowerCase().includes(search.toLowerCase()) ||
      (dep.version && dep.version.toLowerCase().includes(search.toLowerCase())) ||
      (dep.source_file && dep.source_file.toLowerCase().includes(search.toLowerCase()));
    const matchesEcosystem = !selectedEcosystem || dep.ecosystem === selectedEcosystem;
    return matchesSearch && matchesEcosystem;
  });

  if (dependencies.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        <Package className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        No dependencies extracted yet. Index package manifests (package.json, requirements.txt, etc.) to view dependencies.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Search & Ecosystem Filter */}
      <div className="space-y-2">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search dependencies (e.g. express, mongoose)..."
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
          />
        </div>

        {ecosystems.length > 1 && (
          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none text-[11px]">
            <button
              onClick={() => setSelectedEcosystem(null)}
              className={`px-2 py-0.5 rounded transition-colors whitespace-nowrap ${
                selectedEcosystem === null
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              All ({dependencies.length})
            </button>
            {ecosystems.map((eco) => (
              <button
                key={eco}
                onClick={() => setSelectedEcosystem(selectedEcosystem === eco ? null : eco)}
                className={`px-2 py-0.5 rounded transition-colors whitespace-nowrap ${
                  selectedEcosystem === eco
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                {eco} ({dependencies.filter((d) => d.ecosystem === eco).length})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Dependencies List */}
      <div className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1">
        {filtered.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-xs">
            No dependencies match your filter.
          </div>
        ) : (
          filtered.map((dep, idx) => (
            <div
              key={`${dep.name}-${dep.source_file}-${idx}`}
              onClick={() => onSelectDependency && onSelectDependency(dep)}
              className="p-2.5 bg-slate-900/50 border border-slate-800 rounded-lg hover:border-slate-700 hover:bg-slate-850/70 transition-all flex items-center justify-between gap-2 group"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-semibold text-slate-200 truncate">
                    {dep.name}
                  </span>
                  {dep.version && (
                    <span className="text-[10px] font-mono text-cyan-300 bg-slate-800/90 px-1.5 py-0.2 rounded border border-slate-700">
                      {dep.version}
                    </span>
                  )}
                </div>

                {dep.source_file && (
                  <div
                    onClick={(e) => {
                      if (onOpenSourceFile) {
                        e.stopPropagation();
                        onOpenSourceFile(dep.source_file);
                      }
                    }}
                    className={`flex items-center gap-1 mt-1 text-[10px] text-slate-400 font-mono truncate ${
                      onOpenSourceFile ? 'hover:text-cyan-400 cursor-pointer' : ''
                    }`}
                  >
                    <FileCode className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate">{dep.source_file}</span>
                  </div>
                )}
              </div>

              <div className="flex-shrink-0">
                {getEcosystemBadge(dep.ecosystem)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
