import React, { useState, useEffect } from 'react';
import {
  Bot,
  Plus,
  Send,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  FileCode2,
  Terminal,
  RotateCcw,
  Network,
} from 'lucide-react';
import { Repository } from '../types/repository';
import { EngineeringTask, AgentLog } from '../types/task';
import { CodeChange, ValidationResult, ReviewResult, TaskDiagram } from '../types/changes';
import { taskService } from '../services/taskService';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Spinner } from '../components/common/Spinner';
import { AgentTimeline } from '../components/tasks/AgentTimeline';
import { AgentLogsTerminal } from '../components/tasks/AgentLogsTerminal';
import { DiffViewer } from '../components/changes/DiffViewer';
import { ApprovalPanel } from '../components/changes/ApprovalPanel';
import { ValidationSummary } from '../components/changes/ValidationSummary';
import { ReviewScorecard } from '../components/changes/ReviewScorecard';
import { MermaidViewer } from '../components/diagrams/MermaidViewer';
import { ProjectTerminal } from '../components/terminal/ProjectTerminal';
import { GitHubPublishPanel } from '../components/github/GitHubPublishPanel';

interface EngineeringTaskPageProps {
  selectedRepo: Repository | null;
}

const SAMPLE_REQUIREMENTS = [
  'Add JWT authentication, create tests, and update documentation.',
  'Generate comprehensive unit tests for core services.',
  'Create user registration API endpoint with password hashing.',
  'Generate Software Design Document (SDD) and architecture diagrams.',
];

