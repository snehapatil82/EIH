import React from 'react';
import { FileCode, Plus, Minus } from 'lucide-react';
import { CodeChange } from '../../types/changes';
import { Badge } from '../common/Badge';

interface DiffViewerProps {
  change: CodeChange;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ change }) => {
  const lines = change.diff.split('\n');

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-xl mb-6">
      {/* File Diff Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FileCode className="w-4 h-4 text-cyan-400" />
          <span className="font-mono text-xs font-semibold text-slate-100">{change.file_path}</span>
          <Badge
            variant={
              change.change_type === 'add'
                ? 'success'
                : change.change_type === 'modify'
                ? 'info'
                : 'danger'
            }
          >
            {change.change_type.toUpperCase()}
          </Badge>
        </div>

        {change.explanation && (
          <span className="text-xs text-slate-400 italic max-w-md truncate">
            {change.explanation}
          </span>
        )}
      </div>

      {/* Diff Content */}
      <div className="p-3 font-mono text-xs overflow-x-auto max-h-96 leading-relaxed">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => {
              const isAdded = line.startsWith('+') && !line.startsWith('+++');
              const isRemoved = line.startsWith('-') && !line.startsWith('---');
              const isHunkHeader = line.startsWith('@@');

              let rowClass = 'hover:bg-slate-900/40 text-slate-300';
              let lineIcon = null;

              if (isAdded) {
                rowClass = 'bg-emerald-950/40 text-emerald-300 font-medium';
                lineIcon = <Plus className="w-3 h-3 text-emerald-400 inline mr-1" />;
              } else if (isRemoved) {
                rowClass = 'bg-rose-950/40 text-rose-300 font-medium';
                lineIcon = <Minus className="w-3 h-3 text-rose-400 inline mr-1" />;
              } else if (isHunkHeader) {
                rowClass = 'bg-cyan-950/50 text-cyan-400 font-semibold';
              }

              return (
                <tr key={idx} className={rowClass}>
                  <td className="w-8 pr-2 select-none text-right text-slate-400 text-[11px]">
                    {idx + 1}
                  </td>
                  <td className="whitespace-pre py-0.5 px-2">
                    {lineIcon}
                    {line || ' '}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
