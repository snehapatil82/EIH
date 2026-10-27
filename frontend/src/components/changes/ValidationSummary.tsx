import React from 'react';
import { CheckCircle2, XCircle, ShieldCheck, FileCheck, Terminal, AlertTriangle } from 'lucide-react';
import { ValidationResult } from '../../types/changes';

interface ValidationSummaryProps {
  validation?: ValidationResult;
}

export const ValidationSummary: React.FC<ValidationSummaryProps> = ({ validation }) => {
  if (!validation) {
    return (
      <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-xs text-slate-400">
        Validation results pending...
      </div>
    );
  }

  const checks = [
    { label: 'AST Syntax Verification', passed: validation.syntax_passed, icon: FileCheck },
    { label: 'Import Integrity', passed: validation.imports_passed, icon: Terminal },
    { label: 'Sandbox Unit Tests', passed: validation.tests_passed, icon: ShieldCheck },
    { label: 'Requirement Matching', passed: validation.requirements_passed, icon: CheckCircle2 },
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Validation & Test Report (Iteration {validation.iteration})
        </h4>
        <span
          className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
            validation.status === 'passed'
              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
              : 'bg-rose-950 text-rose-300 border border-rose-800'
          }`}
        >
          {validation.status.toUpperCase()}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {checks.map((check, idx) => {
          const Icon = check.icon;
          return (
            <div
              key={idx}
              className={`p-3 rounded-lg border flex items-center gap-2.5 ${
                check.passed
                  ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                  : 'bg-rose-950/20 border-rose-800/40 text-rose-300'
              }`}
            >
              {check.passed ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              )}
              <span className="text-xs font-medium">{check.label}</span>
            </div>
          );
        })}
      </div>

      {validation.error_summary && (
        <div className="p-3 bg-rose-950/40 border border-rose-800 rounded-lg text-xs text-rose-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <strong>Self-Correction Diagnostic:</strong>
            <p className="mt-0.5">{validation.error_summary}</p>
          </div>
        </div>
      )}

      {validation.details?.test_output && (
        <div className="mt-3">
          <span className="text-[11px] text-slate-400 font-mono">Sandbox Test Output:</span>
          <pre className="mt-1 bg-slate-950 p-3 rounded-lg text-[11px] font-mono text-slate-300 max-h-32 overflow-y-auto border border-slate-800 whitespace-pre">
            {validation.details.test_output}
          </pre>
        </div>
      )}
    </div>
  );
};