export const EngineeringTaskPage: React.FC<EngineeringTaskPageProps> = ({ selectedRepo }) => {
  const [requirementInput, setRequirementInput] = useState('');
  const [workflowPref, setWorkflowPref] = useState('auto');
  const [tasks, setTasks] = useState<EngineeringTask[]>([]);
  const [activeTask, setActiveTask] = useState<EngineeringTask | null>(null);
  const [changes, setChanges] = useState<CodeChange[]>([]);
  const [validations, setValidations] = useState<ValidationResult[]>([]);
  const [reviews, setReviews] = useState<ReviewResult[]>([]);
  const [diagrams, setDiagrams] = useState<TaskDiagram[]>([]);
  const [selectedDiagramType, setSelectedDiagramType] = useState<string>('all');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'diffs' | 'validation' | 'review' | 'diagrams' | 'logs' | 'terminal' | 'publish'>('diffs');

  useEffect(() => {
    if (!selectedRepo) return;
    loadTasks();
  }, [selectedRepo]);

  const loadTasks = async () => {
    if (!selectedRepo) return;
    try {
      const taskList = await taskService.listForRepo(selectedRepo.id);
      setTasks(taskList);
      if (taskList.length > 0 && !activeTask) {
        selectTask(taskList[0].id);
      }
    } catch (err) {
      console.error('Failed to load tasks:', err);
    }
  };

  const selectTask = async (taskId: string) => {
    try {
      const task = await taskService.get(taskId);
      setActiveTask(task);
      const chs = await taskService.getChanges(taskId);
      setChanges(chs);
      const vals = await taskService.getValidation(taskId);
      setValidations(vals);
      const revs = await taskService.getReview(taskId);
      setReviews(revs);
      const diags = await taskService.getDiagrams(taskId);
      setDiagrams(diags);
    } catch (err) {
      console.error('Failed to fetch task details:', err);
    }
  };

  const handleCreateTask = async (customReq?: string) => {
    const text = customReq || requirementInput;
    if (!text.trim() || !selectedRepo || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const newTask = await taskService.create(selectedRepo.id, text.trim(), workflowPref);
      setRequirementInput('');
      setActiveTask(newTask);
      setTasks((prev) => [newTask, ...prev]);

      // Connect to live SSE stream for real-time updates
      taskService.streamTask(
        newTask.id,
        (update) => {
          setActiveTask((prev) => {
            if (!prev || prev.id !== update.task_id) return prev;
            const existingLogs = prev.logs || [];
            const incomingLogs = update.new_logs || [];
            const logMap = new Map<string, AgentLog>();
            existingLogs.forEach((l: AgentLog) => logMap.set(l.id || `${l.agent_name}-${l.message}`, l));
            incomingLogs.forEach((l: AgentLog) => logMap.set(l.id || `${l.agent_name}-${l.message}`, l));
            const mergedLogs = Array.from(logMap.values());

            return {
              ...prev,
              status: update.status,
              active_agent: update.active_agent,
              retry_count: update.retry_count,
              steps: update.steps && update.steps.length > 0 ? update.steps : prev.steps,
              logs: mergedLogs,
            };
          });
        },
        async () => {
          await selectTask(newTask.id);
          setIsSubmitting(false);
          await loadTasks();
        },
        async () => {
          // Fallback poll if SSE encounters error
          const interval = setInterval(async () => {
            try {
              const updated = await taskService.get(newTask.id);
              setActiveTask(updated);
              if (updated.status !== 'running' && updated.status !== 'planning') {
                clearInterval(interval);
                await selectTask(updated.id);
                setIsSubmitting(false);
                await loadTasks();
              }
            } catch (e) {
              clearInterval(interval);
              setIsSubmitting(false);
            }
          }, 1500);
        }
      );
    } catch (err) {
      console.error('Failed to create task:', err);
      setIsSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!activeTask) return;
    setIsActionLoading(true);
    try {
      await taskService.approve(activeTask.id);
      await selectTask(activeTask.id);
      await loadTasks();
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!activeTask) return;
    setIsActionLoading(true);
    try {
      await taskService.reject(activeTask.id);
      await selectTask(activeTask.id);
      await loadTasks();
    } catch (err) {
      console.error('Rejection failed:', err);
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleRevise = async (feedback: string) => {
    if (!activeTask) return;
    setIsActionLoading(true);
    const targetId = activeTask.id;
    try {
      await taskService.revise(targetId, feedback);
      // Connect to SSE stream for revision updates
      taskService.streamTask(
        targetId,
        (update) => {
          setActiveTask((prev) => {
            if (!prev || prev.id !== update.task_id) return prev;
            const existingLogs = prev.logs || [];
            const incomingLogs = update.new_logs || [];
            const logMap = new Map<string, AgentLog>();
            existingLogs.forEach((l: AgentLog) => logMap.set(l.id || `${l.agent_name}-${l.message}`, l));
            incomingLogs.forEach((l: AgentLog) => logMap.set(l.id || `${l.agent_name}-${l.message}`, l));

            return {
              ...prev,
              status: update.status,
              active_agent: update.active_agent,
              retry_count: update.retry_count,
              steps: update.steps && update.steps.length > 0 ? update.steps : prev.steps,
              logs: Array.from(logMap.values()),
            };
          });
        },
        async () => {
          await selectTask(targetId);
          await loadTasks();
          setIsActionLoading(false);
        },
        async () => {
          await selectTask(targetId);
          await loadTasks();
          setIsActionLoading(false);
        }
      );
    } catch (err) {
      console.error('Revision failed:', err);
      setIsActionLoading(false);
    }
  };

  if (!selectedRepo) {
    return (
      <div className="p-12 text-center text-slate-400">
        Please select or connect a repository first to launch autonomous engineering tasks.
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Header & Requirement Input */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Bot className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold text-slate-100">
              Autonomous Engineering Studio ({selectedRepo.name})
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Submit a natural-language requirement. Specialized agents will plan, implement, test, document, and validate changes before asking for your approval.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            placeholder="e.g. 'Add JWT authentication, create tests and update documentation'..."
            className="flex-1 bg-slate-950 border border-slate-750 focus:border-cyan-500 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 transition-colors"
            value={requirementInput}
            onChange={(e) => setRequirementInput(e.target.value)}
            disabled={isSubmitting}
          />
          <div className="flex items-center gap-2">
            <select
              className="bg-slate-950 border border-slate-750 text-xs text-slate-300 rounded-xl px-3 py-2.5 focus:outline-none"
              value={workflowPref}
              onChange={(e) => setWorkflowPref(e.target.value)}
              disabled={isSubmitting}
            >
              <option value="auto">Auto Complexity</option>
              <option value="multi_agent">Multi-Agent Workflow</option>
              <option value="single_agent">Single-Agent Workflow</option>
            </select>

            <Button
              variant="primary"
              onClick={() => handleCreateTask()}
              isLoading={isSubmitting}
              disabled={!requirementInput.trim()}
              rightIcon={<Send className="w-3.5 h-3.5" />}
            >
              Execute
            </Button>
          </div>
        </div>

        {/* Quick Requirement Presets */}
        <div className="flex items-center gap-2 flex-wrap pt-1">
          <span className="text-[11px] text-slate-400 font-medium">Quick Prompts:</span>
          {SAMPLE_REQUIREMENTS.map((prompt, i) => (
            <button
              key={i}
              className="text-[11px] px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-750 text-cyan-300 border border-slate-700 transition-colors"
              onClick={() => handleCreateTask(prompt)}
              disabled={isSubmitting}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Main Studio View (Split Layout) */}
      {activeTask ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Task Status & Agent Timeline */}
          <div className="lg:col-span-4 space-y-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Task Overview
                </span>
                <Badge
                  variant={
                    activeTask.complexity === 'COMPLEX'
                      ? 'purple'
                      : activeTask.complexity === 'MEDIUM'
                      ? 'info'
                      : 'cyan'
                  }
                >
                  {activeTask.complexity}
                </Badge>
              </div>

              <h3 className="text-sm font-semibold text-slate-100">{activeTask.requirement}</h3>

              <div className="text-xs text-slate-400 space-y-1 font-mono pt-2 border-t border-slate-800">
                <div>Task ID: {activeTask.id.substring(0, 8)}...</div>
                <div>Workflow: {activeTask.workflow_type}</div>
                <div>Self-Correction Retries: {activeTask.retry_count} / {activeTask.max_retries}</div>
              </div>
            </div>

            <AgentTimeline
              steps={activeTask.steps || []}
              activeAgent={activeTask.active_agent}
              taskStatus={activeTask.status}
            />

            {/* Task Switcher */}
            {tasks.length > 1 && (
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Previous Tasks ({tasks.length})
                </h4>
                <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                  {tasks.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => selectTask(t.id)}
                      className={`w-full text-left p-2 rounded-lg text-xs truncate transition-colors ${
                        activeTask.id === t.id
                          ? 'bg-cyan-950 text-cyan-300 font-semibold'
                          : 'text-slate-400 hover:bg-slate-800 text-slate-300'
                      }`}
                    >
                      {t.requirement}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Code Changes, Validation, Diagrams & Human-in-the-Loop */}
          <div className="lg:col-span-8 space-y-5">
            {/* Human-in-the-Loop Approval Action Bar */}
            <ApprovalPanel
              taskId={activeTask.id}
              status={activeTask.status}
              onApprove={handleApprove}
              onReject={handleReject}
              onRevise={handleRevise}
              isLoading={isActionLoading}
            />

            {/* Studio Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <button
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${
                  activeTab === 'diffs' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setActiveTab('diffs')}
              >
                Code Diffs ({changes.length})
              </button>
              <button
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${
                  activeTab === 'validation' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setActiveTab('validation')}
              >
                Validation & Tests ({validations.length})
              </button>
              <button
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${
                  activeTab === 'review' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setActiveTab('review')}
              >
                Security & Quality Audit
              </button>
              <button
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${
                  activeTab === 'diagrams' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setActiveTab('diagrams')}
              >
                Mermaid Diagrams ({diagrams.length})
              </button>
              <button
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${
                  activeTab === 'logs' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setActiveTab('logs')}
              >
                Agent Trace Logs ({activeTask.logs?.length || 0})
              </button>
              <button
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                  activeTab === 'terminal'
                    ? 'bg-emerald-700 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setActiveTab('terminal')}
              >
                <Terminal className="w-3 h-3" />
                Terminal
              </button>
              <button
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                  activeTab === 'publish'
                    ? 'bg-cyan-700 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setActiveTab('publish')}
              >
                <Network className="w-3 h-3" />
                Publish
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'diffs' && (
              <div>
                {changes.length === 0 ? (
                  <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-xs text-slate-400">
                    No code changes generated yet.
                  </div>
                ) : (
                  changes.map((ch) => <DiffViewer key={ch.id} change={ch} />)
                )}
              </div>
            )}

            {activeTab === 'validation' && (
              <ValidationSummary validation={validations[0]} />
            )}

            {activeTab === 'review' && (
              <ReviewScorecard review={reviews[0]} />
            )}

            {activeTab === 'diagrams' && (
              <div className="space-y-6">
                {diagrams.length > 0 ? (
                  <>
                    {/* Diagram Filter Pills */}
                    <div className="flex items-center gap-2 flex-wrap pb-2 border-b border-slate-800">
                      {(['all', 'architecture', 'sequence', 'usecase', 'state', 'dfd'] as const).map((filterType) => {
                        const count = filterType === 'all'
                          ? diagrams.length
                          : diagrams.filter(d => (d.diagram_type || '').toLowerCase() === filterType).length;
                        if (filterType !== 'all' && count === 0) return null;
                        const labelMap: Record<string, string> = {
                          all: 'All Diagrams',
                          architecture: 'Architecture',
                          sequence: 'Sequence',
                          usecase: 'Use Case',
                          state: 'State Machine',
                          dfd: 'Data Flow (DFD)'
                        };
                        return (
                          <button
                            key={filterType}
                            onClick={() => setSelectedDiagramType(filterType)}
                            className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${
                              selectedDiagramType === filterType
                                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 shadow-sm'
                                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                            }`}
                          >
                            {labelMap[filterType]} ({count})
                          </button>
                        );
                      })}
                    </div>

                    {diagrams
                      .filter(d => selectedDiagramType === 'all' || (d.diagram_type || '').toLowerCase() === selectedDiagramType)
                      .map((d) => {
                        const typeKey = (d.diagram_type || '').toLowerCase();
                        const typeConfig: Record<string, { label: string; badge: string; color: string; border: string; bg: string }> = {
                          architecture: { label: 'Component Architecture', badge: 'graph TD', color: 'text-cyan-300', border: 'border-cyan-800', bg: 'bg-cyan-950/40' },
                          sequence: { label: 'Call Sequence Flow', badge: 'sequenceDiagram', color: 'text-violet-300', border: 'border-violet-800', bg: 'bg-violet-950/40' },
                          usecase: { label: 'Actor Use Case', badge: 'graph LR', color: 'text-indigo-300', border: 'border-indigo-800', bg: 'bg-indigo-950/40' },
                          state: { label: 'State Machine', badge: 'stateDiagram-v2', color: 'text-orange-300', border: 'border-orange-800', bg: 'bg-orange-950/40' },
                          dfd: { label: 'Level-1 Data Flow (DFD)', badge: 'flowchart LR', color: 'text-teal-300', border: 'border-teal-800', bg: 'bg-teal-950/40' },
                        };
                        const cfg = typeConfig[typeKey] || {
                          label: d.diagram_type.toUpperCase(),
                          badge: 'mermaid',
                          color: 'text-cyan-300',
                          border: 'border-slate-800',
                          bg: 'bg-slate-900/40'
                        };

                        return (
                          <div key={d.id || `${d.diagram_type}-${Math.random()}`} className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/20 p-4">
                            <div className={`flex items-start justify-between gap-3 p-3 rounded-lg border ${cfg.bg} ${cfg.border}`}>
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className={`text-xs font-bold uppercase tracking-wider ${cfg.color}`}>
                                    {cfg.label}
                                  </span>
                                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                                    {cfg.badge}
                                  </span>
                                </div>
                                {d.description && (
                                  <p className="text-xs text-slate-300 leading-relaxed font-medium">{d.description}</p>
                                )}
                              </div>
                            </div>
                            <MermaidViewer
                              title={`${cfg.label} · ${activeTask?.requirement || ''}`}
                              chart={d.mermaid_code}
                              description={d.description}
                              filenameBase={`task-${d.diagram_type}`}
                            />
                          </div>
                        );
                      })}
                  </>
                ) : (
                  <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-xs text-slate-400">
                    No diagrams (Architecture, Sequence, Use Case, State Machine, DFD) generated for this task yet.
                  </div>
                )}
              </div>
            )}

            {activeTab === 'logs' && (
              <AgentLogsTerminal logs={activeTask.logs || []} />
            )}

            {activeTab === 'terminal' && (
              <ProjectTerminal taskId={activeTask.id} />
            )}

            {activeTab === 'publish' && (
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Network className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-slate-100">Publish to GitHub</h3>
                  <span className="text-[10px] text-slate-500 ml-auto">Requires explicit confirmation — never auto-pushes</span>
                </div>
                <GitHubPublishPanel taskId={activeTask.id} taskStatus={activeTask.status} />
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="p-16 text-center bg-slate-900/30 border border-dashed border-slate-800 rounded-2xl space-y-3">
          <Bot className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">Autonomous Engineering Studio Ready</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Enter a requirement above to launch the autonomous agentic workflow.
          </p>
        </div>
      )}
    </div>
  );
};

