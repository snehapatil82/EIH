import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Terminal,
  Play,
  Square,
  RotateCcw,
  ChevronRight,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  AlertTriangle,
  History,
  Trash2,
} from 'lucide-react';
import { terminalService } from '../../services/terminalService';
import { TerminalInfo, TerminalOutputChunk, TerminalHistoryEntry } from '../../types/terminal';

interface ProjectTerminalProps {
  taskId: string;
}

interface OutputLine {
  id: string;
  type: 'stdout' | 'stderr' | 'system' | 'error' | 'input';
  text: string;
  elapsed?: number;
  exitCode?: number;
}

const LINE_COLORS: Record<string, string> = {
  stdout: 'text-slate-200',
  stderr: 'text-rose-400',
  system: 'text-cyan-400 font-mono italic',
  error: 'text-amber-400 font-semibold',
  input: 'text-emerald-300 font-mono font-semibold',
};

let lineIdCounter = 0;
const newLine = (type: OutputLine['type'], text: string, elapsed?: number, exitCode?: number): OutputLine => ({
  id: `line-${++lineIdCounter}`,
  type,
  text,
  elapsed,
  exitCode,
});

export const ProjectTerminal: React.FC<ProjectTerminalProps> = ({ taskId }) => {
  const [info, setInfo] = useState<TerminalInfo | null>(null);
  const [output, setOutput] = useState<OutputLine[]>([]);
  const [history, setHistory] = useState<TerminalHistoryEntry[]>([]);
  const [command, setCommand] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'terminal' | 'history'>('terminal');
  const [histCursor, setHistCursor] = useState(-1);
  const [inputHistory, setInputHistory] = useState<string[]>([]);

  const outputRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  // Load project info + history on mount
  useEffect(() => {
    let cancelled = false;
    terminalService.getInfo(taskId).then((i) => {
      if (!cancelled) {
        setInfo(i);
        setOutput([
          newLine('system', `── Project Terminal ──────────────────────────────────────`),
          newLine('system', `Workspace: ${i.workspace_path}`),
          newLine('system', `Project Type: ${i.project_type.toUpperCase()} | Manifests: ${i.manifests.join(', ') || 'none detected'}`),
          newLine('system', `Type a command and press Enter. Use quick-launch buttons above.`),
          newLine('system', `─────────────────────────────────────────────────────────`),
        ]);
      }
    }).catch((err) => {
      if (!cancelled) {
        setOutput([newLine('error', `Failed to load terminal info: ${err.message}`)]);
      }
    });

    terminalService.getHistory(taskId).then((h) => {
      if (!cancelled) setHistory(h);
    }).catch(() => {});

    return () => { cancelled = true; };
  }, [taskId]);

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const appendLine = (line: OutputLine) =>
    setOutput((prev) => [...prev.slice(-2000), line]); // cap at 2000 lines

  const runCommand = useCallback((cmd: string) => {
    const trimmed = cmd.trim();
    if (!trimmed || isRunning) return;

    // Add to input history
    setInputHistory((prev) => [trimmed, ...prev.filter((c) => c !== trimmed)].slice(0, 50));
    setHistCursor(-1);
    setCommand('');
    setIsRunning(true);

    appendLine(newLine('input', `$ ${trimmed}`));

    const cleanup = terminalService.streamCommand(
      taskId,
      trimmed,
      (chunk: TerminalOutputChunk) => {
        if (chunk.type === 'system' && chunk.line.startsWith('$ ')) return; // skip echo
        appendLine(newLine(chunk.type, chunk.line, chunk.elapsed, chunk.exit_code));
      },
      (sessionId) => {
        setIsRunning(false);
        cleanupRef.current = null;
        // Refresh history
        terminalService.getHistory(taskId).then(setHistory).catch(() => {});
      },
      (error) => {
        appendLine(newLine('error', error));
        setIsRunning(false);
        cleanupRef.current = null;
      },
    );

    cleanupRef.current = cleanup;
  }, [taskId, isRunning]);

  const stopCommand = () => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    appendLine(newLine('system', '[Process stopped by user]'));
    setIsRunning(false);
  };

  const clearOutput = () => setOutput([]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      runCommand(command);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const next = Math.min(histCursor + 1, inputHistory.length - 1);
      setHistCursor(next);
      if (inputHistory[next]) setCommand(inputHistory[next]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const next = Math.max(histCursor - 1, -1);
      setHistCursor(next);
      setCommand(next === -1 ? '' : inputHistory[next] || '');
    }
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col" style={{ height: '520px' }}>
      {/* Terminal Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-r from-slate-900 to-slate-900/80 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          {/* macOS-style traffic lights */}
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-rose-500 hover:bg-rose-400 cursor-pointer transition-colors" onClick={stopCommand} title="Stop" />
            <div className="w-3 h-3 rounded-full bg-amber-500 hover:bg-amber-400 cursor-pointer transition-colors" onClick={clearOutput} title="Clear" />
            <div className="w-3 h-3 rounded-full bg-emerald-500 hover:bg-emerald-400 cursor-pointer transition-colors" title="Running" />
          </div>
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-semibold text-slate-300">
            Project Terminal
            {info && (
              <span className="ml-2 px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 text-[10px] border border-cyan-800">
                {info.project_type.toUpperCase()}
              </span>
            )}
          </span>
          {isRunning && (
            <div className="flex items-center gap-1 text-emerald-400 text-xs animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>running</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab(activeTab === 'terminal' ? 'history' : 'terminal')}
            className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 px-2 py-1 rounded hover:bg-slate-800 transition-colors"
          >
            <History className="w-3.5 h-3.5" />
            History ({history.length})
          </button>
          <button
            onClick={clearOutput}
            className="text-slate-500 hover:text-slate-300 p-1 rounded hover:bg-slate-800 transition-colors"
            title="Clear terminal"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          {isRunning ? (
            <button
              onClick={stopCommand}
              className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-rose-900/50 hover:bg-rose-900 text-rose-300 border border-rose-800 transition-colors"
            >
              <Square className="w-3 h-3" />
              Stop
            </button>
          ) : null}
        </div>
      </div>

      {/* Quick-launch buttons */}
      {info && info.suggested_commands.length > 0 && (
        <div className="flex items-center gap-1.5 px-4 py-2 bg-slate-900/50 border-b border-slate-800/50 flex-shrink-0 overflow-x-auto">
          <Zap className="w-3 h-3 text-amber-400 flex-shrink-0" />
          <span className="text-[10px] text-slate-500 font-semibold flex-shrink-0">Quick:</span>
          {info.suggested_commands.map((s, i) => (
            <button
              key={i}
              onClick={() => runCommand(s.cmd)}
              disabled={isRunning}
              className="flex-shrink-0 text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 hover:border-cyan-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed font-mono"
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* Output Area */}
      {activeTab === 'terminal' ? (
        <div
          ref={outputRef}
          className="flex-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed space-y-0.5"
          onClick={() => inputRef.current?.focus()}
        >
          {output.map((line) => (
            <div key={line.id} className={`flex items-start gap-2 ${LINE_COLORS[line.type]}`}>
              {line.elapsed !== undefined && line.type !== 'input' && line.type !== 'system' && (
                <span className="text-slate-600 select-none flex-shrink-0 w-10 text-right">
                  {line.elapsed.toFixed(1)}s
                </span>
              )}
              <span className="whitespace-pre-wrap break-all">{line.text}</span>
              {line.exitCode !== undefined && (
                <span className={`ml-auto flex-shrink-0 flex items-center gap-1 ${line.exitCode === 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {line.exitCode === 0 ? (
                    <CheckCircle2 className="w-3 h-3" />
                  ) : (
                    <XCircle className="w-3 h-3" />
                  )}
                  <span>{line.exitCode}</span>
                </span>
              )}
            </div>
          ))}
          {isRunning && (
            <div className="flex items-center gap-2 text-slate-500 animate-pulse">
              <span className="text-slate-600">▶</span>
              <span>executing...</span>
            </div>
          )}
        </div>
      ) : (
        /* History Tab */
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {history.length === 0 ? (
            <div className="text-xs text-slate-500 italic text-center py-8">No command history yet.</div>
          ) : (
            history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => {
                  setCommand(entry.command);
                  setActiveTab('terminal');
                  setTimeout(() => inputRef.current?.focus(), 50);
                }}
                className="w-full text-left px-3 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-emerald-300 truncate max-w-xs">$ {entry.command}</span>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500">
                    {entry.timed_out ? (
                      <span className="text-amber-400 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />timeout</span>
                    ) : entry.exit_code === 0 ? (
                      <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />ok</span>
                    ) : (
                      <span className="text-rose-400 flex items-center gap-1"><XCircle className="w-3 h-3" />exit {entry.exit_code}</span>
                    )}
                    <span className="opacity-0 group-hover:opacity-100 transition-opacity text-cyan-400">↵ run again</span>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Command Input */}
      <div className="flex items-center gap-2 px-4 py-3 bg-slate-900 border-t border-slate-800 flex-shrink-0">
        <ChevronRight className="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            info
              ? `Type a command (e.g. ${info.suggested_commands[0]?.cmd || 'ls -la'})...`
              : 'Loading workspace...'
          }
          disabled={!info || isRunning}
          className="flex-1 bg-transparent font-mono text-xs text-slate-100 placeholder-slate-600 outline-none disabled:opacity-40"
          autoComplete="off"
          spellCheck={false}
        />
        <button
          onClick={() => runCommand(command)}
          disabled={!command.trim() || isRunning || !info}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isRunning ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5" />
          )}
          Run
        </button>
      </div>
    </div>
  );
};
