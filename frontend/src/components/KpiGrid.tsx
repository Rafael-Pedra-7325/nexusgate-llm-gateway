import React from 'react';
import { DollarSign, Cpu, Gauge, DatabaseZap } from 'lucide-react';
import { KpiMetrics } from '../types';

interface KpiGridProps {
  kpis: KpiMetrics;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ kpis }) => {
  const cards = [
    {
      title: 'Net Inference Spend',
      value: `$${kpis.total_cost_usd.toFixed(4)}`,
      subtext: `Saved $${kpis.total_savings_usd.toFixed(4)} (${kpis.savings_percentage}%) vs GPT-4o`,
      badge: `-${kpis.savings_percentage}% COST`,
      badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25',
      icon: <DollarSign className="w-5 h-5 text-emerald-400" />,
    },
    {
      title: 'Semantic Cache Hit Rate',
      value: `${kpis.cache_hit_rate}%`,
      subtext: `${kpis.cache_hits} cached hits out of ${kpis.total_requests} total requests`,
      badge: 'ZERO-COST HITS',
      badgeColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/25',
      icon: <DatabaseZap className="w-5 h-5 text-cyan-400" />,
    },
    {
      title: 'Total Tokens Routed',
      value: kpis.total_tokens.toLocaleString(),
      subtext: `${kpis.prompt_tokens.toLocaleString()} prompt • ${kpis.completion_tokens.toLocaleString()} completion`,
      badge: `${kpis.total_requests} REQS`,
      badgeColor: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/25',
      icon: <Cpu className="w-5 h-5 text-indigo-400" />,
    },
    {
      title: 'Gateway Latency (Avg / P95)',
      value: `${kpis.avg_latency_ms} ms`,
      subtext: `P95 tail latency: ${kpis.p95_latency_ms} ms • ${kpis.fallback_count} fallbacks`,
      badge: 'SLA HEALTHY',
      badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/25',
      icon: <Gauge className="w-5 h-5 text-amber-400" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.title} className="glass-card rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60">
              {card.icon}
            </div>
            <span className={`text-[11px] font-mono px-2.5 py-0.5 rounded-full border ${card.badgeColor}`}>
              {card.badge}
            </span>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{card.title}</p>
            <p className="text-2xl font-bold text-white mt-1 font-mono">{card.value}</p>
            <p className="text-xs text-slate-400 mt-2">{card.subtext}</p>
          </div>
        </div>
      ))}
    </div>
  );
};
