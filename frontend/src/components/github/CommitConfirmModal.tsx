import React, { useState } from 'react';
import {
  GitBranch,
  GitCommit,
  UploadCloud,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ExternalLink,
  Loader2,
  Lock,
  ShieldCheck,
  FileCode,
  Plus,
  Minus,
  Pencil,
  ChevronDown,
  ChevronRight,
  GitPullRequest,
} from 'lucide-react';
import { GitHubStatus, GitHubDiffResult, PublishResult } from '../../types/github';

interface CommitConfirmModalProps {
  status: GitHubStatus;
  diff: GitHubDiffResult;
  branchName: string;
  commitMessage: string;
  createPr: boolean;
  isPublishing: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const CommitConfirmModal: React.FC<CommitConfirmModalProps> = ({
  status,
  diff,
  branchName,
  commitMessage,
  createPr,
  isPublishing,
  onConfirm,
  onCancel,
}) => {
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const [agreed, setAgreed] = useState(false);

  const toggleFile = (path: string) => {
    setExpandedFiles((prev) => {
      const next = new Set(prev);
      next.has(path) ? next.delete(path) : next.add(path);
      return next;
    });
  };

  const changeTypeColor = (t: string) =>
    t === 'add' ? 'text-emerald-400' : t === 'delete' ? 'text-rose-400' : 'text-amber-400';
  const changeTypeLabel = (t: string) =>
    t === 'add' ? 'ADD' : t === 'delete' ? 'DEL' : 'MOD';

  return (
    /* Backdrop */
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-800">
          <div className="p-2 rounded-lg bg-cyan-950 border border-cyan-800">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100">Confirm Publish to GitHub</h3>
            <p className="text-xs text-slate-400">
              Review all changes carefully before committing. This action cannot be automatically undone.
            </p>
          </div>
        </div>

        {/* Content (scrollable) */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
              <div className="text-[10px] text-slate-500 uppercase font-semibold mb-1">Target Branch</div>
              <div className="flex items-center gap-1.5 text-sm text-cyan-300 font-mono">
                <GitBranch className="w-3.5 h-3.5" />
                {branchName}
              </div>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
              <div className="text-[10px] text-slate-500 uppercase font-semibold mb-1">From Branch</div>
              <div className="flex items-center gap-1.5 text-sm text-slate-300 font-mono">
                <GitBranch className="w-3.5 h-3.5" />
                {status.current_branch}
              </div>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
              <div className="text-[10px] text-slate-500 uppercase font-semibold mb-1">Files Changed</div>
              <div className="text-sm text-slate-200 font-semibold">{diff.total_changed_files} file(s)</div>
            </div>
          </div>

          {/* Commit message */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3">
            <div className="text-[10px] text-slate-500 uppercase font-semibold mb-2 flex items-center gap-1">
              <GitCommit className="w-3 h-3" /> Commit Message
            </div>
            <div className="font-mono text-xs text-slate-200 leading-relaxed">{commitMessage}</div>
          </div>

          {/* File diffs */}
          <div className="space-y-2">
            <div className="text-[10px] text-slate-500 uppercase font-semibold flex items-center gap-1">
              <FileCode className="w-3 h-3" /> Changed Files
            </div>
            {diff.changes.map((c) => (
              <div key={c.file_path} className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
                <button
                  onClick={() => toggleFile(c.file_path)}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-slate-900/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold ${changeTypeColor(c.change_type)}`}>
                      {changeTypeLabel(c.change_type)}
                    </span>
                    <span className="font-mono text-xs text-slate-200">{c.file_path}</span>
                  </div>
                  {expandedFiles.has(c.file_path) ? (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                  )}
                </button>
                {expandedFiles.has(c.file_path) && (
                  <div className="border-t border-slate-800 max-h-48 overflow-y-auto">
                    <div className="p-3 font-mono text-[11px] space-y-0.5">
                      {c.diff.split('\n').map((line, i) => {
                        const isAdd = line.startsWith('+') && !line.startsWith('+++');
                        const isDel = line.startsWith('-') && !line.startsWith('---');
                        const isHunk = line.startsWith('@@');
                        return (
                          <div
                            key={i}
                            className={
                              isAdd
                                ? 'text-emerald-300 bg-emerald-950/30'
                                : isDel
                                ? 'text-rose-300 bg-rose-950/30'
                                : isHunk
                                ? 'text-cyan-400 bg-cyan-950/30'
                                : 'text-slate-400'
                            }
                          >
                            {line || ' '}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {createPr && (
            <div className="flex items-start gap-2 p-3 rounded-xl bg-purple-950/30 border border-purple-800/50 text-xs text-purple-300">
              <GitPullRequest className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              A pull request will be created from <strong className="mx-1 font-mono">{branchName}</strong> → <strong className="mx-1 font-mono">{status.default_branch}</strong> after the push.
            </div>
          )}

          {/* Warning banner */}
          <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-950/30 border border-amber-800/50 text-xs text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>
              AI-generated code should be reviewed by a human before merging. Never push directly to a protected branch.
            </span>
          </div>

          {/* Checkbox confirmation */}
          <label className="flex items-start gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-0.5 accent-cyan-500"
            />
            <span className="text-xs text-slate-300">
              I have reviewed the changes above and confirm I want to push them to{' '}
              <span className="font-mono text-cyan-300">{branchName}</span> on{' '}
              <span className="font-mono text-cyan-300">{status.repository_owner}/{status.repository_name}</span>.
            </span>
          </label>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-800 flex-shrink-0">
          <button
            onClick={onCancel}
            disabled={isPublishing}
            className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 rounded-xl border border-slate-700 hover:border-slate-600 transition-colors disabled:opacity-40"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!agreed || isPublishing}
            className="flex items-center gap-2 px-5 py-2 text-sm font-semibold rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
          >
            {isPublishing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Publishing…
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" />
                Publish to GitHub
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
