import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderGit2,
  FileCode2,
  Layers,
  Bot,
  Plus,
  ArrowRight,
  MessageSquareCode,
  FolderTree,
  Sparkles,
  GitBranch,
  Network,
  BarChart3,
  Send,
  Clock,
  Info,
  CheckCircle2,
  ShieldCheck,
  Award,
  Zap,
  Activity,
  Cpu,
  RefreshCw,
  Search,
  BookOpen,
} from 'lucide-react';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Repository, CodeEntity } from '../types/repository';
import { EngineeringTask } from '../types/task';
import { BenchmarkData } from '../types/changes';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Spinner } from '../components/common/Spinner';
import { RepoConnectorModal } from '../components/repository/RepoConnectorModal';
import { MermaidViewer } from '../components/diagrams/MermaidViewer';
import { CitationBadge } from '../components/chat/CitationBadge';
import { chatService } from '../services/chatService';
import { taskService } from '../services/taskService';
import { repositoryService } from '../services/repositoryService';
import { researchService } from '../services/researchService';

interface DashboardPageProps {
  repositories: Repository[];
  selectedRepo: Repository | null;
  onSelectRepo: (repo: Repository) => void;
  onConnectRepo: (url: string, branch?: string) => Promise<void>;
  isLoading: boolean;
}

const AGENTS_LIST = [
  { name: 'Orchestrator', role: 'Workflow routing, complexity classification & retry state machine', icon: Bot, status: 'Active' },
  { name: 'Requirement Agent', role: 'Decomposes prompt into formal objectives & constraints', icon: Sparkles, status: 'Active' },
  { name: 'Repository Agent', role: 'Full-repository topology scanning & file metadata indexing', icon: FolderGit2, status: 'Active' },
  { name: 'Code Understanding', role: 'Extracts AST symbols, functions, classes & API endpoints', icon: FolderTree, status: 'Active' },
  { name: 'Design Agent', role: 'Generates software architecture & implementation blueprints', icon: Layers, status: 'Active' },
  { name: 'Diagram Agent', role: 'Synthesizes Mermaid component & sequence flow visualizations', icon: Network, status: 'Active' },
  { name: 'Code Generation', role: 'Multi-file code synthesis & precision AST modifications', icon: FileCode2, status: 'Active' },
  { name: 'Test Generation', role: 'Synthesizes pytest/unit tests with high coverage', icon: CheckCircle2, status: 'Active' },
  { name: 'Documentation', role: 'Generates SDD specifications and API docstrings', icon: Info, status: 'Active' },
  { name: 'Validation Agent', role: 'AST syntax verification, dependency and test validation', icon: Zap, status: 'Active' },
  { name: 'Review Agent', role: 'Comprehensive quality, security and maintainability audit', icon: ShieldCheck, status: 'Active' },
  { name: 'Workspace Manager', role: 'Sandbox isolation & zero-risk staging before approval', icon: Cpu, status: 'Active' },
];

const SAMPLE_QUESTIONS = [
  'How does authentication work in this repository?',
  'Where is the database connection initialized?',
  'Explain the overall architecture and main entrypoints.',
];

const SAMPLE_TASKS = [
  'Add JWT authentication, create tests, and update documentation.',
  'Generate comprehensive unit tests for core services.',
  'Create user registration API endpoint with password hashing.',
];

