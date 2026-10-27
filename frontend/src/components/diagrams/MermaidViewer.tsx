import React, { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';
import {
  Copy, Check, Sparkles, ZoomIn, ZoomOut, Maximize2, Minimize2,
  Download, Code2, Eye, RotateCcw, ChevronDown, ChevronUp, FileCode,
  Image as ImageIcon, FileText, Info, ShieldCheck, AlertTriangle, AlertCircle,
  Boxes, GitBranch, ArrowRight
} from 'lucide-react';

export interface DiagramMetadataProps {
  summary?: string;
  components_involved?: string[];
  key_relationships?: string[];
  source_references?: string[];
  evidence_status?: 'verified' | 'partial' | 'unverified';
  evidence_limitations?: string;
}

interface MermaidViewerProps {
  chart: string;
  title?: string;
  description?: string;
  diagramType?: string;
  meta?: DiagramMetadataProps;
  filenameBase?: string;
}

let mermaidInitialized = false;

function initMermaid() {
  if (mermaidInitialized) return;
  mermaidInitialized = true;
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter, sans-serif',
    themeVariables: {
      darkMode: true,
      background: '#090d16',
      primaryColor: '#0e7490',
      primaryTextColor: '#f1f5f9',
      primaryBorderColor: '#164e63',
      lineColor: '#38bdf8',
      secondaryColor: '#1e293b',
      tertiaryColor: '#0f172a',
      noteBkgColor: '#1e293b',
      noteTextColor: '#94a3b8',
      edgeLabelBackground: '#1e293b',
      clusterBkg: '#0f172a',
      clusterBorder: '#1e3a5f',
    },
  });
}

