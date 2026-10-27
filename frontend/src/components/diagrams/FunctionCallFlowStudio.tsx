import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  GitMerge, GitFork, ArrowRight, ArrowLeft, Search, RefreshCw,
  Download, Copy, Check, Eye, Code2, Layers, AlertCircle, Loader2,
  Sparkles, FileCode, CheckCircle2, ShieldCheck, AlertTriangle,
  ChevronRight, ChevronDown, ChevronUp, X, Filter, ExternalLink,
  CornerDownRight, CornerUpLeft, Info, HelpCircle, Maximize2, Minimize2
} from 'lucide-react';
import {
  Repository,
  CallGraphResponse,
  CallGraphNodeItem,
  CallGraphEdgeItem,
  CallGraphFunctionSummary,
  FileContent
} from '../../types/repository';
import { repositoryService } from '../../services/repositoryService';
import { MermaidViewer } from './MermaidViewer';
import { CodeViewer } from '../repository/CodeViewer';

interface FunctionCallFlowStudioProps {
  selectedRepo: Repository;
}

export const FunctionCallFlowStudio: React.FC<FunctionCallFlowStudioProps> = ({ selectedRepo }) => {
  // State for function selection and search
  const [functionsList, setFunctionsList] = useState<CallGraphFunctionSummary[]>([]);
  const [isLoadingFunctions, setIsLoadingFunctions] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFileFilter, setSelectedFileFilter] = useState<string>('all');
  const [isSearchDropdownOpen, setIsSearchDropdownOpen] = useState(false);
  const searchDropdownRef = useRef<HTMLDivElement>(null);

  // Call graph state
  const [selectedFunctionId, setSelectedFunctionId] = useState<string | null>(null);
  const [explorationMode, setExplorationMode] = useState<'calls_from' | 'called_by' | 'full'>('calls_from');
  const [traversalDepth, setTraversalDepth] = useState<number>(2);
  const [isCollapsedBranches, setIsCollapsedBranches] = useState<boolean>(false);
  const [callGraphData, setCallGraphData] = useState<CallGraphResponse | null>(null);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);

  // Inspector / Selection state
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeInspectorTab, setActiveInspectorTab] = useState<'explanation' | 'details' | 'calls'>('explanation');
  const [viewMode, setViewMode] = useState<'interactive' | 'mermaid'>('interactive');

  // Code Viewer Modal state
  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [codeModalFile, setCodeModalFile] = useState<FileContent | null>(null);
  const [codeModalLine, setCodeModalLine] = useState<number>(1);
  const [isLoadingCode, setIsLoadingCode] = useState(false);

  // Notification / Copy state
  const [copiedMermaid, setCopiedMermaid] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch functions list on repo change
  const loadFunctions = useCallback(async (search?: string, filePath?: string) => {
    setIsLoadingFunctions(true);
    try {
      const fns = await repositoryService.getCallGraphFunctions(
        selectedRepo.id,
        search,
        filePath === 'all' ? undefined : filePath
      );
      setFunctionsList(fns);
      // Auto-select top connected function if none selected yet
      if (!selectedFunctionId && fns.length > 0) {
        setSelectedFunctionId(fns[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load call graph functions:', err);
    } finally {
      setIsLoadingFunctions(false);
    }
  }, [selectedRepo.id, selectedFunctionId]);

  useEffect(() => {
    loadFunctions(searchQuery, selectedFileFilter);
  }, [loadFunctions, searchQuery, selectedFileFilter]);

  // Load call graph when function, mode, or depth changes
  const loadCallGraph = useCallback(async (funcId?: string, mode = explorationMode, depth = traversalDepth) => {
    setIsLoadingGraph(true);
    setGraphError(null);
    try {
      const data = await repositoryService.getCallGraph(
        selectedRepo.id,
        funcId || undefined,
        mode,
        depth
      );
      setCallGraphData(data);
      if (!funcId && data.root_function_id) {
        setSelectedFunctionId(data.root_function_id);
      }
      // Default inspector selection to root node
      setSelectedNodeId(funcId || data.root_function_id);
    } catch (err: any) {
      setGraphError(err.message || 'Failed to generate call graph.');
    } finally {
      setIsLoadingGraph(false);
    }
  }, [selectedRepo.id, explorationMode, traversalDepth]);

  useEffect(() => {
    loadCallGraph(selectedFunctionId || undefined, explorationMode, traversalDepth);
  }, [selectedRepo.id, selectedFunctionId, explorationMode, traversalDepth, loadCallGraph]);

  // Click outside to close search dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchDropdownRef.current && !searchDropdownRef.current.contains(e.target as Node)) {
        setIsSearchDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Unique files list for the file filter dropdown
  const uniqueFiles = useMemo(() => {
    const set = new Set<string>();
    functionsList.forEach((f) => {
      if (f.file_path) set.add(f.file_path);
    });
    return Array.from(set).sort();
  }, [functionsList]);

  // Currently inspected node details
  const inspectedNode = useMemo(() => {
    if (!callGraphData) return null;
    return callGraphData.nodes.find((n) => n.id === selectedNodeId) ||
           callGraphData.nodes.find((n) => n.id === callGraphData.root_function_id) ||
           null;
  }, [callGraphData, selectedNodeId]);

  // Edges filtered for collapsing branches if enabled
  const displayedEdges = useMemo(() => {
    if (!callGraphData) return [];
    if (!isCollapsedBranches) return callGraphData.edges;
    // When collapsed, skip secondary non-direct branch edges
    return callGraphData.edges.filter((e) => !e.is_conditional || e.branch_condition?.includes('main') || e.caller_id === callGraphData.root_function_id);
  }, [callGraphData, isCollapsedBranches]);

  // Connected nodes & edges relative to selected node for path highlighting
  const activePathEdges = useMemo(() => {
    if (!selectedNodeId || !callGraphData) return new Set<string>();
    const edgeSet = new Set<string>();
    callGraphData.edges.forEach((e) => {
      if (e.caller_id === selectedNodeId || e.callee_id === selectedNodeId) {
        edgeSet.add(`${e.caller_id}->${e.callee_id || e.callee_symbol_name}:${e.call_site_line}`);
      }
    });
    return edgeSet;
  }, [selectedNodeId, callGraphData]);

  const activeConnectedNodeIds = useMemo(() => {
    if (!selectedNodeId || !callGraphData) return new Set<string>();
    const nodeSet = new Set<string>([selectedNodeId]);
    callGraphData.edges.forEach((e) => {
      if (e.caller_id === selectedNodeId && e.callee_id) {
        nodeSet.add(e.callee_id);
      }
      if (e.callee_id === selectedNodeId) {
        nodeSet.add(e.caller_id);
      }
    });
    return nodeSet;
  }, [selectedNodeId, callGraphData]);

  // Handle open source in CodeViewer modal
  const handleOpenSource = async (filePath: string, line: number) => {
    setIsLoadingCode(true);
    setIsCodeModalOpen(true);
    setCodeModalLine(line);
    try {
      const fileData = await repositoryService.getFileContent(selectedRepo.id, filePath);
      setCodeModalFile(fileData);
    } catch (err: any) {
      console.error('Failed to load file content:', err);
    } finally {
      setIsLoadingCode(false);
    }
  };

  // Handle export .mmd
  const handleExportMMD = () => {
    if (!callGraphData?.mermaid_code) return;
    const blob = new Blob([callGraphData.mermaid_code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `callflow-${callGraphData.root_function_name.replace(/[^a-zA-Z0-9_-]/g, '_')}-${explorationMode}.mmd`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Handle copy Mermaid code
  const handleCopyMermaid = () => {
    if (!callGraphData?.mermaid_code) return;
    navigator.clipboard.writeText(callGraphData.mermaid_code);
    setCopiedMermaid(true);
    setTimeout(() => setCopiedMermaid(false), 2000);
  };

  // Handle refresh
  const handleRefreshGraph = async () => {
    setIsRefreshing(true);
    try {
      await repositoryService.refreshCallGraph(selectedRepo.id);
      await loadFunctions();
      await loadCallGraph(selectedFunctionId || undefined);
    } catch (err) {
      console.error('Failed to refresh call graph:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Group nodes into topological visual layers for interactive canvas
  const organizedLayers = useMemo(() => {
    if (!callGraphData || !callGraphData.nodes.length) return [];
    const rootId = callGraphData.root_function_id;
    const rootNode = callGraphData.nodes.find((n) => n.id === rootId);

    // Callers (incoming)
    const incomingCallers = callGraphData.nodes.filter((n) => n.id !== rootId && callGraphData.edges.some((e) => e.caller_id === n.id && e.callee_id === rootId));
    // Direct Callees (outgoing)
    const directCallees = callGraphData.nodes.filter((n) => n.id !== rootId && callGraphData.edges.some((e) => e.caller_id === rootId && e.callee_id === n.id));
    // Nested Callees (depth > 1)
    const directIds = new Set([rootId, ...incomingCallers.map((n) => n.id), ...directCallees.map((n) => n.id)]);
    const nestedCallees = callGraphData.nodes.filter((n) => !directIds.has(n.id));

    const layers: Array<{ title: string; subtitle: string; nodes: CallGraphNodeItem[]; color: string }> = [];

    if (incomingCallers.length > 0) {
      layers.push({
        title: 'Incoming Callers',
        subtitle: `${incomingCallers.length} function(s) calling root`,
        nodes: incomingCallers,
        color: 'border-violet-800/80 bg-violet-950/20 text-violet-300',
      });
    }

    if (rootNode) {
      layers.push({
        title: 'Selected Target Function',
        subtitle: 'Root of exploration',
        nodes: [rootNode],
        color: 'border-cyan-700 bg-cyan-950/40 text-cyan-200',
      });
    }

    if (directCallees.length > 0) {
      layers.push({
        title: 'Direct Outgoing Calls',
        subtitle: `${directCallees.length} function(s) directly called`,
        nodes: directCallees,
        color: 'border-fuchsia-800/80 bg-fuchsia-950/20 text-fuchsia-300',
      });
    }

    if (nestedCallees.length > 0) {
      layers.push({
        title: 'Downstream / Nested Calls',
        subtitle: `${nestedCallees.length} deep callee(s)`,
        nodes: nestedCallees,
        color: 'border-amber-800/80 bg-amber-950/20 text-amber-300',
      });
    }

    return layers;
  }, [callGraphData]);

  return (
    <div className="h-full flex flex-col min-h-0 bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Controls Toolbar */}
      <div className="flex-shrink-0 px-4 py-2.5 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md flex flex-wrap items-center justify-between gap-3">
        {/* Left: Search Function & File Filter */}
        <div className="flex items-center gap-2 flex-1 min-w-[320px] max-w-xl">
          {/* File Filter Dropdown */}
          <div className="relative">
            <select
              value={selectedFileFilter}
              onChange={(e) => setSelectedFileFilter(e.target.value)}
              className="h-8 pl-2.5 pr-7 text-xs rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:border-slate-700 focus:outline-none focus:border-cyan-600 appearance-none max-w-[140px] truncate"
              title="Filter by file"
            >
              <option value="all">All Files ({uniqueFiles.length})</option>
              {uniqueFiles.map((f) => (
                <option key={f} value={f}>
                  {f.split('/').pop()}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3 h-3 text-slate-500 absolute right-2 top-2.5 pointer-events-none" />
          </div>

          {/* Function Live Search Typeahead */}
          <div className="relative flex-1" ref={searchDropdownRef}>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchDropdownOpen(true);
                }}
                onFocus={() => setIsSearchDropdownOpen(true)}
                placeholder="Search function by name or file…"
                className="w-full h-8 pl-8 pr-8 text-xs rounded-lg bg-slate-900 border border-slate-800 text-slate-200 placeholder-slate-500 hover:border-slate-700 focus:outline-none focus:border-cyan-500 transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-2 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Dropdown Menu */}
            {isSearchDropdownOpen && (
              <div className="absolute left-0 right-0 top-9 max-h-72 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-y-auto z-50 p-1 space-y-0.5">
                {isLoadingFunctions ? (
                  <div className="p-4 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                    <span>Indexing functions…</span>
                  </div>
                ) : functionsList.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">
                    No functions matching &quot;{searchQuery}&quot;
                  </div>
                ) : (
                  functionsList.map((fn) => {
                    const isSelected = fn.id === selectedFunctionId;
                    return (
                      <button
                        key={fn.id}
                        onClick={() => {
                          setSelectedFunctionId(fn.id);
                          setIsSearchDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-colors ${
                          isSelected
                            ? 'bg-cyan-950 border border-cyan-800 text-cyan-200'
                            : 'hover:bg-slate-800/80 text-slate-300'
                        }`}
                      >
                        <div className="min-w-0 pr-2">
                          <div className="flex items-center gap-1.5 font-semibold font-mono text-slate-100 truncate">
                            <span className="text-cyan-400">{fn.name}()</span>
                            {fn.enclosing_class && (
                              <span className="text-[10px] text-slate-400 font-sans">
                                in {fn.enclosing_class}
                              </span>
                            )}
                            {fn.is_async && (
                              <span className="text-[9px] px-1 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                                async
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-500 truncate mt-0.5">
                            {fn.file_path}:L{fn.start_line}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-400 flex-shrink-0">
                          <span title="Outgoing calls" className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">
                            {fn.callee_count} calls
                          </span>
                          <span title="Incoming callers" className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">
                            {fn.caller_count} callers
                          </span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
        </div>

        {/* Center: Exploration Modes & Traversal Depth */}
        <div className="flex items-center gap-2">
          {/* Mode Segmented Controls */}
          <div className="flex items-center bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setExplorationMode('calls_from')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                explorationMode === 'calls_from'
                  ? 'bg-fuchsia-950 border border-fuchsia-700 text-fuchsia-200 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="View functions directly called by the selected function"
            >
              <ArrowRight className="w-3.5 h-3.5 text-fuchsia-400" />
              <span>Calls From</span>
            </button>
            <button
              onClick={() => setExplorationMode('called_by')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                explorationMode === 'called_by'
                  ? 'bg-violet-950 border border-violet-700 text-violet-200 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="View functions that invoke the selected function"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-violet-400" />
              <span>Called By</span>
            </button>
            <button
              onClick={() => setExplorationMode('full')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                explorationMode === 'full'
                  ? 'bg-cyan-950 border border-cyan-700 text-cyan-200 shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Explore both incoming callers and outgoing callees"
            >
              <GitMerge className="w-3.5 h-3.5 text-cyan-400" />
              <span>Full Flow</span>
            </button>
          </div>

          {/* Depth Selector */}
          <div className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800 text-xs">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Depth</span>
            {[1, 2, 3, 4, 5].map((d) => (
              <button
                key={d}
                onClick={() => setTraversalDepth(d)}
                className={`w-6 h-6 rounded flex items-center justify-center font-bold text-xs transition-colors ${
                  traversalDepth === d
                    ? 'bg-cyan-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          {/* Branch Collapsing Toggle */}
          <button
            onClick={() => setIsCollapsedBranches((v) => !v)}
            className={`px-2.5 py-1 text-xs rounded-lg border transition-colors flex items-center gap-1.5 ${
              isCollapsedBranches
                ? 'bg-amber-950 border-amber-800 text-amber-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
            title="Collapse secondary branches or view all paths"
          >
            <Filter className="w-3 h-3" />
            <span>{isCollapsedBranches ? 'Branches Collapsed' : 'All Branches'}</span>
          </button>
        </div>

        {/* Right: View Toggle, Refresh, Export Actions */}
        <div className="flex items-center gap-2">
          {/* View Mode Toggle: Interactive Graph vs Mermaid Renderer */}
          <div className="flex items-center bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('interactive')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === 'interactive'
                  ? 'bg-slate-800 text-cyan-300 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3 h-3" />
              <span>Interactive</span>
            </button>
            <button
              onClick={() => setViewMode('mermaid')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === 'mermaid'
                  ? 'bg-slate-800 text-cyan-300 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code2 className="w-3 h-3" />
              <span>Mermaid</span>
            </button>
          </div>

          {/* Copy Mermaid */}
          <button
            onClick={handleCopyMermaid}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Copy Mermaid syntax"
          >
            {copiedMermaid ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{copiedMermaid ? 'Copied' : 'Copy'}</span>
          </button>

          {/* Export .mmd */}
          <button
            onClick={handleExportMMD}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Download Mermaid (.mmd) file"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Export .mmd</span>
          </button>

          {/* Refresh / Re-index button */}
          <button
            onClick={handleRefreshGraph}
            disabled={isRefreshing || isLoadingGraph}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white transition-colors disabled:opacity-40"
            title="Refresh AST Call Graph"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Studio Body: Graph Canvas + Side Inspector Panel */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Center Canvas Area */}
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative">
          {isLoadingGraph ? (
            <div className="h-full flex flex-col items-center justify-center gap-3 bg-slate-950">
              <div className="w-12 h-12 rounded-full border-2 border-slate-800 flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
              </div>
              <p className="text-sm font-semibold text-slate-300">Traversing Function Call Flow…</p>
              <p className="text-xs text-slate-500">
                Extracting AST call sites, control-flow branches, and caller hierarchies.
              </p>
            </div>
          ) : graphError ? (
            <div className="h-full flex flex-col items-center justify-center gap-3 bg-slate-950 p-6 text-center">
              <AlertCircle className="w-10 h-10 text-rose-500" />
              <p className="text-sm font-semibold text-rose-300">Call Graph Extraction Failed</p>
              <p className="text-xs text-slate-500 max-w-md">{graphError}</p>
              <button
                onClick={() => loadCallGraph(selectedFunctionId || undefined)}
                className="px-4 py-2 rounded-xl bg-slate-800 border border-slate-700 text-xs font-semibold hover:border-cyan-700 text-slate-200"
              >
                Retry Extraction
              </button>
            </div>
          ) : !callGraphData || callGraphData.nodes.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center gap-3 bg-slate-950 p-6 text-center">
              <GitMerge className="w-12 h-12 text-slate-700" />
              <p className="text-sm font-semibold text-slate-400">No Functions Found</p>
              <p className="text-xs text-slate-500 max-w-sm">
                No syntax-supported function declarations were extracted for this repository.
              </p>
            </div>
          ) : viewMode === 'mermaid' ? (
            /* Rendered Mermaid SVG View */
            <div className="h-full overflow-hidden p-3">
              <MermaidViewer
                chart={callGraphData.mermaid_code}
                title={`Function Call Flow · ${callGraphData.root_function_name}`}
                description={callGraphData.explanation?.summary}
                diagramType="Function Call Flow"
                filenameBase={`callflow-${callGraphData.root_function_name}`}
                meta={{
                  summary: callGraphData.explanation?.control_flow_narrative,
                  components_involved: callGraphData.explanation?.components_involved,
                  evidence_status: 'verified',
                  evidence_limitations: callGraphData.explanation?.static_limitations,
                }}
              />
            </div>
          ) : (
            /* Interactive Directed Graph Layout */
            <div className="h-full overflow-y-auto p-4 space-y-6">
              {/* Stats Bar */}
              <div className="flex items-center justify-between text-xs px-3 py-2 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 flex-wrap gap-2">
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-slate-200">
                    Root: <span className="text-cyan-400 font-mono">{callGraphData.root_function_name}()</span>
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                    {callGraphData.stats.total_nodes} Nodes
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                    {callGraphData.stats.total_edges} Edges
                  </span>
                  {callGraphData.stats.conditional_calls > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800 text-[11px]">
                      {callGraphData.stats.conditional_calls} Conditional Branches
                    </span>
                  )}
                  {callGraphData.stats.async_calls > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 text-[11px]">
                      {callGraphData.stats.async_calls} Async
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-500">
                  Click any node to inspect function details, branches, and code.
                </div>
              </div>

              {/* Topological Layer Columns */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {organizedLayers.map((layer, lIdx) => (
                  <div key={lIdx} className="flex flex-col gap-3">
                    {/* Layer Header */}
                    <div className="pb-1 border-b border-slate-800">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">{layer.title}</h4>
                        <span className="text-[10px] text-slate-500 font-mono">{layer.nodes.length}</span>
                      </div>
                      <p className="text-[10px] text-slate-500">{layer.subtitle}</p>
                    </div>

                    {/* Nodes in this layer */}
                    <div className="space-y-3">
                      {layer.nodes.map((node) => {
                        const isSelected = node.id === selectedNodeId;
                        const isRoot = node.id === callGraphData.root_function_id;
                        const isConnected = activeConnectedNodeIds.has(node.id);

                        return (
                          <div
                            key={node.id}
                            onClick={() => setSelectedNodeId(node.id)}
                            className={`p-3.5 rounded-xl border transition-all cursor-pointer relative group ${
                              isSelected
                                ? 'bg-cyan-950/70 border-cyan-500 shadow-lg shadow-cyan-950/50 ring-2 ring-cyan-500/40'
                                : isConnected
                                ? 'bg-slate-900 border-slate-700 hover:border-slate-600'
                                : 'bg-slate-900/40 border-slate-800/80 opacity-80 hover:opacity-100 hover:bg-slate-900 hover:border-slate-700'
                            }`}
                          >
                            {/* Card Header: Name + Badges */}
                            <div className="flex items-start justify-between gap-2 mb-1.5">
                              <div className="min-w-0">
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  <span className={`text-xs font-bold font-mono truncate ${isSelected ? 'text-cyan-300' : 'text-slate-200 group-hover:text-cyan-300'}`}>
                                    {node.name}()
                                  </span>
                                  {isRoot && (
                                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-cyan-600 text-white">
                                      ROOT
                                    </span>
                                  )}
                                  {node.is_async && (
                                    <span className="text-[9px] px-1 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                                      async
                                    </span>
                                  )}
                                </div>
                                {node.enclosing_class && (
                                  <div className="text-[10px] text-slate-400 font-sans mt-0.5">
                                    Class: <span className="text-slate-300 font-semibold">{node.enclosing_class}</span>
                                  </div>
                                )}
                              </div>

                              {/* Action buttons */}
                              <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleOpenSource(node.file_path, node.start_line);
                                  }}
                                  title="View source code at line"
                                  className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-cyan-300"
                                >
                                  <FileCode className="w-3.5 h-3.5" />
                                </button>
                                {!isRoot && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setSelectedFunctionId(node.id);
                                    }}
                                    title="Set as exploration root"
                                    className="p-1 rounded bg-slate-800 hover:bg-cyan-900 text-slate-400 hover:text-cyan-200 text-[10px] font-bold"
                                  >
                                    Focus
                                  </button>
                                )}
                              </div>
                            </div>

                            {/* Location & Lines */}
                            <div className="flex items-center gap-2 text-[11px] text-slate-400 mb-2 font-mono">
                              <span className="truncate max-w-[180px]" title={node.file_path}>
                                {node.file_path.split('/').pop()}
                              </span>
                              <span className="text-slate-600">·</span>
                              <span className="text-slate-400">L{node.start_line}–L{node.end_line}</span>
                            </div>

                            {/* Parameters summary */}
                            {node.parameters.length > 0 && (
                              <div className="text-[10px] text-slate-500 font-mono mb-2 truncate">
                                ({node.parameters.map((p) => p.name).join(', ')})
                              </div>
                            )}

                            {/* Node Footer: Caller / Callee counts */}
                            <div className="flex items-center justify-between text-[10px] pt-2 border-t border-slate-800/80 text-slate-400">
                              <span className="flex items-center gap-1">
                                <CornerDownRight className="w-3 h-3 text-fuchsia-400" />
                                {node.callee_count} calls
                              </span>
                              <span className="flex items-center gap-1">
                                <CornerUpLeft className="w-3 h-3 text-violet-400" />
                                {node.caller_count} callers
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              {/* Explicit Directed Call Relationships List */}
              <div className="mt-8 pt-4 border-t border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Directed Call Sites & Branch Conditions ({displayedEdges.length})
                  </h4>
                  <span className="text-[11px] text-slate-500">
                    Static Lexical Ordering
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {displayedEdges.map((edge, idx) => {
                    const isEdgeActive = activePathEdges.has(`${edge.caller_id}->${edge.callee_id || edge.callee_symbol_name}:${edge.call_site_line}`);
                    return (
                      <div
                        key={idx}
                        className={`p-2.5 rounded-lg border text-xs transition-colors ${
                          isEdgeActive
                            ? 'bg-slate-900 border-cyan-700/80 text-slate-200 shadow-md'
                            : 'bg-slate-900/30 border-slate-800/70 text-slate-400 hover:bg-slate-900/60'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-1 mb-1 font-mono">
                          <span className="text-slate-300 font-semibold truncate max-w-[120px]" title={edge.caller_name}>
                            {edge.caller_name}()
                          </span>
                          <span className="text-slate-600">→</span>
                          <span className="text-cyan-400 font-semibold truncate max-w-[120px]" title={edge.callee_raw_name}>
                            {edge.callee_symbol_name}()
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] text-slate-500">
                          <span>Line {edge.call_site_line}</span>
                          <div className="flex items-center gap-1">
                            {edge.branch_condition ? (
                              <span className="px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800 truncate max-w-[120px]">
                                {edge.branch_condition}
                              </span>
                            ) : edge.is_conditional ? (
                              <span className="px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800">
                                branch
                              </span>
                            ) : null}
                            {edge.is_async && (
                              <span className="px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                                await
                              </span>
                            )}
                            {edge.is_recursive && (
                              <span className="px-1.5 py-0.2 rounded bg-rose-950 text-rose-300 border border-rose-800">
                                recursive
                              </span>
                            )}
                            {edge.is_external && (
                              <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                                external
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Side Panel: Function Details & Grounded Explanation */}
        <div className="w-96 flex-shrink-0 border-l border-slate-800 bg-slate-950/70 flex flex-col min-h-0 overflow-hidden shadow-2xl">
          {/* Panel Header & Tabs */}
          <div className="flex-shrink-0 px-4 pt-3 pb-2 border-b border-slate-800 bg-slate-900/60">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                Function Inspector
              </span>
              {inspectedNode && (
                <button
                  onClick={() => handleOpenSource(inspectedNode.file_path, inspectedNode.start_line)}
                  className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:border-cyan-700"
                >
                  <FileCode className="w-3 h-3 text-cyan-400" />
                  <span>View Code</span>
                </button>
              )}
            </div>

            {/* Sub-tabs */}
            <div className="flex items-center bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs">
              <button
                onClick={() => setActiveInspectorTab('explanation')}
                className={`flex-1 py-1 rounded text-center font-medium transition-colors ${
                  activeInspectorTab === 'explanation'
                    ? 'bg-slate-800 text-cyan-300 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Grounded Explanation
              </button>
              <button
                onClick={() => setActiveInspectorTab('details')}
                className={`flex-1 py-1 rounded text-center font-medium transition-colors ${
                  activeInspectorTab === 'details'
                    ? 'bg-slate-800 text-cyan-300 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Parameters & Meta
              </button>
              <button
                onClick={() => setActiveInspectorTab('calls')}
                className={`flex-1 py-1 rounded text-center font-medium transition-colors ${
                  activeInspectorTab === 'calls'
                    ? 'bg-slate-800 text-cyan-300 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Calls Breakdown
              </button>
            </div>
          </div>

          {/* Panel Content Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {inspectedNode ? (
              <>
                {/* Active Function Card */}
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold font-mono text-cyan-300">{inspectedNode.name}()</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      {inspectedNode.language}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 truncate" title={inspectedNode.file_path}>
                    {inspectedNode.file_path}:L{inspectedNode.start_line}-L{inspectedNode.end_line}
                  </div>
                  {inspectedNode.enclosing_class && (
                    <div className="text-[11px] text-slate-400">
                      Enclosing Class: <span className="text-slate-200 font-semibold">{inspectedNode.enclosing_class}</span>
                    </div>
                  )}
                </div>

                {/* Tab: Grounded Explanation */}
                {activeInspectorTab === 'explanation' && (
                  <div className="space-y-4">
                    {/* Function Role / Summary */}
                    <div className="space-y-1">
                      <h5 className="font-bold text-slate-300 flex items-center gap-1.5">
                        <Info className="w-3.5 h-3.5 text-cyan-400" />
                        What does this function do?
                      </h5>
                      <p className="text-slate-400 leading-relaxed bg-slate-900/30 p-2.5 rounded-lg border border-slate-800/80">
                        {callGraphData?.explanation?.summary || 'No docstring or implementation summary available.'}
                      </p>
                    </div>

                    {/* Control Flow Narrative & Lexical Order */}
                    <div className="space-y-1">
                      <h5 className="font-bold text-slate-300 flex items-center gap-1.5">
                        <GitFork className="w-3.5 h-3.5 text-amber-400" />
                        Control Flow & Call Order
                      </h5>
                      <p className="text-slate-400 leading-relaxed bg-slate-900/30 p-2.5 rounded-lg border border-slate-800/80">
                        {callGraphData?.explanation?.control_flow_narrative}
                      </p>
                    </div>

                    {/* Static Analysis Limitations */}
                    <div className="space-y-1">
                      <h5 className="font-bold text-slate-400 flex items-center gap-1.5 text-[11px]">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        Verification Bounds & Limitations
                      </h5>
                      <p className="text-[11px] text-slate-500 leading-normal bg-slate-900/20 p-2.5 rounded-lg border border-slate-800/60">
                        {callGraphData?.explanation?.static_limitations}
                      </p>
                    </div>

                    {/* Components Involved */}
                    {callGraphData?.explanation?.components_involved && callGraphData.explanation.components_involved.length > 0 && (
                      <div className="space-y-1.5">
                        <h5 className="font-bold text-slate-300">Components Involved</h5>
                        <div className="space-y-1 font-mono text-[10px]">
                          {callGraphData.explanation.components_involved.map((file, idx) => (
                            <div key={idx} className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-400 truncate" title={file}>
                              {file}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab: Parameters & Meta */}
                {activeInspectorTab === 'details' && (
                  <div className="space-y-4">
                    {/* Parameters Table */}
                    <div className="space-y-2">
                      <h5 className="font-bold text-slate-300">Parameters ({inspectedNode.parameters.length})</h5>
                      {inspectedNode.parameters.length === 0 ? (
                        <p className="text-slate-500 text-xs">This function takes no parameters.</p>
                      ) : (
                        <div className="space-y-1.5">
                          {inspectedNode.parameters.map((p, idx) => (
                            <div key={idx} className="p-2 rounded-lg bg-slate-900/80 border border-slate-800 text-xs flex items-center justify-between font-mono">
                              <span className="text-slate-200 font-semibold">{p.name}</span>
                              <div className="text-[11px] text-slate-400">
                                {p.type_annotation ? (
                                  <span className="text-cyan-400">: {p.type_annotation}</span>
                                ) : (
                                  <span className="text-slate-500">any</span>
                                )}
                                {p.default_value && (
                                  <span className="text-amber-400 ml-1">= {p.default_value}</span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Docstring */}
                    {inspectedNode.docstring && (
                      <div className="space-y-1.5">
                        <h5 className="font-bold text-slate-300">Docstring</h5>
                        <pre className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 whitespace-pre-wrap font-mono">
                          {inspectedNode.docstring}
                        </pre>
                      </div>
                    )}

                    {/* Decorators */}
                    {inspectedNode.decorators.length > 0 && (
                      <div className="space-y-1.5">
                        <h5 className="font-bold text-slate-300">Decorators</h5>
                        <div className="flex flex-wrap gap-1">
                          {inspectedNode.decorators.map((d, idx) => (
                            <span key={idx} className="px-2 py-0.5 rounded bg-violet-950/60 border border-violet-800 text-violet-300 font-mono text-[11px]">
                              @{d}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab: Calls Breakdown */}
                {activeInspectorTab === 'calls' && (
                  <div className="space-y-4">
                    {/* Outgoing Calls */}
                    <div className="space-y-2">
                      <h5 className="font-bold text-slate-300 flex items-center gap-1.5">
                        <CornerDownRight className="w-3.5 h-3.5 text-fuchsia-400" />
                        Outgoing Calls ({inspectedNode.callee_count})
                      </h5>
                      {callGraphData?.explanation?.outgoing_calls_breakdown?.length ? (
                        <div className="space-y-1.5">
                          {callGraphData.explanation.outgoing_calls_breakdown.map((item, idx) => (
                            <div key={idx} className="p-2 rounded-lg bg-slate-900 border border-slate-800 space-y-0.5">
                              <div className="flex items-center justify-between font-mono text-xs">
                                <span className="font-bold text-fuchsia-300">#{item.order} {item.callee}()</span>
                                <span className="text-[10px] text-slate-500">Line {item.line}</span>
                              </div>
                              <p className="text-[11px] text-slate-400 leading-normal">
                                {item.execution_nature}
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-500 text-xs">No direct outgoing calls detected.</p>
                      )}
                    </div>

                    {/* Incoming Callers */}
                    <div className="space-y-2">
                      <h5 className="font-bold text-slate-300 flex items-center gap-1.5">
                        <CornerUpLeft className="w-3.5 h-3.5 text-violet-400" />
                        Incoming Callers ({inspectedNode.caller_count})
                      </h5>
                      {callGraphData?.explanation?.incoming_callers?.length ? (
                        <div className="space-y-1.5">
                          {callGraphData.explanation.incoming_callers.map((item, idx) => (
                            <div key={idx} className="p-2 rounded-lg bg-slate-900 border border-slate-800 space-y-0.5">
                              <div className="flex items-center justify-between font-mono text-xs">
                                <span className="font-bold text-violet-300">{item.caller}()</span>
                                <span className="text-[10px] text-slate-500">Line {item.line}</span>
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono truncate" title={item.file}>
                                {item.file} ({item.condition})
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-500 text-xs">No repository callers detected (entrypoint function).</p>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-center p-6">
                Select a function node on the canvas to view detailed execution traces and evidence.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Code Viewer Modal */}
      {isCodeModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-6">
          <div className="w-full max-w-5xl h-[85vh] bg-slate-950 rounded-2xl border border-slate-800 flex flex-col overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-900/60 flex-shrink-0">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-cyan-400" />
                <span className="text-sm font-bold text-slate-100 font-mono">
                  {codeModalFile?.path || 'Source Viewer'}
                </span>
                <span className="text-xs text-slate-500">
                  (Target: Line {codeModalLine})
                </span>
              </div>
              <button
                onClick={() => setIsCodeModalOpen(false)}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 min-h-0 p-4">
              {isLoadingCode ? (
                <div className="h-full flex flex-col items-center justify-center gap-3">
                  <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
                  <p className="text-sm text-slate-400">Loading source file…</p>
                </div>
              ) : (
                <CodeViewer file={codeModalFile} highlightLine={codeModalLine} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
