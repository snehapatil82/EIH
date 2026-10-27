import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  FileText,
  Edit3,
  Eye,
  Save,
  RefreshCw,
  Download,
  Copy,
  Check,
  ShieldCheck,
  AlertTriangle,
  History,
  Sparkles,
  ExternalLink,
  RotateCcw,
  BookOpen,
  X,
  Bot,
  FileCheck2,
} from 'lucide-react';
import {
  DocumentationItem,
  DocumentationVersion,
  DocumentationValidationResult,
  DocumentationAIActionResult,
  CitationItem,
} from '../../types/documentation';
import { documentationService } from '../../services/documentationService';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { CitationBadge } from '../chat/CitationBadge';

interface DocEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: DocumentationItem;
  repositoryId: string;
  onSaved: (updatedItem: DocumentationItem) => void;
  onRegenerate: (item: DocumentationItem) => void;
}

export const DocEditorModal: React.FC<DocEditorModalProps> = ({
  isOpen,
  onClose,
  item,
  repositoryId,
  onSaved,
  onRegenerate,
}) => {
  const [content, setContent] = useState(item.content);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'validation' | 'citations' | 'versions'>('preview');
  const [isSaving, setIsSaving] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<DocumentationValidationResult | null>(null);
  const [versions, setVersions] = useState<DocumentationVersion[]>([]);
  const [isCopied, setIsCopied] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);

  // AI Actions state
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [aiAction, setAiAction] = useState('summarize');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<DocumentationAIActionResult | null>(null);
  const [showAiModal, setShowAiModal] = useState(false);

  useEffect(() => {
    setContent(item.content);
    if (isOpen) {
      loadVersions();
    }
  }, [item, isOpen]);

  const loadVersions = async () => {
    try {
      const vList = await documentationService.getVersions(repositoryId, item.id);
      setVersions(vList);
    } catch (e) {
      console.error('Failed to load doc versions:', e);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await documentationService.update(
        repositoryId,
        item.id,
        content,
        'Manual user revision from Documentation Workspace'
      );
      onSaved(updated);
      setIsEditing(false);
      await loadVersions();
    } catch (e) {
      console.error('Save failed:', e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const res = await documentationService.validate(repositoryId, item.id);
      setValidationResult(res);
      setActiveTab('validation');
    } catch (e) {
      console.error('Validation failed:', e);
    } finally {
      setIsValidating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${item.doc_type}_${item.repository_id.substring(0, 8)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleRevertVersion = async (version: DocumentationVersion) => {
    try {
      const reverted = await documentationService.revertVersion(repositoryId, item.id, version.id);
      setContent(reverted.content);
      onSaved(reverted);
      setIsEditing(false);
      setActiveTab('preview');
    } catch (e) {
      console.error('Revert failed:', e);
    }
  };

  const handleRunAIAction = async () => {
    setIsAiLoading(true);
    try {
      const res = await documentationService.executeAIAction(
        repositoryId,
        item.id,
        aiAction,
        window.getSelection()?.toString() || undefined
      );
      setAiResult(res);
    } catch (e) {
      console.error('AI action failed:', e);
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleApplyAiResult = () => {
    if (!aiResult) return;
    setContent((prev) => prev + '\n\n' + aiResult.result);
    setAiResult(null);
    setShowAiModal(false);
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      await onRegenerate(item);
    } finally {
      setIsRegenerating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="flex flex-col w-full max-w-6xl h-[92vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-950/80 text-cyan-400 border border-cyan-800/80">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100">{item.title}</h2>
                <Badge
                  variant={
                    item.status === 'up_to_date'
                      ? 'success'
                      : item.status === 'outdated'
                      ? 'danger'
                      : 'warning'
                  }
                  size="sm"
                >
                  {item.status.replace(/_/g, ' ').toUpperCase()}
                </Badge>
                {item.validation_status === 'passed' && (
                  <Badge variant="cyan" size="sm">
                    ✓ AST VERIFIED
                  </Badge>
                )}
              </div>
              <p className="text-xs text-slate-400">
                Repository Workspace Document • {item.citations?.length || 0} Ground Truth Citations
              </p>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAiModal(true)}
              leftIcon={<Sparkles className="w-3.5 h-3.5 text-cyan-400" />}
              className="text-xs border-cyan-800/60 text-cyan-300 hover:bg-cyan-950/50"
            >
              AI Actions
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleRegenerate}
              isLoading={isRegenerating}
              leftIcon={<RefreshCw className="w-3.5 h-3.5 text-amber-400" />}
              className="text-xs border-amber-800/50 text-amber-300 hover:bg-amber-950/40"
            >
              Regenerate
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleValidate}
              isLoading={isValidating}
              leftIcon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
              className="text-xs"
            >
              Validate
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              leftIcon={isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              {isCopied ? 'Copied' : 'Copy'}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              leftIcon={<Download className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              Download
            </Button>

            {isEditing ? (
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
                isLoading={isSaving}
                leftIcon={<Save className="w-3.5 h-3.5" />}
                className="text-xs"
              >
                Save Changes
              </Button>
            ) : (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsEditing(true)}
                leftIcon={<Edit3 className="w-3.5 h-3.5" />}
                className="text-xs"
              >
                Edit Markdown
              </Button>
            )}

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-slate-800 transition-colors ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Subheader Navigation */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-slate-950/40 border-b border-slate-800/80 text-xs">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setIsEditing(false);
                setActiveTab('preview');
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                !isEditing && activeTab === 'preview'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              Document Preview
            </button>

            <button
              onClick={() => setIsEditing(true)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                isEditing
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Edit3 className="w-3.5 h-3.5" />
              Markdown Editor
            </button>

            <button
              onClick={() => {
                setIsEditing(false);
                setActiveTab('validation');
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                !isEditing && activeTab === 'validation'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Validation Report
            </button>

            <button
              onClick={() => {
                setIsEditing(false);
                setActiveTab('citations');
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                !isEditing && activeTab === 'citations'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileCheck2 className="w-3.5 h-3.5" />
              Source Citations ({item.citations?.length || 0})
            </button>

            <button
              onClick={() => {
                setIsEditing(false);
                setActiveTab('versions');
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                !isEditing && activeTab === 'versions'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Version History ({versions.length})
            </button>
          </div>

          <div className="flex items-center gap-3 text-slate-400">
            <span>Lines: {content.split('\n').length}</span>
            <span>Words: {content.split(/\s+/).filter(Boolean).length}</span>
          </div>
        </div>

        {/* Main Content Workspace */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-900/40">
          {isEditing ? (
            <div className="h-full flex flex-col space-y-2">
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write technical documentation in Markdown..."
                className="w-full flex-1 p-5 font-mono text-xs leading-relaxed bg-slate-950 text-slate-100 border border-slate-800 rounded-xl focus:border-cyan-500 focus:outline-none resize-none selection:bg-cyan-500 selection:text-white"
              />
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>Markdown mode enabled. Use GitHub-Flavored Markdown syntax.</span>
                <Button size="sm" variant="primary" onClick={handleSave} isLoading={isSaving}>
                  Save & Validate
                </Button>
              </div>
            </div>
          ) : activeTab === 'preview' ? (
            <div className="prose prose-invert prose-cyan max-w-none text-slate-200 text-sm leading-relaxed space-y-4">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ node, ...props }) => <h1 className="text-2xl font-bold text-slate-100 border-b border-slate-800 pb-3 mb-4" {...props} />,
                  h2: ({ node, ...props }) => <h2 className="text-xl font-semibold text-slate-100 border-b border-slate-800/60 pb-2 mt-6 mb-3" {...props} />,
                  h3: ({ node, ...props }) => <h3 className="text-base font-semibold text-cyan-300 mt-4 mb-2" {...props} />,
                  table: ({ node, ...props }) => <div className="overflow-x-auto my-4"><table className="w-full text-xs text-left border border-slate-800 rounded-lg overflow-hidden" {...props} /></div>,
                  th: ({ node, ...props }) => <th className="p-2.5 bg-slate-950 font-semibold text-slate-300 border-b border-slate-800" {...props} />,
                  td: ({ node, ...props }) => <td className="p-2.5 border-b border-slate-850/80 font-mono text-[11px]" {...props} />,
                  code: ({ node, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    return (
                      <code className="px-1.5 py-0.5 rounded bg-slate-950 text-cyan-300 font-mono text-xs border border-slate-800" {...props}>
                        {children}
                      </code>
                    );
                  },
                  pre: ({ node, ...props }) => (
                    <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs overflow-x-auto font-mono text-slate-300 my-4" {...props} />
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          ) : activeTab === 'validation' ? (
            <div className="space-y-6 max-w-4xl mx-auto">
              <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    Ground Truth Repository Verification
                  </h3>
                  <Badge variant={validationResult?.passed !== false ? 'success' : 'danger'}>
                    {validationResult?.status?.toUpperCase() || 'EVALUATED'}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-center">
                    <span className="text-lg font-bold text-emerald-400">
                      {validationResult?.verified_claims ?? item.validation_details?.verified_claims ?? 0}
                    </span>
                    <span className="block text-[11px] text-slate-400">Claims Verified</span>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-center">
                    <span className="text-lg font-bold text-cyan-400">
                      {validationResult?.verified_files ?? item.validation_details?.verified_files ?? 0}
                    </span>
                    <span className="block text-[11px] text-slate-400">Files Grounded</span>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-center">
                    <span className="text-lg font-bold text-indigo-400">
                      {validationResult?.verified_apis ?? item.validation_details?.verified_apis ?? 0}
                    </span>
                    <span className="block text-[11px] text-slate-400">APIs Confirmed</span>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-center">
                    <span className="text-lg font-bold text-amber-400">
                      {validationResult?.outdated_references ?? item.validation_details?.outdated_references ?? 0}
                    </span>
                    <span className="block text-[11px] text-slate-400">Outdated References</span>
                  </div>
                </div>
              </div>

              {/* Claims Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Individual Verified Claims & AST Symbols
                </h4>
                <div className="space-y-2">
                  {(validationResult?.claims || item.validation_details?.claims || []).map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        {c.exists ? (
                          <span className="text-emerald-400 font-bold">✓</span>
                        ) : (
                          <span className="text-rose-400 font-bold">⚠</span>
                        )}
                        <span className="font-mono text-slate-200">`{c.reference}`</span>
                        <span className="text-slate-400">• {c.details}</span>
                      </div>
                      <Badge variant={c.exists ? 'cyan' : 'danger'} size="sm">
                        {c.type.toUpperCase()}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : activeTab === 'citations' ? (
            <div className="space-y-4 max-w-4xl mx-auto">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-100">
                  Repository Citations & Evidence ({item.citations?.length || 0})
                </h3>
                <span className="text-xs text-slate-400">
                  Click any citation badge to view verified line-by-line repository source code.
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(item.citations || []).map((cit, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 hover:border-cyan-800 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <CitationBadge
                        citation={{
                          file_path: cit.file_path,
                          start_line: cit.start_line,
                          end_line: cit.end_line,
                          snippet: cit.snippet || '',
                          score: cit.score,
                        }}

                      />
                      {cit.score && (
                        <span className="text-[10px] text-cyan-400 font-mono">
                          {(cit.score * 100).toFixed(0)}% Match
                        </span>
                      )}
                    </div>
                    {cit.snippet && (
                      <div className="bg-slate-900 p-2.5 rounded text-[11px] font-mono text-slate-300 max-h-28 overflow-y-auto line-clamp-4">
                        {cit.snippet}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4 max-w-3xl mx-auto">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-100">Revision History</h3>
                <span className="text-xs text-slate-400">Tracked changes, commits, and regenerations</span>
              </div>

              <div className="space-y-3">
                {versions.map((v) => (
                  <div
                    key={v.id}
                    className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-cyan-300">{v.version_tag}</span>
                        <span className="text-xs text-slate-300">{v.change_summary}</span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {new Date(v.created_at).toLocaleString()} • {v.content.split('\n').length} lines
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRevertVersion(v)}
                      leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                      className="text-xs"
                    >
                      Revert to this
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* AI Actions Modal */}
      {showAiModal && (
        <Modal
          isOpen={showAiModal}
          onClose={() => setShowAiModal(false)}
          title={`Documentation AI Copilot: ${item.title}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            <p className="text-xs text-slate-400">
              Select an autonomous technical action to enhance, simplify, or audit this document.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[
                { id: 'summarize', label: 'Summarize Section' },
                { id: 'expand', label: 'Expand Technical Depth' },
                { id: 'simplify', label: 'Simplify Concepts' },
                { id: 'find_inconsistencies', label: 'Find Inconsistencies' },
                { id: 'explain_section', label: 'Architectural Explanation' },
                { id: 'update_from_code', label: 'Sync with Latest Code' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setAiAction(opt.id)}
                  className={`p-2.5 rounded-lg text-xs font-medium border text-left transition-all ${
                    aiAction === opt.id
                      ? 'bg-cyan-950 text-cyan-300 border-cyan-800'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <Button
              variant="primary"
              onClick={handleRunAIAction}
              isLoading={isAiLoading}
              leftIcon={<Sparkles className="w-3.5 h-3.5" />}
              className="w-full text-xs"
            >
              Execute AI Action
            </Button>

            {aiResult && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 pt-3">
                <div className="flex items-center justify-between text-xs text-cyan-400 font-semibold">
                  <span>AI Result ({aiResult.action})</span>
                  <span>{aiResult.explanation}</span>
                </div>
                <div className="prose prose-invert prose-xs text-slate-300 bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{aiResult.result}</ReactMarkdown>
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" size="sm" onClick={() => setAiResult(null)}>
                    Discard
                  </Button>
                  <Button variant="primary" size="sm" onClick={handleApplyAiResult}>
                    Apply to Document
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
