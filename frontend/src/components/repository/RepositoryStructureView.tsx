import React, { useState } from 'react';
import {
  FolderTree,
  Folder,
  FolderOpen,
  FileCode,
  Layers,
  ChevronRight,
  ChevronDown,
  Search,
  Code2,
  HardDrive,
  BarChart2,
} from 'lucide-react';
import { DirectorySummary, FileTreeItem } from '../../types/repository';
import { Badge } from '../common/Badge';

interface RepositoryStructureViewProps {
  rootDirectories: DirectorySummary[];
  treeItems?: FileTreeItem[];
  totalFiles?: number;
  totalLines?: number;
  onSelectFile?: (filePath: string) => void;
  onSelectDirectory?: (dirPath: string) => void;
}

export const RepositoryStructureView: React.FC<RepositoryStructureViewProps> = ({
  rootDirectories = [],
  treeItems = [],
  totalFiles = 0,
  totalLines = 0,
  onSelectFile,
}) => {
  const [search, setSearch] = useState('');
  const [selectedDir, setSelectedDir] = useState<string | null>(null);

  // Compute folder statistics
  const filteredDirs = rootDirectories.filter((d) =>
    d.name.toLowerCase().includes(search.toLowerCase()) ||
    d.languages.some((l) => l.toLowerCase().includes(search.toLowerCase()))
  );

  // Find files in selected directory from treeItems
  const getFilesInDir = (dirName: string, items: FileTreeItem[]): FileTreeItem[] => {
    let result: FileTreeItem[] = [];
    for (const item of items) {
      if (item.path.startsWith(dirName + '/') || item.path === dirName) {
        if (item.type === 'file') {
          result.push(item);
        }
        if (item.children) {
          result = result.concat(getFilesInDir(dirName, item.children));
        }
      } else if (item.children) {
        result = result.concat(getFilesInDir(dirName, item.children));
      }
    }
    return result;
  };

  const activeDirFiles = selectedDir ? getFilesInDir(selectedDir, treeItems) : [];

  return (
    <div className="space-y-4">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <FolderTree className="w-4 h-4 text-amber-400" />
            Repository Structure & Directory Topology
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Module distribution across {rootDirectories.length} root packages ({totalFiles} files, {totalLines.toLocaleString()} LOC)
          </p>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter modules / folders..."
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Directory Topology Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filteredDirs.map((dir) => {
          const isSelected = selectedDir === dir.name;
          const pctFiles = totalFiles > 0 ? Math.round((dir.file_count / totalFiles) * 100) : 0;
          const pctLines = totalLines > 0 ? Math.round((dir.line_count / totalLines) * 100) : 0;

          return (
            <div
              key={dir.path}
              onClick={() => setSelectedDir(isSelected ? null : dir.name)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer group flex flex-col justify-between space-y-3 ${
                isSelected
                  ? 'bg-amber-950/30 border-amber-500/50 shadow-md ring-1 ring-amber-500/30'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-850/80'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-amber-900/50 text-amber-300' : 'bg-slate-950 text-amber-400 group-hover:text-amber-300'} border border-slate-800`}>
                    {isSelected ? <FolderOpen className="w-4 h-4" /> : <Folder className="w-4 h-4" />}
                  </div>
                  <div className="min-w-0">
                    <span className="text-xs font-mono font-bold text-slate-100 group-hover:text-amber-300 truncate block">
                      {dir.name}/
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {dir.file_count} files ({pctFiles}% of repo)
                    </span>
                  </div>
                </div>

                <ChevronRight className={`w-3.5 h-3.5 text-slate-500 transition-transform ${isSelected ? 'rotate-90 text-amber-400' : 'group-hover:text-slate-300'}`} />
              </div>

              {/* Progress bar of volume */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                  <span>Volume: {dir.line_count.toLocaleString()} lines</span>
                  <span>{pctLines}% LOC</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-yellow-400 rounded-full transition-all"
                    style={{ width: `${Math.max(pctLines, 4)}%` }}
                  />
                </div>
              </div>

              {/* Languages in directory */}
              <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800/80">
                {dir.languages.map((lang) => (
                  <span
                    key={lang}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Directory Files Drilldown */}
      {selectedDir && (
        <div className="p-4 bg-slate-900/80 border border-amber-500/30 rounded-xl space-y-3 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-bold text-slate-200">
                Files inside <code className="text-amber-300 font-mono">{selectedDir}/</code> ({activeDirFiles.length})
              </h4>
            </div>
            <button
              onClick={() => setSelectedDir(null)}
              className="text-[11px] text-slate-400 hover:text-slate-200"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-60 overflow-y-auto pr-1">
            {activeDirFiles.map((file) => (
              <div
                key={file.path}
                onClick={() => onSelectFile && onSelectFile(file.path)}
                className={`p-2 bg-slate-950/80 border border-slate-800 rounded-lg flex items-center justify-between gap-2 text-xs transition-colors ${
                  onSelectFile ? 'hover:border-cyan-500/50 hover:bg-slate-900 cursor-pointer group' : ''
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <FileCode className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                  <span className="font-mono text-slate-300 group-hover:text-cyan-300 truncate text-[11px]">
                    {file.name}
                  </span>
                </div>
                {file.language && (
                  <span className="text-[10px] text-slate-500 font-mono flex-shrink-0">
                    {file.language}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
