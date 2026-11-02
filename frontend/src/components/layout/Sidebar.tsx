import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  FolderTree,
  MessageSquareCode,
  Bot,
  Network,
  Sparkles,
  BookOpen,
  ShieldCheck,
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Repositories', path: '/repositories', icon: FolderGit2 },
  { name: 'Code Explorer', path: '/explorer', icon: FolderTree },
  { name: 'AI Chat & RAG', path: '/chat', icon: MessageSquareCode },
  { name: 'Documentation', path: '/documentation', icon: BookOpen, badge: 'Agentic' },
  { name: 'Engineering Tasks', path: '/tasks', icon: Bot, badge: 'Agentic' },
  { name: 'Diagram Studio', path: '/architecture', icon: Network, badge: '10 Types' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950/60 backdrop-blur-md flex flex-col justify-between py-5 px-3 min-h-[calc(100vh-4rem)] select-none">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500 flex items-center justify-between">
          <span>Main Navigation</span>
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-500/60" />
        </div>
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs md:text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/15 via-cyan-500/10 to-transparent text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-950/40'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/80 hover:translate-x-0.5'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-1 rounded-lg transition-colors ${
                        isActive
                          ? 'text-cyan-400 bg-cyan-950/60'
                          : 'text-slate-400 group-hover:text-cyan-300 group-hover:bg-slate-850'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border transition-colors ${
                        isActive
                          ? 'bg-cyan-950/90 text-cyan-300 border-cyan-500/40 shadow-[0_0_10px_-2px_rgba(6,182,212,0.3)]'
                          : 'bg-slate-900 text-slate-400 border-slate-750 group-hover:text-cyan-300 group-hover:border-cyan-800'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </div>

      <div className="p-3.5 bg-gradient-to-br from-slate-900/90 to-slate-950/90 border border-slate-800/80 rounded-2xl shadow-lg relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-cyan-500/10 transition-colors" />
        <div className="flex items-center gap-2 text-xs text-slate-200 font-semibold mb-1.5">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>Human-in-the-Loop</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed font-normal">
          AI changes are isolated in staging workspaces with AST validation before approvals.
        </p>
      </div>
    </aside>
  );
};
