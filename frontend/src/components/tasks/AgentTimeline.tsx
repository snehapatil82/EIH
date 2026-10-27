import React from 'react';
import {
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
  Cpu,
  FileCheck,
  Code2,
  FlaskConical,
  BookOpen,
  Network,
  ShieldCheck,
} from 'lucide-react';
import { TaskStep } from '../../types/task';

interface AgentTimelineProps {
  steps: TaskStep[];
  activeAgent?: string;
  taskStatus: string;
}

const AGENT_ICONS: Record<string, any> = {
  orchestrator: Cpu,
  requirement_agent: FileCheck,
  repository_agent: Network,
  code_understanding_agent: Code2,
  design_agent: Network,
  code_agent: Code2,
  test_agent: FlaskConical,
  documentation_agent: BookOpen,
  diagram_agent: Network,
  validation_agent: ShieldCheck,
  review_agent: ShieldCheck,
};

export const AgentTimeline: React.FC<AgentTimelineProps> = ({
  steps,
  activeAgent,
  taskStatus,
}) => {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Agentic Execution Pipeline
        </h3>
        <span className="text-xs font-mono text-cyan-400">
          Status: <strong className="uppercase">{taskStatus}</strong>
        </span>
      </div>

      <div className="space-y-3">
        {steps.map((step, idx) => {
          const Icon = AGENT_ICONS[step.agent_name] || Cpu;
          const isCurrent = activeAgent === step.agent_name && taskStatus === 'running';
          const isCompleted = step.status === 'completed' || taskStatus === 'waiting_approval' || taskStatus === 'approved';

          return (
            <div
              key={step.id || idx}
              className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${
                isCurrent
                  ? 'bg-cyan-950/40 border-cyan-500/60 shadow-lg shadow-cyan-950/50'
                  : isCompleted
                  ? 'bg-slate-900/80 border-slate-800'
                  : 'bg-slate-950/40 border-slate-850 opacity-60'
              }`}
            >
              <div className="mt-0.5">
                {isCurrent ? (
                  <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
                ) : isCompleted ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : step.status === 'failed' ? (
                  <AlertCircle className="w-5 h-5 text-rose-400" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-600" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-cyan-400" />
                    <h4 className="text-xs font-semibold text-slate-200">{step.title}</h4>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">
                    {step.agent_name.replace('_', ' ')}
                  </span>
                </div>
                {step.description && (
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{step.description}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
