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
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Repositories', path: '/repositories', icon: FolderGit2 },
  { name: 'Code Explorer', path: '/explorer', icon: FolderTree },
  { name: 'AI Chat & RAG', path: '/chat', icon: MessageSquareCode },
  { name: 'Documentation Intelligence', path: '/documentation', icon: BookOpen, badge: 'Agentic' },
  { name: 'Engineering Tasks', path: '/tasks', icon: Bot, badge: 'Agentic' },
  { name: 'Diagram Studio', path: '/architecture', icon: Network, badge: '10 Types' },
];


export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/30 flex flex-col justify-between py-5 px-3 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Navigation
        </div>
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      <div className="p-3 bg-gradient-to-br from-slate-900 to-slate-850 border border-slate-800 rounded-xl">
        <div className="flex items-center gap-2 text-xs text-slate-300 font-semibold mb-1">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Human-in-the-Loop</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          AI changes are isolated in staging workspaces. Approvals required before merging.
        </p>
      </div>
    </aside>
  );
};
