import React from 'react';
import { Activity, Terminal, ListFilter, Sliders, Zap, RefreshCw } from 'lucide-react';

export type ActiveTab = 'overview' | 'playground' | 'logs' | 'config';

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  sandboxMode: boolean;
  onRefresh: () => void;
  refreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  sandboxMode,
  onRefresh,
  refreshing,
}) => {
  const navItems: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Observability', icon: <Activity className="w-4 h-4" /> },
    { id: 'playground', label: 'Live Playground', icon: <Terminal className="w-4 h-4" /> },
    { id: 'logs', label: 'Trace Logs', icon: <ListFilter className="w-4 h-4" /> },
    { id: 'config', label: 'Routing & SDK', icon: <Sliders className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-[#07090E]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Zap className="w-5 h-5 text-slate-950 fill-slate-950" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-white">NexusGate</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              LLM Proxy • Semantic Cache • Cost & Complexity Router
            </p>
          </div>
        </div>

        {/* Navigation Pills */}
        <nav className="flex items-center gap-1 bg-obsidian-900/90 p-1 rounded-xl border border-slate-800/80">
          {navItems.map((item) => {
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  active
                    ? 'bg-slate-800 text-cyan-300 shadow-sm border border-slate-700/70'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Status & Refresh */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-xs font-mono text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            {sandboxMode ? 'SANDBOX MODE' : 'LIVE PROVIDERS'}
          </div>
          <button
            onClick={onRefresh}
            title="Refresh telemetry"
            className="p-2 rounded-lg border border-slate-800 bg-obsidian-900 text-slate-400 hover:text-white hover:border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
