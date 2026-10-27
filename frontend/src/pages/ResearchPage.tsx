import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Zap,
  Award,
  Layers,
  Scale,
  Sparkles,
} from 'lucide-react';
import { BenchmarkData } from '../types/changes';
import { researchService } from '../services/researchService';
import { Spinner } from '../components/common/Spinner';

export const ResearchPage: React.FC = () => {
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadBenchmarks = async () => {
      setIsLoading(true);
      try {
        const res = await researchService.getBenchmarks();
        setData(res);
      } catch (err) {
        console.error('Failed to load benchmarks:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadBenchmarks();
  }, []);

  if (isLoading || !data) {
    return (
      <div className="p-20 flex justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-cyan-400" />
          <h2 className="text-xl font-bold text-slate-100">
            Research Evaluation: Single-Agent vs Multi-Agent Orchestration
          </h2>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Comparative empirical evaluation across latency, self-correction iteration count, test passing rate, and code quality.
        </p>
      </div>

      {/* Metric Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Single Agent Card */}
        <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl shadow-xl space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-slate-100">Single-Agent Workflow</h3>
              <p className="text-xs text-slate-400">Direct prompt-to-code generation</p>
            </div>
            <span className="px-2.5 py-1 text-xs font-mono font-bold bg-slate-800 text-slate-300 rounded-md">
              Fast / Lightweight
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Avg Latency</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-100">
                {data.single_agent_metrics.avg_latency_seconds}s
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Validation Pass Rate</span>
              </div>
              <div className="text-xl font-bold font-mono text-emerald-400">
                {data.single_agent_metrics.validation_pass_rate}%
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-blue-400" />
                <span>Quality Score</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-100">
                {data.single_agent_metrics.avg_quality_score}/100
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                <span>Security Score</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-100">
                {data.single_agent_metrics.avg_security_score}/100
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-850">
            <strong>Optimal For:</strong> {data.single_agent_metrics.suitability}
          </p>
        </div>

        {/* Multi-Agent Card */}
        <div className="p-6 bg-slate-900/60 border border-cyan-500/30 rounded-2xl shadow-xl space-y-5 ring-1 ring-cyan-500/20">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-cyan-300">Multi-Agent Workflow</h3>
              <p className="text-xs text-slate-400">Collaborative 12-agent pipeline with self-correction</p>
            </div>
            <span className="px-2.5 py-1 text-xs font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800 rounded-md">
              High Assurance
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Avg Latency</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-100">
                {data.multi_agent_metrics.avg_latency_seconds}s
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Validation Pass Rate</span>
              </div>
              <div className="text-xl font-bold font-mono text-emerald-400">
                {data.multi_agent_metrics.validation_pass_rate}%
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-blue-400" />
                <span>Quality Score</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-100">
                {data.multi_agent_metrics.avg_quality_score}/100
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-850">
              <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                <span>Security Score</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-100">
                {data.multi_agent_metrics.avg_security_score}/100
              </div>
            </div>
          </div>

          <p className="text-xs text-cyan-200 leading-relaxed bg-cyan-950/30 p-3 rounded-lg border border-cyan-800/40">
            <strong>Optimal For:</strong> {data.multi_agent_metrics.suitability}
          </p>
        </div>
      </div>

      {/* Comparison Matrix Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 bg-slate-900 border-b border-slate-800">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Feature & Capability Comparison Matrix
          </h4>
        </div>
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
              <th className="py-3 px-6">Evaluation Dimension</th>
              <th className="py-3 px-6">Single-Agent Paradigm</th>
              <th className="py-3 px-6">Multi-Agent State Machine</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-slate-300">
            {data.comparison_matrix.map((row, i) => (
              <tr key={i} className="hover:bg-slate-850 transition-colors">
                <td className="py-3.5 px-6 font-semibold text-slate-100">{row.dimension}</td>
                <td className="py-3.5 px-6 text-slate-400">{row.single_agent}</td>
                <td className="py-3.5 px-6 font-medium text-cyan-300">{row.multi_agent}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
