import React from 'react';
import { Terminal, Shield, Zap, AlertTriangle, CheckCircle } from 'lucide-react';
import { AgentLog } from '../../types/task';

interface AgentLogsTerminalProps {
  logs: AgentLog[];
}

export const AgentLogsTerminal: React.FC<AgentLogsTerminalProps> = ({ logs }) => {
  const getLevelStyle = (level: string) => {
    switch (level) {
      case 'ACTION':
        return 'text-cyan-400 font-semibold';
      case 'WARNING':
        return 'text-amber-400 font-semibold';
      case 'ERROR':
        return 'text-rose-400 font-semibold';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <h4 className="text-xs font-mono font-semibold text-slate-300">Agent Reasoning & Trace Logs</h4>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-700" />
          <span className="w-2.5 h-2.5 rounded-full bg-slate-700" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
        </div>
      </div>

      <div className="p-4 font-mono text-xs overflow-y-auto max-h-72 space-y-2 leading-relaxed">
        {logs.length === 0 ? (
          <div className="text-slate-400 italic">No agent logs recorded yet.</div>
        ) : (
          logs.map((log, i) => (
            <div key={log.id || i} className="flex items-start gap-2">
              <span className="text-slate-400 select-none">
                [{new Date(log.created_at || Date.now()).toLocaleTimeString()}]
              </span>
              <span className="text-purple-400 font-medium">@{log.agent_name}:</span>
              <span className={getLevelStyle(log.level)}>[{log.level}]</span>
              <span className="text-slate-200">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
