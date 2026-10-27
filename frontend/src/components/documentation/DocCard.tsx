import React from 'react';
import {
  BookOpen,
  FileText,
  Terminal,
  Settings,
  Layers,
  HelpCircle,
  Database,
  Code2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Eye,
  FileCheck2,
} from 'lucide-react';
import { DocumentationItem, DocStatus } from '../../types/documentation';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface DocCardProps {
  item: DocumentationItem;
  onView: (item: DocumentationItem) => void;
  onGenerate: (item: DocumentationItem) => void;
  isLoading?: boolean;
}

const getDocIcon = (docType: string) => {
  switch (docType) {
    case 'readme':
    case 'project_overview':
      return BookOpen;
    case 'installation_guide':
      return Terminal;
    case 'configuration_guide':
      return Settings;
    case 'deployment_guide':
      return Layers;
    case 'troubleshooting_guide':
      return HelpCircle;
    case 'api_documentation':
      return Code2;
    case 'architecture_documentation':
      return Layers;
    case 'database_documentation':
      return Database;
    case 'testing_documentation':
      return ShieldCheck;
    default:
      return FileText;
  }
};

const getStatusBadge = (status: DocStatus) => {
  switch (status) {
    case 'up_to_date':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/70 text-emerald-400 border border-emerald-800/80">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Up to date
        </span>
      );
    case 'update_recommended':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/70 text-amber-300 border border-amber-800/80">
          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
          Update recommended
        </span>
      );
    case 'outdated':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/70 text-rose-300 border border-rose-800/80">
          <span className="w-2 h-2 rounded-full bg-rose-400"></span>
          Outdated
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800/70 text-slate-400 border border-slate-700">
          <span className="w-2 h-2 rounded-full bg-slate-500"></span>
          Not generated
        </span>
      );
  }
};

export const DocCard: React.FC<DocCardProps> = ({
  item,
  onView,
  onGenerate,
  isLoading = false,
}) => {
  const Icon = getDocIcon(item.doc_type);
  const isGenerated = Boolean(item.content && item.content.trim().length > 0);

  const formattedDate = item.last_generated_at
    ? new Date(item.last_generated_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  return (
    <div
      className={`group relative flex flex-col justify-between rounded-xl p-5 transition-all duration-200 border ${
        item.status === 'outdated'
          ? 'bg-rose-950/10 border-rose-900/50 hover:border-rose-700/80'
          : item.status === 'update_recommended'
          ? 'bg-amber-950/10 border-amber-900/50 hover:border-amber-700/80'
          : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
      } hover:shadow-xl hover:shadow-cyan-950/20`}
    >
      <div>
        {/* Top Meta Bar */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-cyan-950/70 text-cyan-400 border border-cyan-800/60 group-hover:scale-105 transition-transform">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap mb-0.5">
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                  {item.category === 'project' ? 'Project Documentation' : 'Technical Specification'}
                </span>
                {item.is_ai_generated && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-950/90 text-purple-300 border border-purple-700/80">
                    <Sparkles className="w-2.5 h-2.5 text-purple-400" />
                    AI Generated
                  </span>
                )}
              </div>
              <h3 className="text-base font-semibold text-slate-100 group-hover:text-cyan-300 transition-colors">
                {item.title}
              </h3>
            </div>
          </div>
          {getStatusBadge(item.status)}
        </div>

        {/* Source File if AI generated for specific module */}
        {item.source_file && (
          <div className="mb-2 text-[10px] font-mono text-slate-400 bg-slate-950/80 px-2 py-1 rounded border border-slate-800/80 truncate">
            Source: <span className="text-cyan-400">{item.source_file}</span>
          </div>
        )}

        {/* Description */}
        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-4">
          {item.description || 'Repository-aware technical specification grounded in source code.'}
        </p>

        {/* Impact Warning Banner if outdated */}
        {item.status === 'outdated' && item.impact_reason && (
          <div className="mb-4 p-2.5 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="leading-snug">
              <strong className="font-semibold block text-[11px] uppercase tracking-wider text-rose-200">
                Documentation Sync Required
              </strong>
              <span>{item.impact_reason}</span>
            </div>
          </div>
        )}

        {/* Verification & Metadata tags */}
        <div className="flex items-center gap-3 text-xs text-slate-400 py-2 border-t border-slate-800/80 mb-4 flex-wrap">
          {isGenerated ? (
            <>
              <div className="flex items-center gap-1.5 font-medium">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Generated {formattedDate}</span>
              </div>

              {item.validation_status === 'passed' && (
                <div className="flex items-center gap-1 text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>
                    {item.validation_details?.verified_claims || 0} claims verified
                  </span>
                </div>
              )}

              {item.citations && item.citations.length > 0 && (
                <div className="flex items-center gap-1 text-cyan-400 font-medium">
                  <FileCheck2 className="w-3.5 h-3.5" />
                  <span>{item.citations.length} citations</span>
                </div>
              )}
            </>
          ) : (
            <span className="text-slate-400 italic">No document generated yet.</span>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex items-center gap-2 pt-2 border-t border-slate-800/60">
        {isGenerated ? (
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onView(item)}
              className="flex-1 text-xs"
              leftIcon={<Eye className="w-3.5 h-3.5" />}
            >
              View & Edit
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onGenerate(item)}
              isLoading={isLoading}
              className="text-xs"
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Regenerate
            </Button>
          </>
        ) : (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onGenerate(item)}
            isLoading={isLoading}
            className="w-full text-xs"
            leftIcon={<Sparkles className="w-3.5 h-3.5 text-cyan-200" />}
          >
            Generate Documentation
          </Button>
        )}
      </div>
    </div>
  );
};
