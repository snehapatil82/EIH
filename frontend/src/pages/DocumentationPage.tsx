import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Sparkles,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  RefreshCw,
  FolderTree,
  Filter,
  Flame,
  FileCode,
} from 'lucide-react';
import { Repository } from '../types/repository';
import {
  DocumentationDashboard,
  DocumentationItem,
  DocumentationCoverage,
  DocumentationGap,
  DocumentationSearchMatch,
} from '../types/documentation';
import { documentationService } from '../services/documentationService';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Spinner } from '../components/common/Spinner';
import { DocCard } from '../components/documentation/DocCard';
import { DocGapsPanel } from '../components/documentation/DocGapsPanel';
import { DocEditorModal } from '../components/documentation/DocEditorModal';

interface DocumentationPageProps {
  selectedRepo: Repository | null;
}

export const DocumentationPage: React.FC<DocumentationPageProps> = ({ selectedRepo }) => {
  const [dashboard, setDashboard] = useState<DocumentationDashboard | null>(null);
  const [items, setItems] = useState<DocumentationItem[]>([]);
  const [coverage, setCoverage] = useState<DocumentationCoverage | null>(null);
  const [gaps, setGaps] = useState<DocumentationGap[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState<'all' | 'project' | 'technical' | 'outdated' | 'ai_generated'>('all');
  const [resolvingGapId, setResolvingGapId] = useState<string | null>(null);
  const [generatingDocType, setGeneratingDocType] = useState<string | null>(null);

  // Toast notification
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Editor Modal
  const [activeItem, setActiveItem] = useState<DocumentationItem | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<DocumentationSearchMatch[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Change Impact Sync
  const [isSyncingImpact, setIsSyncingImpact] = useState(false);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    if (!selectedRepo) return;
    loadAllDocumentationData();
  }, [selectedRepo]);

  const loadAllDocumentationData = async () => {
    if (!selectedRepo) return;
    setIsLoading(true);
    try {
      const [dashData, itemsData, covData, gapsData] = await Promise.all([
        documentationService.getDashboard(selectedRepo.id),
        documentationService.list(selectedRepo.id),
        documentationService.getCoverage(selectedRepo.id),
        documentationService.getGaps(selectedRepo.id),
      ]);
      setDashboard(dashData);
      setItems(itemsData);
      setCoverage(covData);
      setGaps(gapsData);
    } catch (err) {
      console.error('Failed to load documentation data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async (item: DocumentationItem) => {
    if (!selectedRepo) return;
    setGeneratingDocType(item.doc_type);
    try {
      const generated = await documentationService.generate(selectedRepo.id, item.doc_type);
      setItems((prev) =>
        prev.map((i) =>
          i.id === generated.id || i.doc_type === generated.doc_type ? generated : i
        )
      );
      // Update modal activeItem if it's the same document
      if (activeItem && (activeItem.id === generated.id || activeItem.doc_type === generated.doc_type)) {
        setActiveItem(generated);
      }
      showToast(`✓ "${item.title}" generated successfully`, 'success');
      // Refresh statistics and coverage asynchronously without disruptive page reload
      documentationService.getDashboard(selectedRepo.id).then(setDashboard).catch(() => {});
      documentationService.getCoverage(selectedRepo.id).then(setCoverage).catch(() => {});
      documentationService.getGaps(selectedRepo.id).then(setGaps).catch(() => {});
    } catch (err) {
      console.error('Doc generation failed:', err);
      showToast(`Failed to generate "${item.title}". Please try again.`, 'error');
    } finally {
      setGeneratingDocType(null);
    }
  };

  const handleOpenEditor = (item: DocumentationItem) => {
    setActiveItem(item);
    setIsEditorOpen(true);
  };

  const handleItemSaved = (updatedItem: DocumentationItem) => {
    setActiveItem(updatedItem);
    setItems((prev) =>
      prev.map((i) =>
        i.id === updatedItem.id || i.doc_type === updatedItem.doc_type ? updatedItem : i
      )
    );
    documentationService.getDashboard(selectedRepo?.id || '').then(setDashboard).catch(() => {});
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRepo || !searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await documentationService.search(selectedRepo.id, searchQuery.trim());
      setSearchResults(res.results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSyncChangeImpact = async () => {
    if (!selectedRepo) return;
    setIsSyncingImpact(true);
    try {
      await documentationService.syncChangeImpact(selectedRepo.id);
      await loadAllDocumentationData();
      showToast('Change impact synced successfully', 'success');
    } catch (err) {
      console.error('Sync impact failed:', err);
      showToast('Failed to sync change impact', 'error');
    } finally {
      setIsSyncingImpact(false);
    }
  };

  const handleGenerateAll = async () => {
    if (!selectedRepo) return;
    setIsLoading(true);
    const toGenerate = items.filter(
      (i) => i.status === 'not_generated' || i.status === 'outdated'
    );
    if (toGenerate.length === 0) {
      showToast('All documents are already up to date', 'success');
      setIsLoading(false);
      return;
    }
    let successCount = 0;
    try {
      for (const item of toGenerate) {
        setGeneratingDocType(item.doc_type);
        try {
          const generated = await documentationService.generate(selectedRepo.id, item.doc_type);
          setItems((prev) =>
            prev.map((i) =>
              i.id === generated.id || i.doc_type === generated.doc_type ? generated : i
            )
          );
          if (activeItem && (activeItem.id === generated.id || activeItem.doc_type === generated.doc_type)) {
            setActiveItem(generated);
          }
          successCount++;
        } catch {
          // continue with next item
        }
      }
      const [dashData, covData, gapsData] = await Promise.all([
        documentationService.getDashboard(selectedRepo.id),
        documentationService.getCoverage(selectedRepo.id),
        documentationService.getGaps(selectedRepo.id),
      ]);
      setDashboard(dashData);
      setCoverage(covData);
      setGaps(gapsData);
      showToast(`✓ Generated ${successCount} of ${toGenerate.length} documents`, 'success');
    } catch (err) {
      console.error('Batch generation failed:', err);
      showToast('Batch generation encountered errors', 'error');
    } finally {
      setIsLoading(false);
      setGeneratingDocType(null);
    }
  };

  const handleResolveGap = async (gap: DocumentationGap) => {
    if (!selectedRepo) return;
    setResolvingGapId(gap.id);
    try {
      const generatedDoc = await documentationService.resolveGap(selectedRepo.id, gap.id);

      // Add or update document in items catalog
      setItems((prevItems) => {
        const idx = prevItems.findIndex(
          (i) => i.id === generatedDoc.id || i.doc_type === generatedDoc.doc_type
        );
        if (idx >= 0) {
          const next = [...prevItems];
          next[idx] = generatedDoc;
          return next;
        } else {
          return [generatedDoc, ...prevItems];
        }
      });

      // Update gap status in local state to resolved
      setGaps((prevGaps) =>
        prevGaps.map((g) => (g.id === gap.id ? { ...g, status: 'resolved' } : g))
      );

      // Refresh metrics in background
      documentationService.getDashboard(selectedRepo.id).then(setDashboard).catch(() => {});
      documentationService.getCoverage(selectedRepo.id).then(setCoverage).catch(() => {});

      showToast(`Resolved gap & generated "${generatedDoc.title}"`, 'success');
    } catch (err) {
      console.error('Failed to resolve gap:', err);
      showToast('Failed to resolve gap and generate document', 'error');
    } finally {
      setResolvingGapId(null);
    }
  };

  const filteredItems = items.filter((item) => {
    if (activeCategory === 'project') return item.category === 'project';
    if (activeCategory === 'technical') return item.category === 'technical';
    if (activeCategory === 'outdated') return item.status === 'outdated' || item.status === 'update_recommended';
    if (activeCategory === 'ai_generated') return item.is_ai_generated === true;
    return true;
  });

  const outdatedItems = items.filter((i) => i.status === 'outdated');

  if (!selectedRepo) {
    return (
      <div className="p-12 text-center text-slate-400">
        Please select or connect a repository first to access Documentation Intelligence.
      </div>
    );
  }

  return (
    <div className="p-8 space-y-7 max-w-7xl mx-auto">
      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed top-6 right-6 z-[100] flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl border text-sm font-medium transition-all duration-300 ${
            toast.type === 'success'
              ? 'bg-emerald-950 border-emerald-700 text-emerald-300'
              : 'bg-rose-950 border-rose-700 text-rose-300'
          }`}
        >
          <span>{toast.type === 'success' ? '✓' : '✗'}</span>
          <span>{toast.message}</span>
        </div>
      )}
      {/* Top Hero Banner & Executive Metrics */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/50 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800/80">
                <BookOpen className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-bold text-slate-100">
                Documentation Intelligence ({selectedRepo.name})
              </h1>
              <Badge variant="cyan" size="sm">
                Branch: {selectedRepo.default_branch || 'main'}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 max-w-2xl">
              Autonomous repository-aware technical documentation engine. Analyzes source code, AST entities, APIs, configurations, and change impact to generate verified specifications.
            </p>
          </div>

          {/* Quick Action Controls */}
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSyncChangeImpact}
              isLoading={isSyncingImpact}
              leftIcon={<RotateCcw className="w-3.5 h-3.5 text-amber-400" />}
              className="text-xs"
            >
              Sync Change Impact
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleGenerateAll}
              isLoading={isLoading}
              leftIcon={<Sparkles className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              Generate All Specs
            </Button>
          </div>
        </div>

        {/* 4 Key Executive Metric Tiles */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-slate-800/70">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              Estimated Coverage
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-cyan-400">
                {dashboard?.coverage_score ?? 0}%
              </span>
              <span className="text-[11px] text-slate-400">Grounded</span>
            </div>
            {/* Progress bar */}
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-cyan-500 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${dashboard?.coverage_score ?? 0}%` }}
              ></div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              Files & Modules Analyzed
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-100">
                {dashboard?.files_analyzed ?? selectedRepo.total_files}
              </span>
              <span className="text-[11px] text-slate-400">
                ({dashboard?.modules_count ?? 1} modules)
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              AST entities mapped
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              Specifications Status
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-400">
                {dashboard?.up_to_date_count ?? 0}
              </span>
              <span className="text-[11px] text-slate-400">
                / {dashboard?.total_documents ?? 13} Up to date
              </span>
            </div>
            <div className="text-[11px] text-amber-400 font-medium">
              {dashboard?.outdated_count ?? 0} require update
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              Last Code Analysis
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-base font-semibold text-slate-200">
                {dashboard?.last_analyzed || '5 minutes ago'}
              </span>
            </div>
            <div className="text-[11px] text-slate-400">
              Branch `{selectedRepo.default_branch || 'main'}`
            </div>
          </div>
        </div>

        {/* Global Documentation Search Bar */}
        <form onSubmit={handleSearch} className="flex gap-2 pt-1">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search across all technical specifications (e.g., 'How does authentication work?', 'API contracts')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <Button
            type="submit"
            variant="secondary"
            size="sm"
            isLoading={isSearching}
            className="text-xs px-4"
          >
            Search Docs
          </Button>
          {searchResults.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchResults([]);
                setSearchQuery('');
              }}
              className="text-xs"
            >
              Clear
            </Button>
          )}
        </form>

        {/* Search Results Drawer if active */}
        {searchResults.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-950 border border-cyan-800/60 space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-cyan-300">
              <span>Found {searchResults.length} relevant sections matching "{searchQuery}"</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {searchResults.map((match) => {
                const matchedItem = items.find((i) => i.id === match.document_id);
                return (
                  <div
                    key={match.document_id}
                    onClick={() => matchedItem && handleOpenEditor(matchedItem)}
                    className="p-3 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-700 cursor-pointer transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-100">
                      <span>{match.title}</span>
                      <Badge variant="cyan" size="sm">
                        SCORE: {match.score}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 font-mono">
                      {match.snippet}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Change Impact Warning Banner (Section 11) */}
      {outdatedItems.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-900/60 text-amber-300 border border-amber-700/60">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-amber-200">
                Documentation Update Required: {outdatedItems.length} documents may be outdated
              </h3>
              <p className="text-xs text-amber-300/80">
                Code modifications were detected in components affecting{' '}
                {outdatedItems.map((i) => i.title).join(', ')}.
              </p>
            </div>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={handleGenerateAll}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            className="text-xs bg-amber-600 hover:bg-amber-500 text-white"
          >
            Regenerate Outdated Docs
          </Button>
        </div>
      )}

      {/* Autonomous Documentation Gap Detection (Section 13) */}
      <DocGapsPanel
        gaps={gaps}
        onGenerateDocForGap={handleResolveGap}
        onRefreshGaps={async () => {
          if (!selectedRepo) return;
          const freshGaps = await documentationService.scanGaps(selectedRepo.id);
          setGaps(freshGaps);
        }}
        isLoading={isLoading}
        resolvingGapId={resolvingGapId}
      />

      {/* Documentation Catalog & Cards Grid (Section 4) */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              Technical Documentation Catalog
              <span className="text-xs font-normal text-slate-400">
                ({items.length} Grounded Specifications)
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Select any document to review, regenerate, validate against AST symbols, or edit with AI.
            </p>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-900/80 border border-slate-800 rounded-xl text-xs flex-wrap">
            <button
              onClick={() => setActiveCategory('all')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                activeCategory === 'all'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ({items.length})
            </button>
            <button
              onClick={() => setActiveCategory('project')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                activeCategory === 'project'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Project ({items.filter((i) => i.category === 'project').length})
            </button>
            <button
              onClick={() => setActiveCategory('technical')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                activeCategory === 'technical'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Technical ({items.filter((i) => i.category === 'technical').length})
            </button>
            <button
              onClick={() => setActiveCategory('outdated')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                activeCategory === 'outdated'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Needs Update ({items.filter((i) => i.status !== 'up_to_date' && i.status !== 'not_generated').length})
            </button>
            <button
              onClick={() => setActiveCategory('ai_generated')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
                activeCategory === 'ai_generated'
                  ? 'bg-purple-950 text-purple-300 border border-purple-700/80 shadow-sm'
                  : 'text-slate-400 hover:text-purple-300'
              }`}
            >
              <Sparkles className="w-3 h-3 text-purple-400" />
              AI Generated ({items.filter((i) => i.is_ai_generated).length})
            </button>
          </div>
        </div>

        {/* Documentation Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredItems.map((item) => (
            <DocCard
              key={item.id}
              item={item}
              onView={handleOpenEditor}
              onGenerate={handleGenerate}
              isLoading={generatingDocType === item.doc_type}
            />
          ))}
        </div>
      </div>

      {/* Bottom Section: Documentation Coverage Breakdown & Activity Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-4">
        {/* Coverage Breakdown */}
        <div className="lg:col-span-6 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              Repository Coverage Assessment
            </h3>
            <span className="text-xs font-bold text-cyan-400">
              {coverage?.coverage_percentage ?? 0}% Metric
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Documented Modules ({coverage?.documented_modules.length || 0}/{coverage?.total_modules || 0})</span>
                <span className="text-slate-200">
                  {Math.round(
                    ((coverage?.documented_modules.length || 0) / (coverage?.total_modules || 1)) * 100
                  )}%
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div
                  className="bg-emerald-500 h-1.5 rounded-full"
                  style={{
                    width: `${Math.round(
                      ((coverage?.documented_modules.length || 0) / (coverage?.total_modules || 1)) * 100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Documented API Endpoints ({coverage?.documented_endpoints.length || 0}/{coverage?.total_endpoints || 0})</span>
                <span className="text-slate-200">
                  {Math.round(
                    ((coverage?.documented_endpoints.length || 0) / (coverage?.total_endpoints || 1)) * 100
                  )}%
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div
                  className="bg-indigo-500 h-1.5 rounded-full"
                  style={{
                    width: `${Math.round(
                      ((coverage?.documented_endpoints.length || 0) / (coverage?.total_endpoints || 1)) * 100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>

            {coverage?.undocumented_modules && coverage.undocumented_modules.length > 0 && (
              <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                <span className="font-semibold text-amber-400 block mb-1">Undocumented Modules:</span>
                <div className="flex flex-wrap gap-1">
                  {coverage.undocumented_modules.map((m) => (
                    <span key={m} className="px-2 py-0.5 rounded bg-slate-950 font-mono text-slate-300 border border-slate-800">
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Activity Stream */}
        <div className="lg:col-span-6 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            Recent Documentation Activity
          </h3>

          <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1 text-xs">
            {dashboard?.recent_activity && dashboard.recent_activity.length > 0 ? (
              dashboard.recent_activity.map((act) => (
                <div
                  key={act.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/70 border border-slate-800"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                    <span className="font-semibold text-slate-200">{act.action}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <Badge variant={act.validation_status === 'passed' ? 'success' : 'warning'} size="sm">
                      {act.validation_status.toUpperCase()}
                    </Badge>
                    <span>{new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-slate-500 italic">
                No recent documentation events recorded.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Editor & Inspection Modal */}
      {activeItem && (
        <DocEditorModal
          isOpen={isEditorOpen}
          onClose={() => setIsEditorOpen(false)}
          item={activeItem}
          repositoryId={selectedRepo.id}
          onSaved={handleItemSaved}
          onRegenerate={handleGenerate}
        />
      )}
    </div>
  );
};
