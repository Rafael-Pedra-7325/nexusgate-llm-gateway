import React, { useState } from 'react';
import { Search, DatabaseZap, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { RequestLogItem } from '../types';

interface RequestLogsProps {
  logs: RequestLogItem[];
}

export const RequestLogs: React.FC<RequestLogsProps> = ({ logs }) => {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'cache' | 'fallback'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = logs.filter((log) => {
    if (filter === 'cache' && !log.cache_hit) return false;
    if (filter === 'fallback' && !log.fallback_triggered) return false;
    if (
      query &&
      !log.prompt_preview.toLowerCase().includes(query.toLowerCase()) &&
      !log.selected_model.toLowerCase().includes(query.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="glass-card rounded-2xl p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white">Live Gateway Request Telemetry</h2>
          <p className="text-xs text-slate-400">
            Click any row to inspect routing decisions, similarity scores, and fallback traces
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter prompt or model..."
              className="pl-8 pr-3 py-1.5 rounded-xl bg-obsidian-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          {(['all', 'cache', 'fallback'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium capitalize border transition ${
                filter === f
                  ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300'
                  : 'bg-obsidian-950 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {f === 'cache' ? 'Cache Hits' : f === 'fallback' ? 'Fallbacks' : 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-[11px] font-mono uppercase text-slate-400">
              <th className="py-3 px-3">Prompt Preview</th>
              <th className="py-3 px-3">Routed Model</th>
              <th className="py-3 px-3">Complexity</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3 text-right">Tokens</th>
              <th className="py-3 px-3 text-right">Cost</th>
              <th className="py-3 px-3 text-right">Latency</th>
              <th className="py-3 px-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs">
            {filtered.map((log) => {
              const isOpen = expandedId === log.request_id;
              return (
                <React.Fragment key={log.request_id}>
                  <tr
                    onClick={() => setExpandedId(isOpen ? null : log.request_id)}
                    className="hover:bg-slate-800/35 cursor-pointer transition"
                  >
                    <td className="py-3 px-3 max-w-xs truncate text-slate-200 font-medium">
                      {log.prompt_preview}
                    </td>
                    <td className="py-3 px-3 font-mono text-cyan-300">{log.selected_model}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded-md font-mono text-[11px] ${
                          log.complexity_tier === 'complex'
                            ? 'bg-purple-500/15 text-purple-300'
                            : log.complexity_tier === 'moderate'
                            ? 'bg-indigo-500/15 text-indigo-300'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {log.complexity_score.toFixed(2)} ({log.complexity_tier})
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1.5">
                        {log.cache_hit && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono">
                            <DatabaseZap className="w-3 h-3" /> CACHE
                          </span>
                        )}
                        {log.fallback_triggered && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 text-[10px] font-mono">
                            <RefreshCw className="w-3 h-3" /> FALLBACK
                          </span>
                        )}
                        {!log.cache_hit && !log.fallback_triggered && (
                          <span className="text-slate-400 font-mono text-[11px]">DIRECT</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-300">
                      {log.total_tokens}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-emerald-400">
                      ${log.cost_usd.toFixed(5)}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-200">
                      {log.latency_ms} ms
                    </td>
                    <td className="py-3 px-2 text-slate-500">
                      {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </td>
                  </tr>

                  {isOpen && (
                    <tr className="bg-obsidian-950/90">
                      <td colSpan={8} className="p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-[11px] font-mono uppercase text-slate-400 mb-2">
                              Execution Steps ({log.request_id})
                            </p>
                            <div className="space-y-1.5">
                              {log.trace.map((step, i) => (
                                <div
                                  key={i}
                                  className="text-xs flex items-center justify-between p-2 rounded-lg bg-slate-900/90 border border-slate-800"
                                >
                                  <span className="text-slate-200">
                                    <strong className="text-cyan-300">{step.step}:</strong>{' '}
                                    {step.detail}
                                  </span>
                                  <span className="font-mono text-slate-400">
                                    {step.duration_ms}ms
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="text-xs space-y-1.5 font-mono text-slate-300 bg-slate-900/70 p-3.5 rounded-xl border border-slate-800">
                            <p>Strategy: {log.routing_strategy}</p>
                            <p>Attempted Chain: {log.attempted_models.join(' → ')}</p>
                            <p>Baseline GPT-4o Cost: ${log.baseline_cost_usd.toFixed(6)}</p>
                            <p className="text-emerald-400">
                              Net Savings: ${log.savings_usd.toFixed(6)}
                            </p>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
