import React from 'react';
import { CodeEntity } from '../../types/repository';
import { Badge } from '../common/Badge';

interface SymbolInspectorProps {
  entities: CodeEntity[];
  onSelectSymbol?: (entity: CodeEntity) => void;
}

export const SymbolInspector: React.FC<SymbolInspectorProps> = ({
  entities,
  onSelectSymbol,
}) => {
  if (entities.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-slate-400">
        No AST entities detected for this selection.
      </div>
    );
  }

  const getEntityBadge = (type: string) => {
    switch (type) {
      case 'function':
        return <Badge variant="cyan">Function</Badge>;
      case 'class':
        return <Badge variant="purple">Class</Badge>;
      case 'method':
        return <Badge variant="info">Method</Badge>;
      case 'endpoint':
        return <Badge variant="success">API Endpoint</Badge>;
      default:
        return <Badge variant="default">{type}</Badge>;
    }
  };

  return (
    <div className="space-y-2 overflow-y-auto max-h-[calc(100vh-16rem)] pr-1 font-mono text-xs">
      {entities.map((entity) => (
        <div
          key={entity.id}
          className="p-3 bg-slate-900/60 hover:bg-slate-900 border border-slate-800 rounded-lg cursor-pointer transition-all hover:border-slate-700"
          onClick={() => onSelectSymbol && onSelectSymbol(entity)}
        >
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <span className="font-semibold text-slate-200 truncate">{entity.name}</span>
            {getEntityBadge(entity.entity_type)}
          </div>

          <div className="text-[11px] text-slate-400 mb-1">
            <span>{entity.file_path}</span>
            <span className="ml-2 text-cyan-400 font-medium">L{entity.start_line}-{entity.end_line}</span>
          </div>

          {entity.signature && (
            <div className="bg-slate-950 p-1.5 rounded text-[11px] text-cyan-300 font-mono truncate">
              {entity.signature}
            </div>
          )}

          {entity.decorators.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {entity.decorators.map((dec, i) => (
                <span key={i} className="text-[10px] text-amber-300 bg-amber-950/40 px-1.5 py-0.5 rounded">
                  @{dec}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
