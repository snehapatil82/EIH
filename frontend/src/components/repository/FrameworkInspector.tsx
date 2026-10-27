import React, { useState } from 'react';
import {
  Layers, Server, Database, Globe, Sparkles, ShieldCheck,
  Zap, Box, Cpu, Search, CheckCircle2, Package, ChevronDown,
  ChevronRight, ExternalLink, Star,
} from 'lucide-react';
import { Framework } from '../../types/repository';

interface FrameworkInspectorProps {
  frameworks: Framework[];
  onSelectFramework?: (framework: Framework) => void;
}

interface CategoryConfig {
  icon: React.ReactNode;
  color: string;
  bg: string;
  border: string;
}

const CATEGORY_CONFIG: Record<string, CategoryConfig> = {
  backend: {
    icon: <Server className="w-3.5 h-3.5" />,
    color: 'text-emerald-400',
    bg: 'bg-emerald-950/60',
    border: 'border-emerald-800/60',
  },
  server: {
    icon: <Server className="w-3.5 h-3.5" />,
    color: 'text-emerald-400',
    bg: 'bg-emerald-950/60',
    border: 'border-emerald-800/60',
  },
  asgi: {
    icon: <Server className="w-3.5 h-3.5" />,
    color: 'text-emerald-400',
    bg: 'bg-emerald-950/60',
    border: 'border-emerald-800/60',
  },
  database: {
    icon: <Database className="w-3.5 h-3.5" />,
    color: 'text-amber-400',
    bg: 'bg-amber-950/60',
    border: 'border-amber-800/60',
  },
  orm: {
    icon: <Database className="w-3.5 h-3.5" />,
    color: 'text-amber-400',
    bg: 'bg-amber-950/60',
    border: 'border-amber-800/60',
  },
  frontend: {
    icon: <Layers className="w-3.5 h-3.5" />,
    color: 'text-cyan-400',
    bg: 'bg-cyan-950/60',
    border: 'border-cyan-800/60',
  },
  ui: {
    icon: <Layers className="w-3.5 h-3.5" />,
    color: 'text-cyan-400',
    bg: 'bg-cyan-950/60',
    border: 'border-cyan-800/60',
  },
  styling: {
    icon: <Sparkles className="w-3.5 h-3.5" />,
    color: 'text-pink-400',
    bg: 'bg-pink-950/60',
    border: 'border-pink-800/60',
  },
  css: {
    icon: <Sparkles className="w-3.5 h-3.5" />,
    color: 'text-pink-400',
    bg: 'bg-pink-950/60',
    border: 'border-pink-800/60',
  },
  security: {
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
    color: 'text-rose-400',
    bg: 'bg-rose-950/60',
    border: 'border-rose-800/60',
  },
  auth: {
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
    color: 'text-rose-400',
    bg: 'bg-rose-950/60',
    border: 'border-rose-800/60',
  },
  build: {
    icon: <Zap className="w-3.5 h-3.5" />,
    color: 'text-yellow-400',
    bg: 'bg-yellow-950/60',
    border: 'border-yellow-800/60',
  },
  bundler: {
    icon: <Zap className="w-3.5 h-3.5" />,
    color: 'text-yellow-400',
    bg: 'bg-yellow-950/60',
    border: 'border-yellow-800/60',
  },
  tool: {
    icon: <Zap className="w-3.5 h-3.5" />,
    color: 'text-yellow-400',
    bg: 'bg-yellow-950/60',
    border: 'border-yellow-800/60',
  },
  ai: {
    icon: <Cpu className="w-3.5 h-3.5" />,
    color: 'text-purple-400',
    bg: 'bg-purple-950/60',
    border: 'border-purple-800/60',
  },
  'machine learning': {
    icon: <Cpu className="w-3.5 h-3.5" />,
    color: 'text-purple-400',
    bg: 'bg-purple-950/60',
    border: 'border-purple-800/60',
  },
  llm: {
    icon: <Cpu className="w-3.5 h-3.5" />,
    color: 'text-purple-400',
    bg: 'bg-purple-950/60',
    border: 'border-purple-800/60',
  },
  'full-stack': {
    icon: <Globe className="w-3.5 h-3.5" />,
    color: 'text-indigo-400',
    bg: 'bg-indigo-950/60',
    border: 'border-indigo-800/60',
  },
};

const DEFAULT_CONFIG: CategoryConfig = {
  icon: <Box className="w-3.5 h-3.5" />,
  color: 'text-slate-400',
  bg: 'bg-slate-900/60',
  border: 'border-slate-800',
};

