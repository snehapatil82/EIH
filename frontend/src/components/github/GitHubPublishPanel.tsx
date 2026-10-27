import React, { useState, useEffect, useCallback } from 'react';
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
  RefreshCw,
  Plus,
  GitPullRequest,
  FileCode,
  Eye,
} from 'lucide-react';
import { githubService } from '../../services/githubService';
import { GitHubStatus, GitHubDiffResult, PublishResult } from '../../types/github';
import { CommitConfirmModal } from './CommitConfirmModal';

interface GitHubPublishPanelProps {
  taskId: string;
  taskStatus: string;
}

export const GitHubPublishPanel: React.FC<GitHubPublishPanelProps> = ({ taskId, taskStatus }) => {
  const [status, setStatus] = useState<GitHubStatus | null>(null);
  const [diff, setDiff] = useState<GitHubDiffResult | null>(null);
  const [branches, setBranches] = useState<string[]>([]);
  const [branchName, setBranchName] = useState('');
  const [commitMessage, setCommitMessage] = useState('');
  const [createPr, setCreatePr] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [result, setResult] = useState<PublishResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDiffs, setShowDiffs] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [s, d] = await Promise.all([
        githubService.getStatus(taskId),
        githubService.getDiff(taskId),
      ]);
      setStatus(s);
      setDiff(d);
      setBranchName(s.suggested_branch);
      setCommitMessage(
        `feat: AI-generated changes from EIH task ${taskId.substring(0, 8)}\n\n${
          d.changes.map((c) => `- ${c.change_type}: ${c.file_path}`).join('\n')
        }`
      );

      // Fetch branches (non-blocking)
      githubService.listBranches(taskId).then((b) => setBranches(b.branches)).catch(() => {});
    } catch (err: any) {
      setError(err.message || 'Failed to load GitHub status');
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    load();
  }, [load]);

  const handlePublish = async () => {
    if (!status || !diff) return;
    setIsPublishing(true);
    setError(null);
    try {
      const r = await githubService.publish(taskId, {
        branch_name: branchName,
        commit_message: commitMessage,
        confirmed: true,  // User explicitly confirmed in modal
        create_pr: createPr,
      });
      setResult(r);
      setShowConfirm(false);
    } catch (err: any) {
      setError(err.message || 'Publishing failed');
      setShowConfirm(false);
    } finally {
      setIsPublishing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400 gap-2">
        <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
        <span className="text-sm">Loading GitHub status…</span>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="p-6 rounded-xl bg-rose-950/20 border border-rose-800/50 space-y-3">
        <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
          <XCircle className="w-4 h-4" />
          GitHub Integration Error
        </div>
        <p className="text-xs text-rose-300">{error}</p>
        <button
          onClick={load}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3 h-3" /> Retry
        </button>
      </div>
    );
  }

  // Success state
  if (result) {
    return (
      <div className="bg-emerald-950/20 border border-emerald-800/50 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
          <CheckCircle2 className="w-5 h-5" />
          Successfully Published to GitHub
        </div>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-950/50 rounded-xl p-3 border border-slate-800">
            <div className="text-slate-500 uppercase text-[10px] font-semibold mb-1">Branch</div>
            <div className="font-mono text-cyan-300 flex items-center gap-1">
              <GitBranch className="w-3 h-3" />
              {result.branch}
            </div>
          </div>
          <div className="bg-slate-950/50 rounded-xl p-3 border border-slate-800">
            <div className="text-slate-500 uppercase text-[10px] font-semibold mb-1">Commit SHA</div>
            <div className="font-mono text-slate-200">{result.commit_sha}</div>
          </div>
          <div className="bg-slate-950/50 rounded-xl p-3 border border-slate-800">
            <div className="text-slate-500 uppercase text-[10px] font-semibold mb-1">Files Pushed</div>
            <div className="text-slate-200 font-semibold">{result.files_pushed}</div>
          </div>
          {result.pr_url && (
            <div className="bg-slate-950/50 rounded-xl p-3 border border-slate-800">
              <div className="text-slate-500 uppercase text-[10px] font-semibold mb-1">Pull Request</div>
              <a
                href={result.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-400 hover:text-purple-300 flex items-center gap-1 transition-colors"
              >
                <GitPullRequest className="w-3 h-3" />
                View PR
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
          )}
        </div>
        {result.commit_url && (
          <a
            href={result.commit_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 hover:border-cyan-700 transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
            View Commit on GitHub
          </a>
        )}
      </div>
    );
  }

  return (
    <>
      {showConfirm && status && diff && (
        <CommitConfirmModal
          status={status}
          diff={diff}
          branchName={branchName}
          commitMessage={commitMessage}
          createPr={createPr}
          isPublishing={isPublishing}
          onConfirm={handlePublish}
          onCancel={() => setShowConfirm(false)}
        />
      )}

      <div className="space-y-4">
        {/* Repo / token status banner */}
        {status && (
          <div className="flex items-center justify-between bg-slate-900/60 border border-slate-800 rounded-xl px-4 py-3">
            <div className="flex items-center gap-3">
              <GitBranch className="w-4 h-4 text-cyan-400" />
              <div>
                <div className="text-xs font-semibold text-slate-200">
                  {status.repository_owner}/{status.repository_name}
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  HEAD: {status.current_branch} · {status.head_commit_sha || 'n/a'}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {status.token_configured ? (
                <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded-lg border border-emerald-800/50">
                  <ShieldCheck className="w-3 h-3" />
                  Token Configured
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-[11px] text-amber-400 bg-amber-950/40 px-2 py-1 rounded-lg border border-amber-800/50">
                  <Lock className="w-3 h-3" />
                  No Token — Set GITHUB_TOKEN in .env
                </div>
              )}
              <button onClick={load} className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Changed files summary */}
        {diff && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 space-y-3">
            <button
              onClick={() => setShowDiffs(!showDiffs)}
              className="w-full flex items-center justify-between"
            >
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <FileCode className="w-4 h-4 text-cyan-400" />
                {diff.total_changed_files} File{diff.total_changed_files !== 1 ? 's' : ''} Changed
              </div>
              <Eye className={`w-3.5 h-3.5 transition-colors ${showDiffs ? 'text-cyan-400' : 'text-slate-500'}`} />
            </button>

            {showDiffs && (
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                {diff.changes.map((c) => (
                  <div
                    key={c.file_path}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950/50 border border-slate-800/60"
                  >
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                        c.change_type === 'add'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : c.change_type === 'delete'
                          ? 'bg-rose-950 text-rose-400 border border-rose-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}
                    >
                      {c.change_type.toUpperCase()}
                    </span>
                    <span className="font-mono text-xs text-slate-300 truncate">{c.file_path}</span>
                    {c.explanation && (
                      <span className="text-[10px] text-slate-500 italic truncate ml-auto">{c.explanation}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Form */}
        <div className="space-y-3">
          {/* Branch selector */}
          <div>
            <label className="block text-[11px] text-slate-400 font-semibold mb-1.5 flex items-center gap-1">
              <GitBranch className="w-3 h-3" /> Target Branch
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={branchName}
                onChange={(e) => setBranchName(e.target.value)}
                placeholder="feature/my-changes"
                className="flex-1 bg-slate-950 border border-slate-700 focus:border-cyan-500 rounded-xl px-3 py-2 text-xs font-mono text-slate-100 placeholder-slate-600 transition-colors outline-none"
              />
              {branches.length > 0 && (
                <select
                  value={branchName}
                  onChange={(e) => setBranchName(e.target.value)}
                  className="bg-slate-950 border border-slate-700 text-xs text-slate-300 rounded-xl px-2 py-2 focus:outline-none"
                >
                  <option value="">-- Existing branches --</option>
                  {branches.map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {/* Commit message */}
          <div>
            <label className="block text-[11px] text-slate-400 font-semibold mb-1.5 flex items-center gap-1">
              <GitCommit className="w-3 h-3" /> Commit Message
            </label>
            <textarea
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              rows={4}
              className="w-full bg-slate-950 border border-slate-700 focus:border-cyan-500 rounded-xl px-3 py-2 text-xs font-mono text-slate-100 placeholder-slate-600 transition-colors outline-none resize-none"
              placeholder="feat: describe your changes..."
            />
          </div>

          {/* Create PR toggle */}
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={createPr}
              onChange={(e) => setCreatePr(e.target.checked)}
              className="accent-cyan-500"
            />
            <span className="text-xs text-slate-300 flex items-center gap-1.5">
              <GitPullRequest className="w-3.5 h-3.5 text-purple-400" />
              Create pull request after push
            </span>
          </label>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-950/20 border border-rose-800/40 text-xs text-rose-300">
            <XCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        {/* Not configured warning */}
        {status && !status.token_configured && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-950/20 border border-amber-800/40 text-xs text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>
              GitHub token not configured. Set <code className="bg-slate-800 px-1 rounded">GITHUB_TOKEN</code> in{' '}
              <code className="bg-slate-800 px-1 rounded">backend/.env</code> to enable publishing.{' '}
              <strong>Never share your token in chat or terminal.</strong>
            </span>
          </div>
        )}

        {/* Publish button */}
        <button
          onClick={() => setShowConfirm(true)}
          disabled={
            !status?.token_configured ||
            !branchName.trim() ||
            !commitMessage.trim() ||
            isPublishing ||
            (diff?.total_changed_files === 0)
          }
          className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-semibold text-sm shadow-lg shadow-cyan-900/30 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <UploadCloud className="w-4 h-4" />
          Review & Publish to GitHub
        </button>

        <p className="text-[10px] text-slate-600 text-center">
          You will review all changes and explicitly confirm before anything is pushed.
        </p>
      </div>
    </>
  );
};
