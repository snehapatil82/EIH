import React, { useState } from 'react';
import { Github, GitBranch, ArrowRight } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface RepoConnectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (url: string, branch?: string) => Promise<void>;
  isLoading: boolean;
}

const PRESET_REPOS = [
  { name: 'fastapi/fastapi', url: 'https://github.com/fastapi/fastapi', branch: 'master' },
  { name: 'tiangolo/sqlmodel', url: 'https://github.com/tiangolo/sqlmodel', branch: 'main' },
  { name: 'encode/uvicorn', url: 'https://github.com/encode/uvicorn', branch: 'master' },
];

export const RepoConnectorModal: React.FC<RepoConnectorModalProps> = ({
  isOpen,
  onClose,
  onConnect,
  isLoading,
}) => {
  const [url, setUrl] = useState('');
  const [branch, setBranch] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setError('Please enter a valid GitHub repository URL');
      return;
    }
    setError(null);
    try {
      await onConnect(url.trim(), branch.trim() || undefined);
      setUrl('');
      setBranch('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to connect repository');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Connect GitHub Repository">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 text-xs text-rose-300 bg-rose-950/60 border border-rose-800 rounded-lg">
            {error}
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
            GitHub Repository URL
          </label>
          <div className="relative">
            <Github className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="https://github.com/owner/repository"
              className="w-full bg-slate-950 border border-slate-750 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 transition-colors"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
            Branch / Tag (Optional)
          </label>
          <div className="relative">
            <GitBranch className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="main, master, or v1.0"
              className="w-full bg-slate-950 border border-slate-750 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 transition-colors"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              disabled={isLoading}
            />
          </div>
        </div>

        <div className="pt-2">
          <label className="block text-xs text-slate-400 mb-2 font-medium">Quick Presets:</label>
          <div className="flex flex-wrap gap-2">
            {PRESET_REPOS.map((preset) => (
              <button
                key={preset.name}
                type="button"
                className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-750 text-cyan-400 border border-slate-700 transition-colors"
                onClick={() => {
                  setUrl(preset.url);
                  setBranch(preset.branch);
                }}
              >
                {preset.name}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
          <Button variant="outline" type="button" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="primary" type="submit" isLoading={isLoading} rightIcon={<ArrowRight className="w-4 h-4" />}>
            Clone & Index Repo
          </Button>
        </div>
      </form>
    </Modal>
  );
};
