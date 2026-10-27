import React, { useState, useCallback, useRef } from 'react';
import {
  Network, RefreshCw, GitBranch, Workflow, Layout, Package,
  Database, Boxes, ChevronRight, Sparkles, Info, Clock,
  CheckCircle2, AlertCircle, Loader2, Code2, GitFork,
  Search, ShieldCheck, AlertTriangle, Layers, X, ChevronDown,
  ChevronUp, FileText, ArrowRight, Users, Activity, Shuffle, GitMerge
} from 'lucide-react';
import { Repository, DiagramViewMode, DiagramResponse, DiagramNodeEvidence, DiagramType } from '../types/repository';
import { repositoryService } from '../services/repositoryService';
import { MermaidViewer } from '../components/diagrams/MermaidViewer';
import { FunctionCallFlowStudio } from '../components/diagrams/FunctionCallFlowStudio';

interface ArchitecturePageProps {
  selectedRepo: Repository | null;
}

interface DiagramMeta {
  type: DiagramType;
  label: string;
  icon: React.ReactNode;
  codeDescription: string;
  workflowDescription: string;
  badge: string;
  color: string;
}

const DIAGRAM_TYPES: DiagramMeta[] = [
  {
    type: 'architecture',
    label: 'Architecture',
    icon: <Network className="w-4 h-4" />,
    codeDescription: 'High-level component topology, directory modules, and technical connections',
    workflowDescription: 'User interface, business capabilities, service interactions, and data movement during user tasks',
    badge: 'Graph TD',
    color: 'cyan',
  },
  {
    type: 'sequence',
    label: 'Sequence',
    icon: <GitBranch className="w-4 h-4" />,
    codeDescription: 'Inter-module function calls, internal service invocations, and API interactions',
    workflowDescription: 'Chronological interactions among user, screens, controllers, services, and validation branches',
    badge: 'sequenceDiagram',
    color: 'violet',
  },
  {
    type: 'flowchart',
    label: 'Flowchart',
    icon: <Workflow className="w-4 h-4" />,
    codeDescription: 'Processing pipeline: Entrypoints → Controllers → Services → Data layer',
    workflowDescription: 'User journey flowchart: Start, action gates, decision branches, validation errors, and completion',
    badge: 'flowchart TD',
    color: 'amber',
  },
  {
    type: 'uml',
    label: 'UML Class',
    icon: <Layout className="w-4 h-4" />,
    codeDescription: 'AST class definitions with methods, signatures, and code inheritance relationships',
    workflowDescription: 'Conceptual business domain model: Domain concepts, responsibilities, and entity relationships',
    badge: 'classDiagram',
    color: 'emerald',
  },
  {
    type: 'dependency',
    label: 'Dependencies',
    icon: <Package className="w-4 h-4" />,
    codeDescription: 'Package dependency manifest graph grouped by ecosystem (npm, pip, etc.)',
    workflowDescription: 'Feature & capability dependencies: Prerequisite features required to complete user workflows',
    badge: 'graph LR',
    color: 'rose',
  },
  {
    type: 'er',
    label: 'ER Diagram',
    icon: <Database className="w-4 h-4" />,
    codeDescription: 'Database models, schemas, and ORM entity relationships inferred from code',
    workflowDescription: 'Business data entities, fields, and relationships manipulated during user workflows',
    badge: 'erDiagram',
    color: 'sky',
  },
  {
    type: 'usecase',
    label: 'Use Case',
    icon: <Users className="w-4 h-4" />,
    codeDescription: 'Actor interactions, API endpoints, system boundary, and primary functional goals derived from codebase entry points',
    workflowDescription: 'User persona interactions with system capabilities, functional scope, permissions, and goal boundaries',
    badge: 'graph LR',
    color: 'indigo',
  },
  {
    type: 'state',
    label: 'State Machine',
    icon: <Activity className="w-4 h-4" />,
    codeDescription: 'Lifecycle transitions, state handlers, and status flows inferred from entity & workflow state machines',
    workflowDescription: 'Business lifecycle states: initial trigger, pending validations, active processing, terminal completion, and error states',
    badge: 'stateDiagram-v2',
    color: 'orange',
  },
  {
    type: 'dfd',
    label: 'Data Flow (DFD)',
    icon: <Shuffle className="w-4 h-4" />,
    codeDescription: 'Level-1 Data Flow: External entities, service processors, and data stores with directional input/output flows',
    workflowDescription: 'Information pipeline showing end-to-end data transformation, payload routing, persistence, and external outputs',
    badge: 'flowchart LR',
    color: 'teal',
  },
  {
    type: 'callflow',
    label: 'Function Call Flow',
    icon: <GitMerge className="w-4 h-4" />,
    codeDescription: 'Static AST function call graph: callers, callees, branch conditions, async/await chains, and recursive patterns',
    workflowDescription: 'Operational call paths from API entrypoints through business handlers into services and data layer',
    badge: 'flowchart LR',
    color: 'fuchsia',
  },
];

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; badge: string; glow: string }> = {
  cyan: {
    bg: 'bg-cyan-950/60',
    border: 'border-cyan-700',
    text: 'text-cyan-300',
    badge: 'bg-cyan-900/70 text-cyan-300 border-cyan-800',
    glow: 'shadow-cyan-900/40',
  },
  violet: {
    bg: 'bg-violet-950/60',
    border: 'border-violet-700',
    text: 'text-violet-300',
    badge: 'bg-violet-900/70 text-violet-300 border-violet-800',
    glow: 'shadow-violet-900/40',
  },
  amber: {
    bg: 'bg-amber-950/60',
    border: 'border-amber-700',
    text: 'text-amber-300',
    badge: 'bg-amber-900/70 text-amber-300 border-amber-800',
    glow: 'shadow-amber-900/40',
  },
  emerald: {
    bg: 'bg-emerald-950/60',
    border: 'border-emerald-700',
    text: 'text-emerald-300',
    badge: 'bg-emerald-900/70 text-emerald-300 border-emerald-800',
    glow: 'shadow-emerald-900/40',
  },
  rose: {
    bg: 'bg-rose-950/60',
    border: 'border-rose-700',
    text: 'text-rose-300',
    badge: 'bg-rose-900/70 text-rose-300 border-rose-800',
    glow: 'shadow-rose-900/40',
  },
  sky: {
    bg: 'bg-sky-950/60',
    border: 'border-sky-700',
    text: 'text-sky-300',
    badge: 'bg-sky-900/70 text-sky-300 border-sky-800',
    glow: 'shadow-sky-900/40',
  },
  indigo: {
    bg: 'bg-indigo-950/60',
    border: 'border-indigo-700',
    text: 'text-indigo-300',
    badge: 'bg-indigo-900/70 text-indigo-300 border-indigo-800',
    glow: 'shadow-indigo-900/40',
  },
  orange: {
    bg: 'bg-orange-950/60',
    border: 'border-orange-700',
    text: 'text-orange-300',
    badge: 'bg-orange-900/70 text-orange-300 border-orange-800',
    glow: 'shadow-orange-900/40',
  },
  teal: {
    bg: 'bg-teal-950/60',
    border: 'border-teal-700',
    text: 'text-teal-300',
    badge: 'bg-teal-900/70 text-teal-300 border-teal-800',
    glow: 'shadow-teal-900/40',
  },
  fuchsia: {
    bg: 'bg-fuchsia-950/60',
    border: 'border-fuchsia-700',
    text: 'text-fuchsia-300',
    badge: 'bg-fuchsia-900/70 text-fuchsia-300 border-fuchsia-800',
    glow: 'shadow-fuchsia-900/40',
  },
};