export const MermaidViewer: React.FC<MermaidViewerProps> = ({
  chart,
  title,
  description,
  diagramType,
  meta,
  filenameBase,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const downloadMenuRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState('');
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showCode, setShowCode] = useState(false);
  const [isDownloadMenuOpen, setIsDownloadMenuOpen] = useState(false);
  const [showDetails, setShowDetails] = useState(true);

  useEffect(() => {
    initMermaid();
    const renderChart = async () => {
      if (!chart?.trim()) return;
      try {
        setError(null);
        setScale(1);
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        setSvgContent(svg);
      } catch (err: any) {
        setError(err.message || 'Failed to render diagram.');
      }
    };
    renderChart();
  }, [chart]);

  // Click outside to close download menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (downloadMenuRef.current && !downloadMenuRef.current.contains(event.target as Node)) {
        setIsDownloadMenuOpen(false);
      }
    };
    if (isDownloadMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDownloadMenuOpen]);

  const activeFilename = filenameBase || title || 'diagram';

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [chart]);

  const handleDownloadSVG = useCallback(() => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeFilename}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [svgContent, activeFilename]);

  const handleDownloadPNG = useCallback(() => {
    if (!svgContent) return;

    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(svgContent, 'image/svg+xml');
      const svgEl = doc.querySelector('svg');
      if (!svgEl) return;

      // 1. Ensure required SVG namespaces
      if (!svgEl.getAttribute('xmlns')) {
        svgEl.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      }
      if (!svgEl.getAttribute('xmlns:xlink')) {
        svgEl.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
      }

      // 2. Compute accurate dimensions from viewBox or attributes
      let width = 1200;
      let height = 800;
      const viewBox = svgEl.getAttribute('viewBox');
      if (viewBox) {
        const parts = viewBox.split(/[\s,]+/).map(parseFloat);
        if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
          width = parts[2];
          height = parts[3];
        }
      } else {
        const w = parseFloat(svgEl.getAttribute('width') || '');
        const h = parseFloat(svgEl.getAttribute('height') || '');
        if (w && h) {
          width = w;
          height = h;
        }
      }

      // Set explicit dimension attributes on SVG
      svgEl.setAttribute('width', String(width));
      svgEl.setAttribute('height', String(height));

      // 3. Remove all @import statements from <style> blocks (prevents canvas tainting)
      const styleEls = doc.querySelectorAll('style');
      styleEls.forEach((style) => {
        let css = style.textContent || '';
        css = css.replace(/@import\s+url\([^)]+\);?/gi, '');
        css = css.replace(/@import\s+['"][^'"]+['"];?/gi, '');
        style.textContent = css;
      });

      // 4. Strip any external links/images that cause cross-origin tainting
      doc.querySelectorAll('link, image').forEach((el) => {
        const href = el.getAttribute('href') || el.getAttribute('xlink:href') || '';
        if (href.startsWith('http://') || href.startsWith('https://')) {
          el.remove();
        }
      });

      // 5. Replace <foreignObject> elements with native SVG <text> elements
      const foreignObjects = Array.from(doc.querySelectorAll('foreignObject'));
      foreignObjects.forEach((fo) => {
        const rawText = fo.textContent?.trim() || '';
        const x = parseFloat(fo.getAttribute('x') || '0');
        const y = parseFloat(fo.getAttribute('y') || '0');
        const w = parseFloat(fo.getAttribute('width') || '0');
        const h = parseFloat(fo.getAttribute('height') || '0');

        const textEl = doc.createElementNS('http://www.w3.org/2000/svg', 'text');
        textEl.setAttribute('x', String(x + w / 2));
        textEl.setAttribute('y', String(y + h / 2));
        textEl.setAttribute('text-anchor', 'middle');
        textEl.setAttribute('dominant-baseline', 'central');
        textEl.setAttribute('fill', '#f1f5f9');
        textEl.setAttribute('font-family', 'Inter, system-ui, -apple-system, sans-serif');
        textEl.setAttribute('font-size', '13px');
        textEl.setAttribute('font-weight', '500');

        const lines = rawText.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
        if (lines.length > 1) {
          const lineHeight = 16;
          const startY = (y + h / 2) - ((lines.length - 1) * lineHeight) / 2;
          lines.forEach((line, idx) => {
            const tspan = doc.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            tspan.setAttribute('x', String(x + w / 2));
            tspan.setAttribute('y', String(startY + idx * lineHeight));
            tspan.textContent = line;
            textEl.appendChild(tspan);
          });
        } else {
          textEl.textContent = rawText;
        }

        fo.parentNode?.replaceChild(textEl, fo);
      });

      const serializer = new XMLSerializer();
      const sanitizedSvg = serializer.serializeToString(doc);

      const svgBlob = new Blob([sanitizedSvg], { type: 'image/svg+xml;charset=utf-8' });
      const blobUrl = URL.createObjectURL(svgBlob);
      const img = new Image();
      img.crossOrigin = 'anonymous';

      img.onload = () => {
        try {
          const scaleFactor = 2; // High-resolution 2x rendering
          const canvas = document.createElement('canvas');
          canvas.width = Math.round(width * scaleFactor);
          canvas.height = Math.round(height * scaleFactor);
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            URL.revokeObjectURL(blobUrl);
            return;
          }

          // Dark theme background matching dark viewer
          ctx.fillStyle = '#090d16';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

          canvas.toBlob((blob) => {
            if (blob) {
              const pngUrl = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = pngUrl;
              a.download = `${activeFilename}.png`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              setTimeout(() => URL.revokeObjectURL(pngUrl), 1000);
            }
            URL.revokeObjectURL(blobUrl);
          }, 'image/png');
        } catch (canvasErr) {
          console.error('Failed to export canvas to PNG:', canvasErr);
          URL.revokeObjectURL(blobUrl);
        }
      };

      img.onerror = (err) => {
        console.error('Failed to load sanitized SVG image for PNG export:', err);
        URL.revokeObjectURL(blobUrl);
      };

      img.src = blobUrl;
    } catch (err) {
      console.error('Error preparing PNG export:', err);
    }
  }, [svgContent, activeFilename]);

  const handleDownloadMermaid = useCallback(() => {
    if (!chart) return;
    const blob = new Blob([chart], { type: 'text/vnd.mermaid;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeFilename}.mmd`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [chart, activeFilename]);

  const zoom = (delta: number) => setScale((s) => Math.max(0.3, Math.min(3, s + delta)));
  const resetZoom = () => setScale(1);

  const wrapperClass = isFullscreen
    ? 'fixed inset-0 z-50 bg-slate-950 flex flex-col'
    : 'bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col';

  return (
    <div className={wrapperClass}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
          {title && (
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider truncate">{title}</h4>
          )}
        </div>

        <div className="flex items-center gap-1.5 flex-shrink-0">
          {/* Zoom controls */}
          <div className="flex items-center gap-1 bg-slate-800/60 rounded-lg px-1.5 py-1 border border-slate-700">
            <button
              onClick={() => zoom(-0.2)}
              title="Zoom out"
              className="text-slate-400 hover:text-white p-0.5 rounded transition-colors"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={resetZoom}
              title="Reset zoom"
              className="text-xs text-slate-400 hover:text-white w-9 text-center font-mono transition-colors"
            >
              {Math.round(scale * 100)}%
            </button>
            <button
              onClick={() => zoom(0.2)}
              title="Zoom in"
              className="text-slate-400 hover:text-white p-0.5 rounded transition-colors"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Reset */}
          <button
            onClick={resetZoom}
            title="Reset view"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Toggle code */}
          <button
            onClick={() => setShowCode((v) => !v)}
            title={showCode ? 'View diagram' : 'View source code'}
            className={`p-1.5 rounded-lg transition-colors ${showCode ? 'bg-cyan-900/60 text-cyan-300 border border-cyan-800' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
          >
            {showCode ? <Eye className="w-3.5 h-3.5" /> : <Code2 className="w-3.5 h-3.5" />}
          </button>

          {/* Download Dropdown Menu */}
          {svgContent && !error && (
            <div className="relative" ref={downloadMenuRef}>
              <button
                id="diagram-download-btn"
                onClick={() => setIsDownloadMenuOpen((v) => !v)}
                title="Download options"
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-750 border border-slate-700 transition-colors"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span>Download</span>
                <ChevronDown className="w-3 h-3 text-slate-400" />
              </button>

              {isDownloadMenuOpen && (
                <div
                  id="diagram-download-menu"
                  className="absolute right-0 top-full mt-1.5 w-60 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-1 z-50 text-left backdrop-blur-md animate-in fade-in zoom-in-95"
                >
                  <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-800">
                    Export Diagram
                  </div>

                  <button
                    id="download-option-svg"
                    onClick={() => {
                      handleDownloadSVG();
                      setIsDownloadMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors group"
                  >
                    <FileCode className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-slate-200">Download SVG</div>
                      <div className="text-[10px] text-slate-500 truncate font-mono">{activeFilename}.svg</div>
                    </div>
                  </button>

                  <button
                    id="download-option-png"
                    onClick={() => {
                      handleDownloadPNG();
                      setIsDownloadMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors group"
                  >
                    <ImageIcon className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-slate-200">Download PNG</div>
                      <div className="text-[10px] text-slate-500 truncate font-mono">{activeFilename}.png</div>
                    </div>
                  </button>

                  <button
                    id="download-option-mmd"
                    onClick={() => {
                      handleDownloadMermaid();
                      setIsDownloadMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors group"
                  >
                    <FileText className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-slate-200">Download Mermaid Source (.mmd)</div>
                      <div className="text-[10px] text-slate-500 truncate font-mono">{activeFilename}.mmd</div>
                    </div>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Copy Mermaid */}
          <button
            onClick={handleCopy}
            title="Copy Mermaid source"
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded-lg transition-colors border border-slate-700"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>

          {/* Fullscreen */}
          <button
            onClick={() => setIsFullscreen((v) => !v)}
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto bg-slate-950/80 relative min-h-[280px]">
        {showCode ? (
          <pre className="p-5 text-xs font-mono text-cyan-300 whitespace-pre-wrap leading-relaxed">{chart}</pre>
        ) : error ? (
          <div className="p-6 text-center space-y-3">
            <p className="text-xs text-rose-400 font-semibold">⚠ Render error: {error}</p>
            <pre className="text-[11px] font-mono text-slate-400 bg-slate-900 p-3 rounded text-left overflow-x-auto max-h-48">
              {chart}
            </pre>
          </div>
        ) : svgContent ? (
          <div
            ref={containerRef}
            className="w-full flex justify-center items-start p-6 transition-transform duration-200 origin-top"
            style={{ transform: `scale(${scale})`, transformOrigin: 'center top' }}
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        ) : (
          <div className="flex items-center justify-center h-full p-10">
            <div className="flex flex-col items-center gap-3 text-slate-500">
              <div className="w-8 h-8 border-2 border-cyan-600/40 border-t-cyan-400 rounded-full animate-spin" />
              <span className="text-xs">Rendering diagram…</span>
            </div>
          </div>
        )}
      </div>

      {/* Repository-Specific Diagram Description Footer */}
      {(description || meta?.summary) && (
        <div className="border-t border-slate-800 bg-slate-900/90 backdrop-blur-md px-5 py-3.5 flex-shrink-0 space-y-3">
          {/* Header Row: Title/Type + Evidence Status Badge + Toggle */}
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-5 h-5 rounded-md bg-cyan-950/80 border border-cyan-800 flex items-center justify-center flex-shrink-0">
                <Info className="w-3 h-3 text-cyan-400" />
              </div>
              <span className="text-xs font-bold text-slate-200 tracking-wide uppercase">
                {diagramType ? `${diagramType} Description` : 'Diagram Description'}
              </span>
              {meta?.evidence_status && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium border flex items-center gap-1 ${
                    meta.evidence_status === 'verified'
                      ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                      : meta.evidence_status === 'partial'
                      ? 'bg-amber-950/80 text-amber-300 border-amber-800'
                      : 'bg-rose-950/80 text-rose-300 border-rose-800'
                  }`}
                >
                  {meta.evidence_status === 'verified' && <ShieldCheck className="w-3 h-3 text-emerald-400" />}
                  {meta.evidence_status === 'partial' && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                  {meta.evidence_status === 'unverified' && <AlertCircle className="w-3 h-3 text-rose-400" />}
                  <span>
                    {meta.evidence_status === 'verified'
                      ? 'Verified AST Evidence'
                      : meta.evidence_status === 'partial'
                      ? 'Partially Verified'
                      : 'Unverified / Missing Source Evidence'}
                  </span>
                </span>
              )}
            </div>

            {(meta?.components_involved?.length || meta?.key_relationships?.length || meta?.source_references?.length) ? (
              <button
                onClick={() => setShowDetails((v) => !v)}
                className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-cyan-300 px-2 py-1 rounded-md hover:bg-slate-800/60 transition-colors"
              >
                <span>{showDetails ? 'Hide Details' : 'View Components & Relationships'}</span>
                {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            ) : null}
          </div>

          {/* Unverified / Missing Evidence Notice */}
          {meta?.evidence_status === 'unverified' && (
            <div className="flex items-start gap-2 p-2.5 rounded-lg bg-rose-950/30 border border-rose-800/60 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Evidence Warning</p>
                <p className="text-[11px] text-rose-300/90 mt-0.5 leading-relaxed">
                  {meta.evidence_limitations || 'A project-specific description could not be generated because the relevant implementation could not be verified.'}
                </p>
              </div>
            </div>
          )}

          {/* Concise Summary Paragraph */}
          <div className="text-xs text-slate-300 leading-relaxed font-normal">
            {meta?.summary || description}
          </div>

          {/* Expanded Details: Components Involved, Key Relationships & Workflow, Source References */}
          {showDetails && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1 border-t border-slate-800/80">
              {/* Components Involved */}
              {meta?.components_involved && meta.components_involved.length > 0 && (
                <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-2.5 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400">
                    <Boxes className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Components & Files Involved</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {meta.components_involved.map((comp, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700/80 text-cyan-200"
                      >
                        {comp}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Main Relationships & Workflow */}
              {meta?.key_relationships && meta.key_relationships.length > 0 && (
                <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-2.5 space-y-1.5 md:col-span-1 lg:col-span-2">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400">
                    <GitBranch className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Key Relationships & Flow</span>
                  </div>
                  <ul className="space-y-1">
                    {meta.key_relationships.map((rel, idx) => (
                      <li key={idx} className="flex items-start gap-1.5 text-[11px] text-slate-300">
                        <ArrowRight className="w-3 h-3 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span className="leading-snug">{rel}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Source References */}
              {meta?.source_references && meta.source_references.length > 0 && (
                <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-2.5 space-y-1.5 md:col-span-2 lg:col-span-3">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400">
                    <FileCode className="w-3.5 h-3.5 text-amber-400" />
                    <span>Source File References</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {meta.source_references.map((src, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-amber-900/50 text-amber-300"
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
