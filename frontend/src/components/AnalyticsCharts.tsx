import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import { ShieldCheck, AlertTriangle, Server } from 'lucide-react';
import { AnalyticsResponse } from '../types';

interface AnalyticsChartsProps {
  data: AnalyticsResponse;
}

const MODEL_COLORS = ['#22d3ee', '#10b981', '#818cf8', '#f59e0b', '#f472b6'];

export const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ data }) => {
  return (
    <div className="space-y-6">
      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost Optimization Area Chart */}
        <div className="glass-card rounded-2xl p-6 lg:col-span-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
            <div>
              <h3 className="text-base font-semibold text-white">
                Cost Optimization: Routed Spend vs. Unrouted Baseline
              </h3>
              <p className="text-xs text-slate-400">
                Real-time comparison of actual gateway cost against uncached GPT-4o baseline ($)
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-500" /> Baseline
              </span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Actual Spend
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.timeseries}>
                <defs>
                  <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="baseGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#64748b" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#64748b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time_bucket" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0d1117',
                    borderColor: '#334155',
                    borderRadius: '12px',
                    fontSize: '12px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="baseline_cost"
                  name="Baseline Cost ($)"
                  stroke="#64748b"
                  fillOpacity={1}
                  fill="url(#baseGrad)"
                />
                <Area
                  type="monotone"
                  dataKey="actual_cost"
                  name="Actual Spend ($)"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#actualGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model Distribution Bar Chart */}
        <div className="glass-card rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Model Routing Split</h3>
            <p className="text-xs text-slate-400 mb-4">Request volume dispatched per model</p>
          </div>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.model_breakdown} layout="vertical" margin={{ left: 10, right: 15 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="model"
                  stroke="#94a3b8"
                  fontSize={11}
                  width={125}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0d1117',
                    borderColor: '#334155',
                    borderRadius: '12px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="requests" name="Requests" radius={[0, 6, 6, 0]}>
                  {data.model_breakdown.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={MODEL_COLORS[index % MODEL_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Cached Vectors: {data.cache.entries_count}</span>
            <span>Threshold: {data.cache.default_threshold}</span>
          </div>
        </div>
      </div>

      {/* Provider Circuit Breaker Health Strip */}
      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">Upstream Provider Circuit Breakers</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Auto-Failover Chain: OpenAI → Anthropic → Groq
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.providers.map((p) => {
            const isHealthy = p.status === 'healthy';
            return (
              <div
                key={p.provider}
                className="flex items-center justify-between p-3.5 rounded-xl bg-obsidian-950/70 border border-slate-800"
              >
                <div className="flex items-center gap-3">
                  {isHealthy ? (
                    <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                  )}
                  <div>
                    <p className="text-sm font-semibold text-white uppercase tracking-wide">
                      {p.provider}
                    </p>
                    <p className="text-xs text-slate-400">
                      {p.total_successes} successful calls • {p.recent_failures} recent errors
                    </p>
                  </div>
                </div>
                <span
                  className={`text-[11px] font-mono px-2.5 py-1 rounded-full border ${
                    isHealthy
                      ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/25'
                      : 'text-amber-300 bg-amber-500/10 border-amber-500/25'
                  }`}
                >
                  {p.status.toUpperCase()}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
