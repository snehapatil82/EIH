import React, { useState } from 'react';
import { Copy, Check, FileCode, Layers } from 'lucide-react';
import { FileContent } from '../../types/repository';

interface CodeViewerProps {
  file: FileContent | null;
  highlightLine?: number;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ file, highlightLine }) => {
  const [copied, setCopied] = useState(false);

  if (!file) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-12 text-center text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800">
        <FileCode className="w-12 h-12 text-slate-600 mb-3" />
        <p className="text-sm font-medium text-slate-300">No file selected</p>
        <p className="text-xs text-slate-400 mt-1">
          Select a file from the repository tree to view its source code and AST symbols.
        </p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(file.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = file.content.split('\n');

  return (
    <div className="flex flex-col h-full bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-xl">
      {/* File Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono text-slate-200 font-semibold">{file.path}</span>
          <span className="text-[11px] text-slate-400">
            ({file.line_count} lines, {(file.size_bytes / 1024).toFixed(1)} KB)
          </span>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-750 px-2.5 py-1 rounded transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      {/* Code Area with line numbers */}
      <div className="flex-1 overflow-auto p-4 font-mono text-xs text-slate-200 leading-relaxed">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => {
              const lineNum = idx + 1;
              const isHighlighted = highlightLine === lineNum;
              return (
                <tr
                  key={idx}
                  className={`${isHighlighted ? 'bg-cyan-950/60 text-cyan-200 font-semibold' : 'hover:bg-slate-900/50'}`}
                >
                  <td className="w-12 pr-4 text-right select-none text-slate-400 text-[11px]">
                    {lineNum}
                  </td>
                  <td className="whitespace-pre">{line || ' '}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