function getCategoryConfig(category: string) {
  const cat = category.toLowerCase();
  for (const [key, val] of Object.entries(CATEGORY_CONFIG)) {
    if (cat.includes(key)) return val;
  }
  return DEFAULT_CONFIG;
}

function getConfidenceValue(confidence?: string): number {
  if (!confidence) return 75;
  const c = confidence.toLowerCase();
  if (c === 'high') return 95;
  if (c === 'medium') return 65;
  if (c === 'low') return 35;
  return 75;
}

function getConfidenceColor(confidence?: string): string {
  const c = (confidence || '').toLowerCase();
  if (c === 'high') return 'bg-emerald-500';
  if (c === 'medium') return 'bg-amber-500';
  if (c === 'low') return 'bg-rose-500';
  return 'bg-cyan-500';
}

// Group frameworks by category
function groupByCategory(frameworks: Framework[]): Record<string, Framework[]> {
  const groups: Record<string, Framework[]> = {};
  for (const fw of frameworks) {
    const cat = fw.category || 'Other';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(fw);
  }
  return groups;
}

export const FrameworkInspector: React.FC<FrameworkInspectorProps> = ({
  frameworks = [],
  onSelectFramework,
}) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'list' | 'group'>('group');

  const categories = Array.from(new Set(frameworks.map((f) => f.category)));

  const filteredFrameworks = frameworks.filter((fw) => {
    const matchesSearch =
      fw.name.toLowerCase().includes(search.toLowerCase()) ||
      fw.category.toLowerCase().includes(search.toLowerCase()) ||
      (fw.source || '').toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !selectedCategory || fw.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const toggleGroup = (cat: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  if (frameworks.length === 0) {
    return (
      <div className="p-10 text-center space-y-3">
        <Package className="w-10 h-10 text-slate-700 mx-auto" />
        <p className="text-xs text-slate-500">No frameworks or major libraries detected.</p>
        <p className="text-[11px] text-slate-600">
          Try re-indexing the repository to detect tech stack components.
        </p>
      </div>
    );
  }

  const grouped = groupByCategory(filteredFrameworks);

  return (
    <div className="space-y-3">
      {/* Search + controls */}
      <div className="space-y-2">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search frameworks, tools, libraries…"
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-600 focus:ring-1 focus:ring-cyan-600/40 transition-colors"
          />
        </div>

        <div className="flex items-center justify-between">
          {/* Category filter pills */}
          <div className="flex gap-1 overflow-x-auto pb-0.5 scrollbar-none text-[11px] flex-1 mr-3">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-2 py-0.5 rounded-md transition-colors whitespace-nowrap flex-shrink-0 ${
                selectedCategory === null
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                  : 'bg-slate-900/80 text-slate-500 border border-slate-800 hover:text-slate-300'
              }`}
            >
              All {frameworks.length}
            </button>
            {categories.map((cat) => {
              const cfg = getCategoryConfig(cat);
              const count = frameworks.filter((f) => f.category === cat).length;
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-md transition-colors whitespace-nowrap flex-shrink-0 border ${
                    selectedCategory === cat
                      ? `${cfg.bg} ${cfg.color} ${cfg.border}`
                      : 'bg-slate-900/80 text-slate-500 border-slate-800 hover:text-slate-300'
                  }`}
                >
                  {cat} <span className="opacity-60">({count})</span>
                </button>
              );
            })}
          </div>

          {/* View mode toggle */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg p-0.5 flex-shrink-0">
            <button
              onClick={() => setViewMode('group')}
              className={`text-[10px] px-2 py-0.5 rounded-md transition-colors ${
                viewMode === 'group' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Group
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`text-[10px] px-2 py-0.5 rounded-md transition-colors ${
                viewMode === 'list' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {filteredFrameworks.length === 0 ? (
        <div className="p-6 text-center text-slate-500 text-xs">
          No frameworks match your filter.
        </div>
      ) : viewMode === 'list' ? (
        /* ── List View ─────────────────────────────────── */
        <div className="space-y-1.5 max-h-[520px] overflow-y-auto pr-1">
          {filteredFrameworks.map((fw) => {
            const cfg = getCategoryConfig(fw.category);
            const confVal = getConfidenceValue(fw.confidence);
            const confColor = getConfidenceColor(fw.confidence);
            return (
              <FrameworkCard
                key={fw.name}
                fw={fw}
                cfg={cfg}
                confVal={confVal}
                confColor={confColor}
                onSelect={onSelectFramework}
              />
            );
          })}
        </div>
      ) : (
        /* ── Grouped View ──────────────────────────────── */
        <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
          {Object.entries(grouped).map(([cat, fws]) => {
            const cfg = getCategoryConfig(cat);
            const isCollapsed = collapsedGroups.has(cat);
            return (
              <div key={cat} className="rounded-xl border border-slate-800 overflow-hidden">
                {/* Group header */}
                <button
                  onClick={() => toggleGroup(cat)}
                  className={`w-full flex items-center justify-between px-3 py-2 ${cfg.bg} border-b ${
                    isCollapsed ? 'border-transparent' : 'border-slate-800/60'
                  } hover:opacity-90 transition-opacity`}
                >
                  <div className={`flex items-center gap-2 ${cfg.color}`}>
                    {cfg.icon}
                    <span className="text-xs font-bold">{cat}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${cfg.bg} ${cfg.border} border opacity-80`}>
                      {fws.length}
                    </span>
                  </div>
                  {isCollapsed
                    ? <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                    : <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                  }
                </button>

                {/* Group items */}
                {!isCollapsed && (
                  <div className="divide-y divide-slate-800/50">
                    {fws.map((fw) => {
                      const confVal = getConfidenceValue(fw.confidence);
                      const confColor = getConfidenceColor(fw.confidence);
                      return (
                        <FrameworkCard
                          key={fw.name}
                          fw={fw}
                          cfg={cfg}
                          confVal={confVal}
                          confColor={confColor}
                          onSelect={onSelectFramework}
                          compact
                        />
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

/* ── Individual Framework Card ──────────────────────────────────── */
interface FrameworkCardProps {
  fw: Framework;
  cfg: CategoryConfig;
  confVal: number;
  confColor: string;
  onSelect?: (fw: Framework) => void;
  compact?: boolean;
}

const FrameworkCard: React.FC<FrameworkCardProps> = ({
  fw, cfg, confVal, confColor, onSelect, compact = false,
}) => (
  <div
    onClick={() => onSelect && onSelect(fw)}
    className={`group transition-all cursor-default ${
      onSelect ? 'cursor-pointer' : ''
    } ${
      compact
        ? 'px-3 py-2.5 bg-slate-950/40 hover:bg-slate-900/60'
        : 'p-3 bg-slate-900/60 border border-slate-800 rounded-xl hover:border-slate-700 hover:bg-slate-900 card-hover'
    }`}
  >
    <div className="flex items-start justify-between gap-2">
      <div className="flex items-center gap-2.5 min-w-0">
        {/* Icon */}
        {!compact && (
          <div className={`flex-shrink-0 p-2 rounded-lg border ${cfg.bg} ${cfg.border} transition-colors`}>
            <span className={cfg.color}>{cfg.icon}</span>
          </div>
        )}

        <div className="min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-bold text-slate-100 group-hover:text-white transition-colors">
              {fw.name}
            </span>
            {fw.version && (
              <span className="text-[10px] font-mono px-1.5 py-px rounded bg-slate-800 text-cyan-300 border border-slate-700 flex-shrink-0">
                v{fw.version}
              </span>
            )}
          </div>

          {!compact && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`text-[10px] font-medium ${cfg.color}`}>{fw.category}</span>
              <span className="text-slate-700">·</span>
              <span className="text-[10px] text-slate-500 font-mono truncate max-w-[160px]">
                {fw.source}
              </span>
            </div>
          )}

          {compact && (
            <span className="text-[10px] text-slate-500 font-mono">{fw.source}</span>
          )}
        </div>
      </div>

      {/* Confidence badge */}
      <div className="flex-shrink-0 flex flex-col items-end gap-1">
        <div className={`flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
          confVal >= 85 ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-900' :
          confVal >= 60 ? 'bg-amber-950/60 text-amber-400 border border-amber-900' :
                          'bg-rose-950/60 text-rose-400 border border-rose-900'
        }`}>
          <CheckCircle2 className="w-2.5 h-2.5" />
          <span>{fw.confidence || 'High'}</span>
        </div>
      </div>
    </div>

    {/* Confidence bar */}
    {!compact && (
      <div className="mt-2.5 space-y-1">
        <div className="flex items-center justify-between text-[10px] text-slate-600">
          <span>Detection Confidence</span>
          <span className={
            confVal >= 85 ? 'text-emerald-400' :
            confVal >= 60 ? 'text-amber-400' : 'text-rose-400'
          }>{confVal}%</span>
        </div>
        <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${confColor}`}
            style={{ width: `${confVal}%` }}
          />
        </div>
      </div>
    )}
  </div>
);
