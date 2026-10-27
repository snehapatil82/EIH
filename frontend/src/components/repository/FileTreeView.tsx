import React, { useState, useMemo } from 'react';
import {
  Folder,
  FolderOpen,
  FileCode,
  FileText,
  File,
  ChevronRight,
  ChevronDown,
  Search,
  Maximize2,
  Minimize2,
  Sparkles,
  Package,
} from 'lucide-react';
import { FileTreeItem } from '../../types/repository';

interface FileTreeViewProps {
  items: FileTreeItem[];
  selectedFilePath: string | null;
  onSelectFile: (path: string) => void;
}

interface TreeNodeProps {
  item: FileTreeItem;
  selectedFilePath: string | null;
  onSelectFile: (path: string) => void;
  level: number;
  forceOpen?: boolean;
}

const getFileIcon = (filename: string, language?: string) => {
  const lower = filename.toLowerCase();
  if (lower.endsWith('.json') || lower === 'package.json') {
    return <Package className="w-4 h-4 text-emerald-400" />;
  }
  if (language === 'Python' || lower.endsWith('.py')) {
    return <FileCode className="w-4 h-4 text-amber-400" />;
  }
  if (language?.includes('TypeScript') || lower.endsWith('.ts') || lower.endsWith('.tsx')) {
    return <FileCode className="w-4 h-4 text-blue-400" />;
  }
  if (language?.includes('JavaScript') || lower.endsWith('.js') || lower.endsWith('.jsx')) {
    return <FileCode className="w-4 h-4 text-yellow-400" />;
  }
  if (lower.endsWith('.md') || lower.endsWith('.txt')) {
    return <FileText className="w-4 h-4 text-emerald-400" />;
  }
  if (lower.endsWith('.css') || lower.endsWith('.scss')) {
    return <FileCode className="w-4 h-4 text-pink-400" />;
  }
  if (lower.endsWith('.html')) {
    return <FileCode className="w-4 h-4 text-orange-400" />;
  }
  return <File className="w-4 h-4 text-slate-400" />;
};

const TreeNode: React.FC<TreeNodeProps> = ({
  item,
  selectedFilePath,
  onSelectFile,
  level,
  forceOpen,
}) => {
  const [isOpen, setIsOpen] = useState(level === 0 || level === 1);
  const isDirectory = item.type === 'directory';
  const isSelected = selectedFilePath === item.path;

  const effectivelyOpen = forceOpen !== undefined ? forceOpen : isOpen;

  const handleClick = () => {
    if (isDirectory) {
      setIsOpen(!effectivelyOpen);
    } else {
      onSelectFile(item.path);
    }
  };

  return (
    <div>
      <div
        className={`flex items-center gap-1.5 py-1 px-2 rounded-md cursor-pointer text-xs transition-colors select-none group ${
          isSelected
            ? 'bg-cyan-950/80 text-cyan-300 font-semibold border border-cyan-800/60 shadow-sm'
            : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100'
        }`}
        style={{ paddingLeft: `${level * 14 + 6}px` }}
        onClick={handleClick}
      >
        {isDirectory ? (
          <>
            {effectivelyOpen ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
            )}
            {effectivelyOpen ? (
              <FolderOpen className="w-4 h-4 text-amber-400 flex-shrink-0" />
            ) : (
              <Folder className="w-4 h-4 text-amber-400 flex-shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5 flex-shrink-0" />
            {getFileIcon(item.name, item.language)}
          </>
        )}

        <span className="truncate flex-1">{item.name}</span>

        {item.language && !isDirectory && (
          <span className="text-[10px] text-slate-500 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
            {item.language}
          </span>
        )}
      </div>

      {isDirectory && effectivelyOpen && item.children && (
        <div>
          {item.children.map((child) => (
            <TreeNode
              key={child.path}
              item={child}
              selectedFilePath={selectedFilePath}
              onSelectFile={onSelectFile}
              level={level + 1}
              forceOpen={forceOpen}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const FileTreeView: React.FC<FileTreeViewProps> = ({
  items,
  selectedFilePath,
  onSelectFile,
}) => {
  const [search, setSearch] = useState('');
  const [forceExpand, setForceExpand] = useState<boolean | undefined>(undefined);

  // Flatten & filter files if searching
  const flattenFiles = (nodes: FileTreeItem[]): FileTreeItem[] => {
    let result: FileTreeItem[] = [];
    for (const node of nodes) {
      if (node.type === 'file') {
        result.push(node);
      }
      if (node.children) {
        result = result.concat(flattenFiles(node.children));
      }
    }
    return result;
  };

  const allFiles = useMemo(() => flattenFiles(items), [items]);

  const filteredFlatFiles = useMemo(() => {
    if (!search.trim()) return null;
    const q = search.toLowerCase();
    return allFiles.filter(
      (f) => f.name.toLowerCase().includes(q) || f.path.toLowerCase().includes(q)
    );
  }, [allFiles, search]);

  if (items.length === 0) {
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        No files discovered in repository.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-2">
      {/* Search and Expand/Collapse Controls */}
      <div className="space-y-1.5 pb-2 border-b border-slate-800">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search files..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-7 pr-2 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span>{allFiles.length} files</span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setForceExpand(true)}
              title="Expand all folders"
              className="p-1 hover:text-cyan-400 transition-colors"
            >
              <Maximize2 className="w-3 h-3" />
            </button>
            <button
              onClick={() => setForceExpand(false)}
              title="Collapse all folders"
              className="p-1 hover:text-cyan-400 transition-colors"
            >
              <Minimize2 className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Tree / Search Results */}
      <div className="flex-1 overflow-y-auto space-y-0.5 font-mono pr-1">
        {filteredFlatFiles !== null ? (
          filteredFlatFiles.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              No matching files found.
            </div>
          ) : (
            filteredFlatFiles.map((file) => (
              <div
                key={file.path}
                onClick={() => onSelectFile(file.path)}
                className={`flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer text-xs transition-colors ${
                  selectedFilePath === file.path
                    ? 'bg-cyan-950/80 text-cyan-300 font-semibold border border-cyan-800/60'
                    : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100'
                }`}
              >
                {getFileIcon(file.name, file.language)}
                <div className="truncate">
                  <span className="text-slate-100">{file.name}</span>
                  <span className="text-[10px] text-slate-500 block truncate">{file.path}</span>
                </div>
              </div>
            ))
          )
        ) : (
          items.map((item) => (
            <TreeNode
              key={item.path}
              item={item}
              selectedFilePath={selectedFilePath}
              onSelectFile={onSelectFile}
              level={0}
              forceOpen={forceExpand}
            />
          ))
        )}
      </div>
    </div>
  );
};
