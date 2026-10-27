import React from 'react';
import { ShieldCheck, Award, Wrench, AlertCircle, Info } from 'lucide-react';
import { ReviewResult } from '../../types/changes';

interface ReviewScorecardProps {
  review?: ReviewResult;
}

export const ReviewScorecard: React.FC<ReviewScorecardProps> = ({ review }) => {
  if (!review) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Automated Quality & Security Audit
        </h4>
        <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-0.5 rounded">
          {review.status.toUpperCase()}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
          <div className="flex items-center justify-center gap-1 text-cyan-400 text-xs font-medium mb-1">
            <Award className="w-3.5 h-3.5" />
            <span>Code Quality</span>
          </div>
          <span className="text-xl font-bold font-mono text-slate-100">{review.quality_score}%</span>
        </div>

        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
          <div className="flex items-center justify-center gap-1 text-emerald-400 text-xs font-medium mb-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Security Audit</span>
          </div>
          <span className="text-xl font-bold font-mono text-slate-100">{review.security_score}%</span>
        </div>

        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center">
          <div className="flex items-center justify-center gap-1 text-purple-400 text-xs font-medium mb-1">
            <Wrench className="w-3.5 h-3.5" />
            <span>Maintainability</span>
          </div>
          <span className="text-xl font-bold font-mono text-slate-100">{review.maintainability_score}%</span>
        </div>
      </div>

      {review.comments.length > 0 && (
        <div className="space-y-2 pt-2">
          <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Audit Findings & Comments
          </h5>
          {review.comments.map((c, i) => (
            <div
              key={i}
              className="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-xs flex items-start gap-2 text-slate-300"
            >
              <Info className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">[{c.file}]:</span> {c.message}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
