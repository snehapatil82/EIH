import React from 'react';
import {
  AlertTriangle,
  FileWarning,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Search,
  CheckCircle,
  RefreshCw,
} from 'lucide-react';
import { DocumentationGap } from '../../types/documentation';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface DocGapsPanelProps {
  gaps: DocumentationGap[];
  onGenerateDocForGap: (gap: DocumentationGap) => void;
  onRefreshGaps: () => void;
  isLoading?: boolean;
  resolvingGapId?: string | null;
}

export const DocGapsPanel: React.FC<DocGapsPanelProps> = ({
  gaps,
  onGenerateDocForGap,
  onRefreshGaps,
  isLoading = false,
  resolvingGapId = null,
}) => {
  const openGaps = gaps.filter((g) => g.status === 'open');
  const resolvedGaps = gaps.filter((g) => g.status === 'resolved');

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatGapType = (type: string) => {
    return type
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-950/70 text-amber-400 border border-amber-800/60">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              Autonomous Documentation Gap Detection
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-950 text-amber-400 border border-amber-800">
                {openGaps.length} Gaps Detected
              </span>
              {resolvedGaps.length > 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" />
                  {resolvedGaps.length} Resolved
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-400">
              Static AST inspection identified missing API schemas, undocumented modules, and outdated specifications.
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onRefreshGaps}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          className="text-xs"
        >
          Rescan Repository
        </Button>
      </div>

      {openGaps.length === 0 ? (
        <div className="py-10 text-center bg-slate-950/50 rounded-xl border border-slate-800/80 space-y-2">
          <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto" />
          <h4 className="text-sm font-semibold text-slate-200">Zero Documentation Gaps Detected</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            All detected modules, configuration manifests, and API endpoints are verified and synchronized.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-1">
          {openGaps.map((gap) => (
            <div
              key={gap.id}
              className="flex flex-col justify-between p-4 rounded-xl bg-slate-950/70 border border-slate-800/90 hover:border-amber-700/60 transition-all group"
            >
              <div className="space-y-2 mb-3">
                <div className="flex items-center justify-between gap-2">
                  <Badge variant={getSeverityVariant(gap.severity)} size="sm">
                    {gap.severity.toUpperCase()} PRIORITY
                  </Badge>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">
                    {formatGapType(gap.gap_type)}
                  </span>
                </div>

                <h4 className="text-xs font-semibold text-slate-100 group-hover:text-amber-300 transition-colors">
                  {gap.title}
                </h4>

                <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
                  {gap.description}
                </p>

                {gap.file_path && (
                  <div className="text-[10px] font-mono text-slate-400 truncate bg-slate-900 px-2 py-1 rounded border border-slate-800">
                    File: <span className="text-slate-300">{gap.file_path}</span>
                  </div>
                )}
              </div>

              <Button
                variant="primary"
                size="sm"
                onClick={() => onGenerateDocForGap(gap)}
                isLoading={resolvingGapId === gap.id}
                disabled={Boolean(resolvingGapId)}
                className="w-full text-xs"
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                {resolvingGapId === gap.id ? 'Resolving & Generating...' : 'Resolve & Regenerate'}
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
