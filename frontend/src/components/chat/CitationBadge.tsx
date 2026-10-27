import React, { useState } from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import { Citation } from '../../types/chat';
import { Modal } from '../common/Modal';

interface CitationBadgeProps {
  citation: Citation;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation }) => {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const lineRangeStr =
    citation.start_line && citation.end_line
      ? `:${citation.start_line}-${citation.end_line}`
      : '';

  return (
    <>
      <button
        onClick={() => setIsPreviewOpen(true)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-800/80 transition-all hover:scale-[1.02] shadow-sm"
      >
        <FileText className="w-3.5 h-3.5 text-cyan-400" />
        <span className="font-semibold">{citation.file_path}{lineRangeStr}</span>
        <ExternalLink className="w-3 h-3 text-cyan-500 opacity-60" />
      </button>

      <Modal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        title={`Source Evidence: ${citation.file_path}${lineRangeStr}`}
        maxWidth="2xl"
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
            <span>Repository Relative Path: <strong className="text-slate-200">{citation.file_path}</strong></span>
            {citation.score && <span>Relevance Score: {(citation.score * 100).toFixed(0)}%</span>}
          </div>

          <div className="bg-slate-950 p-4 rounded-lg font-mono text-xs text-slate-200 overflow-x-auto max-h-96 border border-slate-800 leading-relaxed whitespace-pre">
            {citation.snippet}
          </div>
        </div>
      </Modal>
    </>
  );
};
