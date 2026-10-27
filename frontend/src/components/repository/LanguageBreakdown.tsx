import React from 'react';
import { Code, PieChart } from 'lucide-react';

interface LanguageBreakdownProps {
  languages: Record<string, number>;
  languagePercentages?: Record<string, number>;
  onSelectLanguage?: (language: string) => void;
  selectedLanguage?: string | null;
}

const LANGUAGE_COLORS: Record<string, string> = {
  JavaScript: 'bg-amber-400',
  'JavaScript (React)': 'bg-amber-400',
  TypeScript: 'bg-blue-400',
  'TypeScript (React)': 'bg-blue-500',
  Python: 'bg-emerald-400',
  HTML: 'bg-orange-500',
  CSS: 'bg-sky-400',
  SCSS: 'bg-pink-400',
  Go: 'bg-cyan-400',
  Rust: 'bg-amber-600',
  Java: 'bg-red-500',
  'C#': 'bg-purple-500',
  'C++': 'bg-pink-600',
  C: 'bg-slate-400',
  PHP: 'bg-indigo-400',
  Ruby: 'bg-rose-500',
  SQL: 'bg-teal-400',
  Dockerfile: 'bg-cyan-600',
  YAML: 'bg-violet-400',
  JSON: 'bg-slate-500',
  Markdown: 'bg-slate-400',
  Shell: 'bg-lime-400',
};

const DEFAULT_COLOR = 'bg-slate-400';

export const LanguageBreakdown: React.FC<LanguageBreakdownProps> = ({
  languages = {},
  languagePercentages,
  onSelectLanguage,
  selectedLanguage,
}) => {
  const totalLines = Object.values(languages).reduce((sum, val) => sum + val, 0);

  // Compute percentages if not passed
  const entries = Object.entries(languages)
    .sort((a, b) => b[1] - a[1])
    .map(([lang, lines]) => {
      const pct =
        languagePercentages && languagePercentages[lang] !== undefined
          ? languagePercentages[lang]
          : totalLines > 0
          ? Math.round((lines / totalLines) * 1000) / 10
          : 0;
      return {
        name: lang,
        lines,
        percentage: pct,
        color: LANGUAGE_COLORS[lang] || DEFAULT_COLOR,
      };
    });

  if (entries.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 text-xs">
        No language data available.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="h-2 w-full flex rounded-full overflow-hidden bg-slate-800 gap-0.5">
          {entries.map((item) => (
            <div
              key={item.name}
              style={{ width: `${Math.max(item.percentage, 2)}%` }}
              className={`${item.color} transition-all duration-300 hover:opacity-80`}
              title={`${item.name}: ${item.percentage}% (${item.lines.toLocaleString()} lines)`}
            />
          ))}
        </div>
        <div className="flex justify-between text-[11px] text-slate-400 font-mono">
          <span>{entries.length} Detected Languages</span>
          <span>{totalLines.toLocaleString()} Total Lines</span>
        </div>
      </div>

      {/* Language List */}
      <div className="grid grid-cols-1 gap-1.5">
        {entries.map((item) => {
          const isSelected = selectedLanguage === item.name;
          return (
            <div
              key={item.name}
              onClick={() => onSelectLanguage && onSelectLanguage(item.name)}
              className={`flex items-center justify-between p-2 rounded-lg border transition-all ${
                onSelectLanguage ? 'cursor-pointer' : ''
              } ${
                isSelected
                  ? 'bg-cyan-950/40 border-cyan-500/50 shadow-sm'
                  : 'bg-slate-900/40 border-slate-800/80 hover:bg-slate-850 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${item.color}`} />
                <span className="text-xs font-semibold text-slate-200 truncate">
                  {item.name}
                </span>
              </div>
              <div className="flex items-center gap-3 text-right flex-shrink-0">
                <span className="text-[11px] text-slate-400 font-mono">
                  {item.lines.toLocaleString()} lines
                </span>
                <span className="text-xs font-bold text-slate-100 font-mono min-w-[3rem] text-right">
                  {item.percentage}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
