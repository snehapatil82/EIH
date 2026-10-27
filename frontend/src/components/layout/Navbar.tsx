import React from 'react';
import { GitBranch, FolderGit2, Cpu, Activity } from 'lucide-react';
import { Repository } from '../../types/repository';
import { Badge } from '../common/Badge';

interface NavbarProps {
  repositories: Repository[];
  selectedRepo: Repository | null;
  onSelectRepo: (repo: Repository) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  repositories,
  selectedRepo,
  onSelectRepo,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-900/40">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-slate-100 tracking-tight text-base">
              Engineering Intelligence Hub
            </h1>
            <Badge variant="cyan" size="sm">v1.0 Autonomous</Badge>
          </div>
          <p className="text-xs text-slate-400">Agentic Codebase Understanding & Automation</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {repositories.length > 0 && (
          <div className="flex items-center gap-2 bg-slate-850 px-3 py-1.5 rounded-lg border border-slate-750">
            <FolderGit2 className="w-4 h-4 text-slate-400" />
            <select
              className="bg-transparent text-sm text-slate-200 focus:outline-none cursor-pointer"
              value={selectedRepo?.id || ''}
              onChange={(e) => {
                const found = repositories.find((r) => r.id === e.target.value);
                if (found) onSelectRepo(found);
              }}
            >
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id} className="bg-slate-900 text-slate-100">
                  {repo.owner}/{repo.name}
                </option>
              ))}
            </select>

            {selectedRepo && (
              <div className="flex items-center gap-1.5 border-l border-slate-700 pl-2 text-xs text-slate-400">
                <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
                <span>{selectedRepo.default_branch}</span>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/60 px-2.5 py-1 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Multi-Agent Ready</span>
        </div>
      </div>
    </header>
  );
};
