import React from 'react';
import { GitBranch, FolderGit2, Cpu, ChevronDown } from 'lucide-react';
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
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/75 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-30 transition-colors">
      <div className="flex items-center gap-3.5">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-sky-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 border border-cyan-400/30">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-slate-100 tracking-tight text-sm md:text-base">
              Engineering Intelligence Hub
            </h1>
            <Badge variant="cyan" size="sm" dot>
              v1.0 Autonomous
            </Badge>
          </div>
          <p className="text-xs text-slate-400 font-normal">
            Agentic Codebase Understanding & Automation Platform
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3.5">
        {repositories.length > 0 && (
          <div className="relative flex items-center gap-2 bg-slate-900/90 hover:bg-slate-850 px-3 py-1.5 rounded-xl border border-slate-750/90 hover:border-slate-600 shadow-sm transition-all group">
            <FolderGit2 className="w-4 h-4 text-cyan-400" />
            <select
              className="bg-transparent text-xs md:text-sm font-medium text-slate-200 focus:outline-none cursor-pointer pr-6 appearance-none"
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
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 pointer-events-none group-hover:text-slate-200 transition-colors" />

            {selectedRepo && (
              <div className="hidden sm:flex items-center gap-1.5 border-l border-slate-750 pl-2 text-xs text-slate-400">
                <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-mono text-[11px] text-slate-300">{selectedRepo.default_branch}</span>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center gap-2 text-xs font-mono text-emerald-300 bg-emerald-950/60 border border-emerald-500/30 px-3 py-1.5 rounded-full shadow-[0_0_15px_-3px_rgba(16,185,129,0.2)]">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="hidden sm:inline font-sans text-xs font-medium">Multi-Agent Ready</span>
        </div>
      </div>
    </header>
  );
};