export const DashboardPage: React.FC<DashboardPageProps> = ({
  repositories,
  selectedRepo,
  onSelectRepo,
  onConnectRepo,
  isLoading,
}) => {
  const navigate = useNavigate();
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);

  // Quick Chat State
  const [chatQuery, setChatQuery] = useState('');
  const [chatAnswer, setChatAnswer] = useState<{
    answer: string;
    citations: any[];
    latency: number;
  } | null>(null);
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Quick Task State
  const [taskRequirement, setTaskRequirement] = useState('');
  const [isTaskSubmitting, setIsTaskSubmitting] = useState(false);
  const [recentTasks, setRecentTasks] = useState<EngineeringTask[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);

  // Code Explorer & AST Symbols State
  const [symbols, setSymbols] = useState<CodeEntity[]>([]);
  const [isLoadingSymbols, setIsLoadingSymbols] = useState(false);

  // Architecture Diagram State
  const [diagram, setDiagram] = useState<{ mermaid_code: string; description: string } | null>(null);
  const [isLoadingDiagram, setIsLoadingDiagram] = useState(false);

  // Benchmark State
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData | null>(null);

  const totalFiles = repositories.reduce((acc, r) => acc + (r.total_files || 0), 0);
  const totalLines = repositories.reduce((acc, r) => acc + (r.total_lines || 0), 0);

  // Load contextual data whenever selectedRepo changes
  useEffect(() => {
    if (!selectedRepo) return;

    // Load recent tasks for selected repo
    const loadTasks = async () => {
      setIsLoadingTasks(true);
      try {
        const tasks = await taskService.listForRepo(selectedRepo.id);
        setRecentTasks(tasks.slice(0, 5));
      } catch (err) {
        console.error('Failed to load dashboard tasks:', err);
      } finally {
        setIsLoadingTasks(false);
      }
    };

    // Load AST symbols
    const loadSymbols = async () => {
      setIsLoadingSymbols(true);
      try {
        const entities = await repositoryService.getEntities(selectedRepo.id);
        setSymbols(entities);
      } catch (err) {
        console.error('Failed to load dashboard symbols:', err);
      } finally {
        setIsLoadingSymbols(false);
      }
    };

    // Load Architecture Diagram
    const loadArchitecture = async () => {
      setIsLoadingDiagram(true);
      try {
        const arch = await repositoryService.getArchitecture(selectedRepo.id);
        setDiagram(arch);
      } catch (err) {
        console.error('Failed to load dashboard architecture:', err);
      } finally {
        setIsLoadingDiagram(false);
      }
    };

    loadTasks();
    loadSymbols();
    loadArchitecture();
  }, [selectedRepo]);

  // Load Research Benchmarks once
  useEffect(() => {
    const loadBenchmarks = async () => {
      try {
        const res = await researchService.getBenchmarks();
        setBenchmarkData(res);
      } catch (err) {
        console.error('Failed to load benchmark data:', err);
      }
    };
    loadBenchmarks();
  }, []);

  // Handle Quick Chat
  const handleQuickAsk = async (queryText?: string) => {
    const query = queryText || chatQuery;
    if (!query.trim() || !selectedRepo || isChatLoading) return;

    setIsChatLoading(true);
    try {
      const resp = await chatService.askQuestion(selectedRepo.id, query.trim());
      setChatAnswer({
        answer: resp.answer,
        citations: resp.citations || [],
        latency: resp.latency_seconds,
      });
      setChatQuery('');
    } catch (err: any) {
      setChatAnswer({
        answer: `Error: ${err.message || 'Failed to query codebase'}`,
        citations: [],
        latency: 0,
      });
    } finally {
      setIsChatLoading(false);
    }
  };

  // Handle Quick Task Execution
  const handleQuickTask = async (reqText?: string) => {
    const text = reqText || taskRequirement;
    if (!text.trim() || !selectedRepo || isTaskSubmitting) return;

    setIsTaskSubmitting(true);
    try {
      const newTask = await taskService.create(selectedRepo.id, text.trim(), 'auto');
      setTaskRequirement('');
      setRecentTasks((prev) => [newTask, ...prev.filter((t) => t.id !== newTask.id)]);
      // Navigate to tasks studio to watch execution live
      navigate('/tasks');
    } catch (err) {
      console.error('Failed to launch task from dashboard:', err);
    } finally {
      setIsTaskSubmitting(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Banner / Hero Hub */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/50 border border-cyan-500/20 p-6 md:p-8 rounded-2xl shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="space-y-2 relative z-10">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
              <Sparkles className="w-5 h-5 text-cyan-400" />
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-slate-100 tracking-tight">
              Engineering Intelligence Hub
            </h2>
            <Badge variant="cyan" size="sm">
              12-Agent System
            </Badge>
          </div>
          <p className="text-xs md:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Unified autonomous agentic platform. Grounded RAG code intelligence, automated test & SDD generation, live architecture topology, and human-in-the-loop change gating.
          </p>

          {selectedRepo && (
            <div className="flex items-center gap-2 pt-2 text-xs font-mono text-cyan-300">
              <span className="text-slate-500">Active Repository:</span>
              <span className="bg-cyan-950/80 px-2.5 py-1 rounded-md border border-cyan-800/80 font-bold flex items-center gap-1.5">
                <FolderGit2 className="w-3.5 h-3.5 text-cyan-400" />
                {selectedRepo.owner}/{selectedRepo.name}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 relative z-10 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/repositories')}
            leftIcon={<FolderGit2 className="w-4 h-4" />}
          >
            Manage Repos
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setIsConnectModalOpen(true)}
          >
            Connect Repository
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card glass-card-hover p-5 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 to-blue-500 opacity-80" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Connected Repos</span>
            <div className="p-2 rounded-xl bg-cyan-950/70 border border-cyan-500/30 text-cyan-400 shadow-[0_0_12px_-3px_rgba(6,182,212,0.3)]">
              <FolderGit2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">{repositories.length}</div>
        </div>

        <div className="glass-card glass-card-hover p-5 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-500 opacity-80" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Indexed Files</span>
            <div className="p-2 rounded-xl bg-blue-950/70 border border-blue-500/30 text-blue-400 shadow-[0_0_12px_-3px_rgba(59,130,246,0.3)]">
              <FileCode2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">{totalFiles.toLocaleString()}</div>
        </div>

        <div className="glass-card glass-card-hover p-5 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-pink-500 opacity-80" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Lines of Code</span>
            <div className="p-2 rounded-xl bg-purple-950/70 border border-purple-500/30 text-purple-400 shadow-[0_0_12px_-3px_rgba(168,85,247,0.3)]">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">{totalLines.toLocaleString()}</div>
        </div>

        <div className="glass-card glass-card-hover p-5 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-500 opacity-80" />
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Autonomous Agents</span>
            <div className="p-2 rounded-xl bg-emerald-950/70 border border-emerald-500/30 text-emerald-400 shadow-[0_0_12px_-3px_rgba(16,185,129,0.3)]">
              <Bot className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400 tracking-tight flex items-center gap-2">
            <span>12 Online</span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
        </div>
      </div>

      {/* Quick-Action Feature Launcher Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Platform Capabilities & Quick Launch
          </h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          <button
            onClick={() => navigate('/documentation')}
            className="glass-card glass-card-hover p-4 rounded-2xl text-left group flex flex-col justify-between space-y-3 cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 bg-cyan-950/80 rounded-xl border border-cyan-500/30 text-cyan-400 group-hover:scale-110 transition-transform shadow-[0_0_12px_-3px_rgba(6,182,212,0.3)]">
                <BookOpen className="w-4 h-4" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">Doc Intelligence</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">AST verified docs & sync</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/tasks')}
            className="glass-card glass-card-hover p-4 rounded-2xl text-left group flex flex-col justify-between space-y-3 cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 bg-cyan-950/80 rounded-xl border border-cyan-500/30 text-cyan-400 group-hover:scale-110 transition-transform shadow-[0_0_12px_-3px_rgba(6,182,212,0.3)]">
                <Bot className="w-4 h-4" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200 group-hover:text-cyan-300 transition-colors">Engineering Studio</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">Autonomous task execution & approvals</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/chat')}
            className="glass-card glass-card-hover p-4 rounded-2xl text-left group flex flex-col justify-between space-y-3 cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 bg-blue-950/80 rounded-xl border border-blue-500/30 text-blue-400 group-hover:scale-110 transition-transform shadow-[0_0_12px_-3px_rgba(59,130,246,0.3)]">
                <MessageSquareCode className="w-4 h-4" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200 group-hover:text-blue-300 transition-colors">AI Chat & RAG</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">Grounded Q&A with line citations</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/explorer')}
            className="glass-card glass-card-hover p-4 rounded-2xl text-left group flex flex-col justify-between space-y-3 cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 bg-purple-950/80 rounded-xl border border-purple-500/30 text-purple-400 group-hover:scale-110 transition-transform shadow-[0_0_12px_-3px_rgba(168,85,247,0.3)]">
                <FolderTree className="w-4 h-4" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200 group-hover:text-purple-300 transition-colors">Code Explorer</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">AST symbols & code tree inspector</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/architecture')}
            className="glass-card glass-card-hover p-4 rounded-2xl text-left group flex flex-col justify-between space-y-3 cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 bg-emerald-950/80 rounded-xl border border-emerald-500/30 text-emerald-400 group-hover:scale-110 transition-transform shadow-[0_0_12px_-3px_rgba(16,185,129,0.3)]">
                <Network className="w-4 h-4" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-200 group-hover:text-emerald-300 transition-colors">Architecture</h4>
              <p className="text-[11px] text-slate-400 mt-0.5">Mermaid dependency topology</p>
            </div>
          </button>
        </div>
      </div>

      {/* Main 2-Column Interactive Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Quick Q&A & Autonomous Tasks Studio Widget */}
        <div className="lg:col-span-7 space-y-6">
          {/* Module 1: Grounded AI Codebase Ask Widget */}
          <div className="glass-card p-6 rounded-2xl shadow-xl space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-cyan-950/70 border border-cyan-500/30 rounded-xl text-cyan-400 shadow-[0_0_12px_-3px_rgba(6,182,212,0.3)]">
                  <MessageSquareCode className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">
                    Instant Codebase Q&A (RAG Assistant)
                  </h3>
                  <p className="text-[11px] text-slate-400">Contextual answers grounded in indexed AST code chunks</p>
                </div>
              </div>
              <button
                onClick={() => navigate('/chat')}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors px-2.5 py-1 rounded-lg hover:bg-cyan-950/40"
              >
                <span>Full Chat Studio</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleQuickAsk();
              }}
              className="relative"
            >
              <input
                type="text"
                placeholder={
                  selectedRepo
                    ? `Ask anything about ${selectedRepo.name} (e.g. 'Where is auth handled?')...`
                    : 'Connect a repo to ask questions...'
                }
                className="w-full bg-slate-950/90 border border-slate-750/90 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 rounded-xl pl-4 pr-24 py-3 text-xs md:text-sm text-slate-100 placeholder-slate-500 transition-all shadow-inner"
                value={chatQuery}
                onChange={(e) => setChatQuery(e.target.value)}
                disabled={!selectedRepo || isChatLoading}
              />
              <div className="absolute right-1.5 top-1.5">
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={!chatQuery.trim() || isChatLoading || !selectedRepo}
                  isLoading={isChatLoading}
                  rightIcon={<Send className="w-3.5 h-3.5" />}
                >
                  Ask
                </Button>
              </div>
            </form>

            {/* Quick Sample Prompts */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] text-slate-500 font-medium">Try:</span>
              {SAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleQuickAsk(q)}
                  disabled={!selectedRepo || isChatLoading}
                  className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-750/80 hover:border-cyan-500/40 transition-all cursor-pointer shadow-sm disabled:opacity-40"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Live Chat Answer Area */}
            {chatAnswer && (
              <div className="p-4 bg-slate-950/90 rounded-xl border border-slate-800/90 space-y-3 animate-fade-in shadow-inner">
                <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-850">
                  <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Grounded Answer</span>
                  </div>
                  {chatAnswer.latency > 0 && (
                    <div className="flex items-center gap-1 font-mono text-[11px] bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      <Clock className="w-3 h-3 text-cyan-400" />
                      <span>{chatAnswer.latency}s</span>
                    </div>
                  )}
                </div>

                <div className="prose prose-invert prose-xs max-w-none text-slate-300 leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{chatAnswer.answer}</ReactMarkdown>
                </div>

                {chatAnswer.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-850">
                    <div className="text-[11px] font-semibold text-slate-400 mb-1.5">
                      Verified Citations:
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {chatAnswer.citations.map((c, idx) => (
                        <CitationBadge key={idx} citation={c} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Module 2: Autonomous Engineering Task Launcher & Recent Pipeline */}
          <div className="glass-card p-6 rounded-2xl shadow-xl space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-emerald-950/70 border border-emerald-500/30 rounded-xl text-emerald-400 shadow-[0_0_12px_-3px_rgba(16,185,129,0.3)]">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">
                    Autonomous Engineering Studio
                  </h3>
                  <p className="text-[11px] text-slate-400">Multi-agent code generation, testing & validation sandbox</p>
                </div>
              </div>
              <button
                onClick={() => navigate('/tasks')}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors px-2.5 py-1 rounded-lg hover:bg-cyan-950/40"
              >
                <span>Full Studio</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder={
                  selectedRepo
                    ? `Enter task for ${selectedRepo.name} (e.g. 'Add JWT auth and tests')...`
                    : 'Connect a repo to launch tasks...'
                }
                className="flex-1 bg-slate-950/90 border border-slate-750/90 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 rounded-xl px-4 py-3 text-xs md:text-sm text-slate-100 placeholder-slate-500 transition-all shadow-inner"
                value={taskRequirement}
                onChange={(e) => setTaskRequirement(e.target.value)}
                disabled={!selectedRepo || isTaskSubmitting}
              />
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleQuickTask()}
                isLoading={isTaskSubmitting}
                disabled={!taskRequirement.trim() || !selectedRepo}
                rightIcon={<Send className="w-3.5 h-3.5" />}
              >
                Launch
              </Button>
            </div>

            {/* Quick Task Prompt Chips */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] text-slate-500 font-medium">Presets:</span>
              {SAMPLE_TASKS.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleQuickTask(prompt)}
                  disabled={!selectedRepo || isTaskSubmitting}
                  className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-cyan-300 border border-slate-750/80 hover:border-cyan-500/40 transition-all cursor-pointer shadow-sm disabled:opacity-40"
                >
                  {prompt}
                </button>
              ))}
            </div>

            {/* Recent Tasks List */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                <span>Recent Autonomous Tasks</span>
                <span className="font-mono text-cyan-400">{recentTasks.length} recorded</span>
              </div>

              {isLoadingTasks ? (
                <div className="py-6 flex justify-center">
                  <Spinner size="sm" />
                </div>
              ) : recentTasks.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-2">
                  No engineering tasks executed yet for this repo.
                </p>
              ) : (
                <div className="space-y-2">
                  {recentTasks.map((task) => (
                    <div
                      key={task.id}
                      onClick={() => navigate('/tasks')}
                      className="p-3 bg-slate-950/70 hover:bg-slate-900 border border-slate-800/80 hover:border-cyan-500/40 rounded-xl transition-all flex items-center justify-between gap-3 cursor-pointer group shadow-sm hover:translate-x-0.5"
                    >
                      <div className="space-y-1 min-w-0">
                        <div className="text-xs font-medium text-slate-200 group-hover:text-cyan-300 truncate">
                          {task.requirement}
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
                          <span>Workflow: {task.workflow_type}</span>
                          <span>•</span>
                          <span>Retries: {task.retry_count}</span>
                        </div>
                      </div>

                      <Badge
                        variant={
                          task.status === 'approved' || task.status === 'completed'
                            ? 'success'
                            : task.status === 'waiting_approval'
                              ? 'cyan'
                              : task.status === 'running'
                                ? 'info'
                                : 'default'
                        }
                        size="sm"
                        dot={task.status === 'running'}
                      >
                        {task.status.toUpperCase()}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Codebase AST Symbols, Architecture & Evaluation */}
        <div className="lg:col-span-5 space-y-6">
          {/* Module 3: AST Code Intelligence & Symbols Preview */}
          <div className="glass-card p-6 rounded-2xl shadow-xl space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-purple-950/70 border border-purple-500/30 rounded-xl text-purple-400 shadow-[0_0_12px_-3px_rgba(168,85,247,0.3)]">
                  <FolderTree className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">
                    AST Code Intelligence
                  </h3>
                  <p className="text-[11px] text-slate-400">Extracted functions, classes & symbols</p>
                </div>
              </div>
              <button
                onClick={() => navigate('/explorer')}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors px-2.5 py-1 rounded-lg hover:bg-cyan-950/40"
              >
                <span>Explorer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {isLoadingSymbols ? (
              <div className="py-6 flex justify-center">
                <Spinner size="sm" />
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between bg-slate-950/80 p-3 rounded-xl border border-slate-800 text-xs">
                  <span className="text-slate-400">Total Extracted Symbols:</span>
                  <span className="font-mono font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60">{symbols.length}</span>
                </div>

                {symbols.length > 0 ? (
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {symbols.slice(0, 6).map((sym) => (
                      <div
                        key={sym.id}
                        onClick={() => navigate('/explorer')}
                        className="p-2.5 bg-slate-950/60 hover:bg-slate-900 border border-slate-800/80 hover:border-purple-500/40 rounded-xl text-xs flex items-center justify-between cursor-pointer group transition-all"
                      >
                        <div className="truncate mr-2">
                          <span className="font-mono text-slate-200 group-hover:text-purple-300 transition-colors font-medium">
                            {sym.name}
                          </span>
                          <span className="text-[10px] text-slate-500 block truncate font-mono">
                            {sym.file_path}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800 flex-shrink-0">
                          {sym.entity_type}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No AST symbols parsed yet.</p>
                )}
              </div>
            )}
          </div>

          {/* Module 4: Architecture Topology Preview */}
          <div className="glass-card p-6 rounded-2xl shadow-xl space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-emerald-950/70 border border-emerald-500/30 rounded-xl text-emerald-400 shadow-[0_0_12px_-3px_rgba(16,185,129,0.3)]">
                  <Network className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">
                    Architecture Topology
                  </h3>
                  <p className="text-[11px] text-slate-400">Live synthesized Mermaid diagram</p>
                </div>
              </div>
              <button
                onClick={() => navigate('/architecture')}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors px-2.5 py-1 rounded-lg hover:bg-cyan-950/40"
              >
                <span>Full Graph</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {isLoadingDiagram ? (
              <div className="py-12 flex justify-center">
                <Spinner size="md" />
              </div>
            ) : diagram ? (
              <div className="space-y-2">
                <div className="bg-slate-950/80 rounded-xl p-2 border border-slate-800/80">
                  <MermaidViewer chart={diagram.mermaid_code} />
                </div>
                <p className="text-[11px] text-slate-400 italic text-center">
                  {diagram.description}
                </p>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-4 text-center">
                Select a repository to render its architecture topology.
              </p>
            )}
          </div>

          {/* Module 5: Empirical Benchmark & Research Insights */}
          {benchmarkData && (
            <div className="glass-card p-6 rounded-2xl shadow-xl space-y-4 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-amber-950/70 border border-amber-500/30 rounded-xl text-amber-400 shadow-[0_0_12px_-3px_rgba(245,158,11,0.3)]">
                    <BarChart3 className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">
                      Multi-Agent Benchmark
                    </h3>
                    <p className="text-[11px] text-slate-400">Empirical validation & performance</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-950/90 rounded-xl border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400">Single-Agent Pass Rate</div>
                  <div className="text-lg font-bold font-mono text-slate-200">
                    {benchmarkData.single_agent_metrics.validation_pass_rate}%
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Avg Latency: {benchmarkData.single_agent_metrics.avg_latency_seconds}s
                  </div>
                </div>

                <div className="p-3 bg-cyan-950/30 rounded-xl border border-cyan-500/30 space-y-1">
                  <div className="text-[11px] text-cyan-300 font-medium">Multi-Agent Pass Rate</div>
                  <div className="text-lg font-bold font-mono text-emerald-400">
                    {benchmarkData.multi_agent_metrics.validation_pass_rate}%
                  </div>
                  <div className="text-[10px] text-cyan-400 font-mono">
                    Security Score: {benchmarkData.multi_agent_metrics.avg_security_score}/100
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Autonomous Agent Fleet 12-Agent Fleet Monitor */}
      <div className="glass-card p-6 rounded-2xl shadow-xl space-y-4 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-cyan-950/70 border border-cyan-500/30 rounded-xl text-cyan-400 shadow-[0_0_12px_-3px_rgba(6,182,212,0.3)]">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">
                Autonomous Agent Fleet
              </h3>
              <p className="text-xs text-slate-400">12 specialized autonomous engineering subagents</p>
            </div>
          </div>
          <span className="text-xs font-mono text-emerald-300 bg-emerald-950/60 border border-emerald-500/30 px-3 py-1 rounded-full flex items-center gap-2 shadow-[0_0_12px_-3px_rgba(16,185,129,0.2)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-sans text-xs font-medium">Operational</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3.5">
          {AGENTS_LIST.map((agent, i) => {
            const Icon = agent.icon;
            return (
              <div
                key={i}
                className="p-3.5 bg-slate-950/70 hover:bg-slate-900 border border-slate-800/80 hover:border-cyan-500/30 rounded-xl transition-all duration-200 space-y-2 group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1 rounded-lg bg-slate-900 text-cyan-400 group-hover:text-cyan-300 group-hover:scale-105 transition-all">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-bold text-slate-200 group-hover:text-cyan-200 transition-colors">{agent.name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-300 bg-emerald-950/80 px-2 py-0.5 rounded-full border border-emerald-800/70">
                    {agent.status}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-normal">{agent.role}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Connected Repositories Grid Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-100">Connected Repositories</h3>
            <p className="text-xs text-slate-400">Repositories indexed into vector store and AST topology</p>
          </div>
          <button
            onClick={() => navigate('/repositories')}
            className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors px-2.5 py-1 rounded-lg hover:bg-cyan-950/40"
          >
            <span>View all in detail</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {repositories.length === 0 ? (
          <div className="p-12 text-center glass-card border-dashed border-slate-750 rounded-2xl space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-cyan-950/60 border border-cyan-500/20 flex items-center justify-center mx-auto text-cyan-400">
              <FolderGit2 className="w-7 h-7" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-200">No repositories connected</h4>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Connect a public GitHub repository or use one of the presets to begin exploring and building.
              </p>
            </div>
            <Button variant="primary" size="sm" onClick={() => setIsConnectModalOpen(true)}>
              Connect First Repository
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {repositories.map((repo) => {
              const isSelected = selectedRepo?.id === repo.id;
              return (
                <div
                  key={repo.id}
                  onClick={() => onSelectRepo(repo)}
                  className={`p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 cursor-pointer glass-card ${isSelected
                      ? 'border-cyan-500/60 shadow-xl shadow-cyan-950/60 ring-1 ring-cyan-500/40 -translate-y-0.5'
                      : 'border-slate-800/80 hover:border-slate-700 hover:-translate-y-0.5'
                    }`}
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 truncate">
                        <div className="p-1.5 rounded-lg bg-cyan-950/60 text-cyan-400 border border-cyan-500/20">
                          <FolderGit2 className="w-4 h-4 flex-shrink-0" />
                        </div>
                        <h4 className="text-sm font-bold text-slate-100 truncate">
                          {repo.owner}/{repo.name}
                        </h4>
                      </div>
                      <Badge variant={repo.status === 'indexed' ? 'success' : 'info'} dot>
                        {repo.status.toUpperCase()}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                      <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{repo.default_branch}</span>
                      <span>•</span>
                      <span>{repo.total_files} files</span>
                      <span>•</span>
                      <span>{repo.total_lines} lines</span>
                    </div>

                    {/* Language distribution badges */}
                    {Object.keys(repo.languages || {}).length > 0 && (
                      <div className="pt-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {Object.entries(repo.languages).slice(0, 3).map(([lang, lines]) => (
                            <span key={lang} className="text-[10px] font-mono text-slate-300 bg-slate-900/90 px-2 py-0.5 rounded-md border border-slate-800">
                              {lang}: {lines} lines
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRepo(repo);
                        navigate('/explorer');
                      }}
                      className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-300 py-1 px-2 rounded-lg hover:bg-slate-900 transition-colors"
                    >
                      <FolderTree className="w-3.5 h-3.5" />
                      <span>Explorer</span>
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRepo(repo);
                        navigate('/chat');
                      }}
                      className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-300 py-1 px-2 rounded-lg hover:bg-slate-900 transition-colors"
                    >
                      <MessageSquareCode className="w-3.5 h-3.5" />
                      <span>AI Chat</span>
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRepo(repo);
                        navigate('/tasks');
                      }}
                      className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 py-1 px-2.5 rounded-lg bg-cyan-950/60 border border-cyan-500/20 hover:bg-cyan-950/90 transition-all"
                    >
                      <Bot className="w-3.5 h-3.5" />
                      <span>New Task</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      <span key={lang} className="text-[11px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
        {lang}: {lines} lines
      </span>
                          ))}
    </div>
                      </div >
                    )}
                  </div >

  <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
    <button
      onClick={(e) => {
        e.stopPropagation();
        onSelectRepo(repo);
        navigate('/explorer');
      }}
      className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-cyan-400 py-1"
    >
      <FolderTree className="w-3.5 h-3.5" />
      <span>Explorer</span>
    </button>

    <button
      onClick={(e) => {
        e.stopPropagation();
        onSelectRepo(repo);
        navigate('/chat');
      }}
      className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-cyan-400 py-1"
    >
      <MessageSquareCode className="w-3.5 h-3.5" />
      <span>AI Chat</span>
    </button>

    <button
      onClick={(e) => {
        e.stopPropagation();
        onSelectRepo(repo);
        navigate('/tasks');
      }}
      className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 py-1"
    >
      <Bot className="w-3.5 h-3.5" />
      <span>New Task</span>
    </button>
  </div>
                </div >
              );
            })}
          </div >
        )}
      </div >

  <RepoConnectorModal
    isOpen={isConnectModalOpen}
    onClose={() => setIsConnectModalOpen(false)}
    onConnect={onConnectRepo}
    isLoading={isLoading}
  />
    </div >
  );
};