interface DiagramState {
  mermaid_code: string;
  description: string;
  summary?: string;
  components_involved?: string[];
  key_relationships?: string[];
  source_references?: string[];
  evidence_status?: 'verified' | 'partial' | 'unverified';
  evidence_limitations?: string;
  nodes_evidence?: DiagramNodeEvidence[];
  status: 'idle' | 'loading' | 'done' | 'error';
  error?: string;
  generatedAt?: string;
}

export const ArchitecturePage: React.FC<ArchitecturePageProps> = ({ selectedRepo }) => {
  const [activeType, setActiveType] = useState<DiagramType>('architecture');
  const [viewMode, setViewMode] = useState<DiagramViewMode>('code');
  const [workflowInput, setWorkflowInput] = useState<string>('');
  const [showEvidencePanel, setShowEvidencePanel] = useState<boolean>(false);
  const [evidenceFilter, setEvidenceFilter] = useState<'all' | 'verified' | 'inferred'>('all');
  const [evidenceSearch, setEvidenceSearch] = useState<string>('');
  const [selectedEvidenceNode, setSelectedEvidenceNode] = useState<DiagramNodeEvidence | null>(null);

  // Independent cache per mode and diagram type: `${mode}:${type}`
  const [diagrams, setDiagrams] = useState<Record<string, DiagramState>>({});

  const cacheKey = `${selectedRepo?.id || 'default'}:${viewMode}:${activeType}`;
  const currentDiagram = diagrams[cacheKey];
  const activeMeta = DIAGRAM_TYPES.find((d) => d.type === activeType) || DIAGRAM_TYPES[0];
  const colors = COLOR_MAP[activeMeta.color] || COLOR_MAP.cyan;

  const loadDiagram = useCallback(
    async (type: DiagramType, mode: DiagramViewMode = viewMode, customWorkflowPrompt?: string) => {
      if (!selectedRepo) return;
      const key = `${selectedRepo.id}:${mode}:${type}`;
      setDiagrams((prev) => ({
        ...prev,
        [key]: {
          mermaid_code: prev[key]?.mermaid_code || '',
          description: prev[key]?.description || '',
          status: 'loading',
        },
      }));
      try {
        const res: DiagramResponse = await repositoryService.getDiagram(
          selectedRepo.id,
          type,
          mode,
          customWorkflowPrompt || (mode === 'workflow' ? workflowInput : undefined)
        );
        setDiagrams((prev) => ({
          ...prev,
          [key]: {
            mermaid_code: res.mermaid_code,
            description: res.description,
            summary: res.summary,
            components_involved: res.components_involved,
            key_relationships: res.key_relationships,
            source_references: res.source_references,
            evidence_status: res.evidence_status,
            evidence_limitations: res.evidence_limitations,
            nodes_evidence: res.nodes_evidence || [],
            status: 'done',
            generatedAt: new Date().toLocaleTimeString(),
          },
        }));
      } catch (err: any) {
        setDiagrams((prev) => ({
          ...prev,
          [key]: {
            mermaid_code: '',
            description: '',
            status: 'error',
            error: err.message || 'Failed to generate diagram',
          },
        }));
      }
    },
    [selectedRepo, viewMode, workflowInput]
  );

  const handleSelectType = (type: DiagramType) => {
    setActiveType(type);
    const key = `${selectedRepo?.id || 'default'}:${viewMode}:${type}`;
    if (!diagrams[key] || diagrams[key]?.status === 'idle') {
      loadDiagram(type, viewMode);
    }
  };

  const handleSelectViewMode = (mode: DiagramViewMode) => {
    if (mode === viewMode) return;
    setViewMode(mode);
    const key = `${selectedRepo?.id || 'default'}:${mode}:${activeType}`;
    // Auto-load if not yet fetched for this mode
    if (!diagrams[key] || diagrams[key]?.status === 'idle') {
      loadDiagram(activeType, mode);
    }
  };

  const handleRegenerate = () => loadDiagram(activeType, viewMode, workflowInput);

  const handleApplyWorkflowPrompt = (promptText: string) => {
    setWorkflowInput(promptText);
    loadDiagram(activeType, 'workflow', promptText);
  };

  // Auto-load default diagram (architecture, code view) on mount or repo change
  const bootstrapped = useRef(false);
  React.useEffect(() => {
    if (selectedRepo && !bootstrapped.current) {
      bootstrapped.current = true;
      loadDiagram('architecture', 'code');
    }
  }, [selectedRepo, loadDiagram]);

  // Reset state when repo changes
  React.useEffect(() => {
    bootstrapped.current = false;
    setDiagrams({});
    setActiveType('architecture');
    setViewMode('code');
    setSelectedEvidenceNode(null);
  }, [selectedRepo?.id]);

  // Evidence node filtering
  const evidenceNodes = currentDiagram?.nodes_evidence || [];
  const verifiedCount = evidenceNodes.filter((e) => e.confidence === 'verified').length;
  const inferredCount = evidenceNodes.filter((e) => e.confidence === 'inferred').length;

  const filteredEvidence = evidenceNodes.filter((node) => {
    if (evidenceFilter === 'verified' && node.confidence !== 'verified') return false;
    if (evidenceFilter === 'inferred' && node.confidence !== 'inferred') return false;
    if (evidenceSearch) {
      const q = evidenceSearch.toLowerCase();
      const matchLabel = node.label.toLowerCase().includes(q);
      const matchFile = (node.source_file || '').toLowerCase().includes(q);
      const matchType = node.evidence_type.toLowerCase().includes(q);
      return matchLabel || matchFile || matchType;
    }
    return true;
  });

  if (!selectedRepo) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-20 text-center gap-6">
        <div className="w-20 h-20 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center">
          <Boxes className="w-10 h-10 text-slate-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-300 mb-1">No Repository Selected</h3>
          <p className="text-sm text-slate-500 max-w-sm">
            Select or connect a repository to generate architecture, sequence, flowchart, UML, dependency, ER, use case, state machine, and data flow (DFD) diagrams.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col overflow-hidden">
      {/* Page Header */}
      <div className="flex-shrink-0 px-6 pt-4 pb-3 border-b border-slate-800 bg-slate-950/70 backdrop-blur-md">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          {/* Title & Repo Info */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center flex-shrink-0">
              <Network className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-slate-100">Diagram Studio</h1>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/80">
                  Dual-View
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 truncate">
                {selectedRepo.owner}/{selectedRepo.name} · {DIAGRAM_TYPES.length} diagram types
              </p>
            </div>
          </div>

          {/* Center: Dual-View Segmented Control */}
          <div className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800 shadow-inner">
            <button
              id="diagram-view-code-btn"
              onClick={() => handleSelectViewMode('code')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'code'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-900/40 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Code / Repository View</span>
            </button>
            <button
              id="diagram-view-workflow-btn"
              onClick={() => handleSelectViewMode('workflow')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'workflow'
                  ? 'bg-gradient-to-r from-amber-600 to-rose-600 text-white shadow-md shadow-amber-900/40 border border-amber-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <GitFork className="w-3.5 h-3.5" />
              <span>User Workflow View</span>
            </button>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {currentDiagram?.status === 'done' && (
              <button
                id="toggle-evidence-inspector-btn"
                onClick={() => setShowEvidencePanel((v) => !v)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                  showEvidencePanel
                    ? 'bg-cyan-950 border-cyan-700 text-cyan-300'
                    : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white hover:border-slate-600'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Evidence ({evidenceNodes.length})</span>
                {showEvidencePanel ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}
            {currentDiagram?.status === 'done' && (
              <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500">
                <Clock className="w-3 h-3" />
                <span>Generated {currentDiagram.generatedAt}</span>
              </div>
            )}
            <button
              id="diagram-regenerate-btn"
              onClick={handleRegenerate}
              disabled={currentDiagram?.status === 'loading'}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:border-cyan-700 hover:bg-cyan-950/40 transition-all disabled:opacity-40"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${currentDiagram?.status === 'loading' ? 'animate-spin' : ''}`}
              />
              Re-generate
            </button>
          </div>
        </div>
      </div>

      {/* Main Workspace: Left sidebar + Diagram + Traceability Inspector */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left Sidebar: 6 Diagram Types */}
        <div className="w-52 flex-shrink-0 border-r border-slate-800 bg-slate-950/40 overflow-y-auto p-3 space-y-1.5">
          <div className="flex items-center justify-between px-2 pb-1">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-600">
              Diagram Types
            </p>
            <span className="text-[10px] font-mono text-slate-500">
              {viewMode === 'code' ? 'Code' : 'Workflow'}
            </span>
          </div>

          {DIAGRAM_TYPES.map((meta) => {
            const key = `${viewMode}:${meta.type}`;
            const state = diagrams[key];
            const isActive = activeType === meta.type;
            const c = COLOR_MAP[meta.color] || COLOR_MAP.cyan;
            return (
              <button
                key={meta.type}
                id={`diagram-tab-${meta.type}`}
                onClick={() => handleSelectType(meta.type)}
                className={`w-full text-left px-3 py-2.5 rounded-xl border transition-all group flex flex-col gap-1 ${
                  isActive
                    ? `${c.bg} ${c.border} shadow-lg ${c.glow}`
                    : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className={`flex items-center gap-2 ${isActive ? c.text : 'text-slate-400 group-hover:text-slate-200'}`}>
                    {meta.icon}
                    <span className="text-xs font-semibold">{meta.label}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {state?.status === 'loading' && (
                      <Loader2 className="w-3 h-3 text-slate-500 animate-spin" />
                    )}
                    {state?.status === 'done' && (
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    )}
                    {state?.status === 'error' && (
                      <AlertCircle className="w-3 h-3 text-rose-500" />
                    )}
                    {isActive && state?.status !== 'loading' && (
                      <ChevronRight className={`w-3 h-3 ${c.text}`} />
                    )}
                  </div>
                </div>
                <span className={`text-[10px] leading-tight ${isActive ? 'text-slate-300' : 'text-slate-600 group-hover:text-slate-500'}`}>
                  {meta.badge}
                </span>
              </button>
            );
          })}
        </div>

        {/* Center: Main diagram content area */}
        {activeType === 'callflow' ? (
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            <FunctionCallFlowStudio selectedRepo={selectedRepo} />
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden p-4 gap-3">
            {/* Diagram Viewer Area */}
            <div className="flex-1 min-h-0 overflow-hidden relative">
            {!currentDiagram || currentDiagram.status === 'idle' ? (
              <div className="h-full flex flex-col items-center justify-center gap-4 bg-slate-900/30 border border-slate-800 rounded-xl">
                <div className={`w-16 h-16 rounded-2xl border flex items-center justify-center ${colors.bg} ${colors.border}`}>
                  <span className={`scale-150 ${colors.text}`}>{activeMeta.icon}</span>
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-300 mb-1">
                    {activeMeta.label} ({viewMode === 'code' ? 'Code View' : 'Workflow View'}) not yet generated
                  </p>
                  <p className="text-xs text-slate-500 max-w-xs">
                    {viewMode === 'code'
                      ? 'Analyze AST classes, calls, dependencies, and file relationships'
                      : 'Synthesize end-to-end user actions, frontend routes, and controllers'}
                  </p>
                </div>
                <button
                  onClick={handleRegenerate}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-xs font-semibold transition-all ${colors.bg} ${colors.border} ${colors.text} hover:opacity-80`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Generate {activeMeta.label} ({viewMode === 'code' ? 'Code' : 'Workflow'})
                </button>
              </div>
            ) : currentDiagram.status === 'loading' ? (
              <div className="h-full flex flex-col items-center justify-center gap-4 bg-slate-900/30 border border-slate-800 rounded-xl">
                <div className="relative">
                  <div className="w-14 h-14 rounded-full border-2 border-slate-800 flex items-center justify-center">
                    <Loader2 className={`w-7 h-7 animate-spin ${colors.text}`} />
                  </div>
                  <div className={`absolute inset-0 rounded-full border-2 ${colors.border} opacity-30 animate-ping`} />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-300 mb-1">
                    Generating {activeMeta.label} ({viewMode === 'code' ? 'Code View' : 'Workflow View'})…
                  </p>
                  <p className="text-xs text-slate-500">
                    {viewMode === 'code'
                      ? 'Mapping files, symbol calls, and package dependency trees'
                      : 'Analyzing frontend screens, controller routes, validation gates, and user actions'}
                  </p>
                </div>
              </div>
            ) : currentDiagram.status === 'error' ? (
              <div className="h-full flex flex-col items-center justify-center gap-4 bg-slate-900/30 border border-rose-900/50 rounded-xl">
                <AlertCircle className="w-10 h-10 text-rose-400" />
                <div className="text-center">
                  <p className="text-sm font-semibold text-rose-300 mb-1">Generation Failed</p>
                  <p className="text-xs text-slate-500 max-w-xs">{currentDiagram.error}</p>
                </div>
                <button
                  onClick={handleRegenerate}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs font-semibold hover:bg-rose-950 transition-all"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Retry
                </button>
              </div>
            ) : (
              <div className="h-full overflow-hidden flex flex-col">
                <div className="flex-1 min-h-0">
                  <MermaidViewer
                    chart={currentDiagram.mermaid_code}
                    title={`${activeMeta.label} (${viewMode === 'code' ? 'Code View' : 'Workflow View'}) · ${selectedRepo.owner}/${selectedRepo.name}`}
                    description={currentDiagram.description}
                    diagramType={activeMeta.label}
                    meta={{
                      summary: currentDiagram.summary,
                      components_involved: currentDiagram.components_involved,
                      key_relationships: currentDiagram.key_relationships,
                      source_references: currentDiagram.source_references,
                      evidence_status: currentDiagram.evidence_status,
                      evidence_limitations: currentDiagram.evidence_limitations,
                    }}
                    filenameBase={`${activeType}-${viewMode === 'workflow' ? 'user-workflow' : 'code-view'}`}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Traceability & Evidence Inspector Drawer / Panel */}
          {showEvidencePanel && currentDiagram?.status === 'done' && (
            <div className="h-64 flex-shrink-0 bg-slate-950/90 border border-slate-800 rounded-xl flex flex-col overflow-hidden shadow-2xl">
              {/* Inspector Header */}
              <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/60 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-slate-200">Traceability & Evidence Inspector</span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" />
                    {verifiedCount} Verified
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    {inferredCount} Inferred
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {/* Filter tabs */}
                  <div className="flex items-center bg-slate-900 rounded-lg p-0.5 border border-slate-800 text-[11px]">
                    <button
                      onClick={() => setEvidenceFilter('all')}
                      className={`px-2 py-0.5 rounded ${evidenceFilter === 'all' ? 'bg-slate-800 text-white font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      All ({evidenceNodes.length})
                    </button>
                    <button
                      onClick={() => setEvidenceFilter('verified')}
                      className={`px-2 py-0.5 rounded ${evidenceFilter === 'verified' ? 'bg-emerald-900/60 text-emerald-300 font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      Verified ({verifiedCount})
                    </button>
                    <button
                      onClick={() => setEvidenceFilter('inferred')}
                      className={`px-2 py-0.5 rounded ${evidenceFilter === 'inferred' ? 'bg-amber-900/60 text-amber-300 font-medium' : 'text-slate-400 hover:text-slate-200'}`}
                    >
                      Inferred ({inferredCount})
                    </button>
                  </div>

                  {/* Search box */}
                  <div className="relative w-44">
                    <Search className="w-3 h-3 text-slate-500 absolute left-2 top-2" />
                    <input
                      type="text"
                      placeholder="Filter nodes..."
                      value={evidenceSearch}
                      onChange={(e) => setEvidenceSearch(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-7 pr-2 py-1 text-[11px] text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-600"
                    />
                  </div>

                  <button
                    onClick={() => setShowEvidencePanel(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Inspector Content: Node Cards list + Selected Detail view */}
              <div className="flex-1 flex min-h-0 overflow-hidden">
                {/* Nodes List */}
                <div className="flex-1 overflow-y-auto p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {filteredEvidence.map((node) => {
                    const isSelected = selectedEvidenceNode?.id === node.id;
                    const isVerified = node.confidence === 'verified';
                    return (
                      <div
                        key={node.id}
                        onClick={() => setSelectedEvidenceNode(node)}
                        className={`p-2.5 rounded-xl border text-left cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-cyan-950/60 border-cyan-600 shadow-lg shadow-cyan-950/50'
                            : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-1.5 mb-1">
                          <span className="text-xs font-semibold text-slate-200 truncate flex-1">
                            {node.label}
                          </span>
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-medium border uppercase tracking-wider flex-shrink-0 ${
                              isVerified
                                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                                : 'bg-amber-950/80 text-amber-300 border-amber-800'
                            }`}
                          >
                            {node.confidence}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 text-[10px] text-slate-400 mb-1">
                          <span className="px-1.5 py-0.2 rounded bg-slate-800 border border-slate-700/60 text-slate-300 font-mono">
                            {node.evidence_type}
                          </span>
                          {node.source_file && (
                            <span className="truncate text-slate-400 font-mono">
                              {node.source_file.split('/').slice(-2).join('/')}
                              {node.line_range ? `:${node.line_range}` : ''}
                            </span>
                          )}
                        </div>

                        {node.details && (
                          <p className="text-[10px] text-slate-500 line-clamp-1 italic">
                            {node.details}
                          </p>
                        )}
                      </div>
                    );
                  })}
                  {filteredEvidence.length === 0 && (
                    <div className="col-span-full text-center py-8 text-xs text-slate-500">
                      No diagram nodes matched the filter criteria.
                    </div>
                  )}
                </div>

                {/* Selected Node Details Drawer */}
                {selectedEvidenceNode && (
                  <div className="w-80 border-l border-slate-800 bg-slate-900/80 p-3.5 flex flex-col gap-2 overflow-y-auto">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                        Node Evidence Detail
                      </span>
                      <button
                        onClick={() => setSelectedEvidenceNode(null)}
                        className="text-slate-500 hover:text-slate-300"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>

                    <h4 className="text-xs font-bold text-slate-100">{selectedEvidenceNode.label}</h4>

                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-500 block">Verification Status</span>
                        <span
                          className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border mt-0.5 ${
                            selectedEvidenceNode.confidence === 'verified'
                              ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                              : 'bg-amber-950 text-amber-300 border-amber-800'
                          }`}
                        >
                          {selectedEvidenceNode.confidence === 'verified' ? (
                            <ShieldCheck className="w-3 h-3" />
                          ) : (
                            <AlertTriangle className="w-3 h-3" />
                          )}
                          {selectedEvidenceNode.confidence === 'verified' ? 'Verified Code Evidence' : 'Synthesized / Inferred'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500 block">Evidence Type</span>
                        <span className="font-mono text-slate-300 text-[11px]">{selectedEvidenceNode.evidence_type}</span>
                      </div>

                      {selectedEvidenceNode.source_file && (
                        <div>
                          <span className="text-[10px] text-slate-500 block">Source File & Line</span>
                          <span className="font-mono text-cyan-300 text-[11px] break-all block bg-slate-950 p-1.5 rounded border border-slate-800">
                            {selectedEvidenceNode.source_file}
                            {selectedEvidenceNode.line_range ? ` (L${selectedEvidenceNode.line_range})` : ''}
                          </span>
                        </div>
                      )}

                      {selectedEvidenceNode.entity_name && (
                        <div>
                          <span className="text-[10px] text-slate-500 block">AST Entity / Symbol</span>
                          <span className="font-mono text-slate-300 text-[11px]">{selectedEvidenceNode.entity_name}</span>
                        </div>
                      )}

                      {selectedEvidenceNode.details && (
                        <div>
                          <span className="text-[10px] text-slate-500 block">Implementation Notes</span>
                          <p className="text-slate-400 text-[11px] leading-relaxed mt-0.5 italic">
                            {selectedEvidenceNode.details}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Bottom status bar: all diagram statuses */}
          <div className="flex-shrink-0 flex items-center gap-4 px-3 py-2 bg-slate-900/40 border border-slate-800 rounded-xl overflow-x-auto scrollbar-none">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-600 whitespace-nowrap">
              {viewMode === 'code' ? 'Code View Status' : 'Workflow View Status'}
            </span>
            {DIAGRAM_TYPES.map((meta) => {
              const key = `${viewMode}:${meta.type}`;
              const state = diagrams[key];
              const c = COLOR_MAP[meta.color] || COLOR_MAP.cyan;
              return (
                <button
                  key={meta.type}
                  onClick={() => handleSelectType(meta.type)}
                  className={`flex items-center gap-1.5 text-[11px] whitespace-nowrap px-2 py-1 rounded-lg transition-colors ${
                    activeType === meta.type ? `${c.bg} ${c.text} border ${c.border}` : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {state?.status === 'loading' ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : state?.status === 'done' ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                  ) : state?.status === 'error' ? (
                    <AlertCircle className="w-3 h-3 text-rose-500" />
                  ) : (
                    <div className="w-3 h-3 rounded-full border border-slate-700" />
                  )}
                  <span>{meta.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
      </div>
    </div>
  );
};
