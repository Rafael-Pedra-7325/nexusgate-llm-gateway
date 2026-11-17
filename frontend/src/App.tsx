import React, { useEffect, useState, useCallback } from 'react';
import { Navbar, ActiveTab } from './components/Navbar';
import { KpiGrid } from './components/KpiGrid';
import { AnalyticsCharts } from './components/AnalyticsCharts';
import { Playground } from './components/Playground';
import { RequestLogs } from './components/RequestLogs';
import { RoutingConfig } from './components/RoutingConfig';
import { fetchAnalytics, fetchLogs, fetchConfig } from './api';
import { AnalyticsResponse, RequestLogItem } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [logs, setLogs] = useState<RequestLogItem[]>([]);
  const [config, setConfig] = useState<Record<string, any> | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadAll = useCallback(async () => {
    setRefreshing(true);
    try {
      const [aData, lData, cData] = await Promise.all([
        fetchAnalytics(),
        fetchLogs(60),
        fetchConfig(),
      ]);
      setAnalytics(aData);
      setLogs(lData);
      setConfig(cData);
    } catch (err) {
      console.error('Failed to refresh telemetry:', err);
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  return (
    <div className="min-h-screen flex flex-col bg-[#07090E] text-slate-100">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        sandboxMode={analytics?.sandbox_mode ?? true}
        onRefresh={loadAll}
        refreshing={refreshing}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {analytics && <KpiGrid kpis={analytics.kpis} />}

        {activeTab === 'overview' && analytics && <AnalyticsCharts data={analytics} />}
        {activeTab === 'playground' && <Playground onRequestCompleted={loadAll} />}
        {activeTab === 'logs' && <RequestLogs logs={logs} />}
        {activeTab === 'config' && <RoutingConfig config={config} onCacheCleared={loadAll} />}
      </main>

      <footer className="border-t border-slate-800/70 py-4 text-center text-xs text-slate-500">
        NexusGate LLM Proxy & Observability Control Plane • OpenAI-Compatible API Gateway
      </footer>
    </div>
  );
}
