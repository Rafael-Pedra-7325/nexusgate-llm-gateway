import React, { useState } from 'react';
import {
  Send,
  Sparkles,
  DatabaseZap,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Clock,
  DollarSign,
} from 'lucide-react';
import { sendGatewayCompletion } from '../api';
import { ChatCompletionResult } from '../types';

interface PlaygroundProps {
  onRequestCompleted: () => void;
}

const PRESETS = [
  {
    label: '1. Simple Fact (Low Cost)',
    prompt: 'What is the capital of France?',
    strategy: 'complexity' as const,
    fail: false,
  },
  {
    label: '2. Paraphrase (Semantic Cache Hit)',
    prompt: "Tell me France's capital city",
    strategy: 'complexity' as const,
    fail: false,
  },
  {
    label: '3. Complex Architecture (GPT-4o)',
    prompt:
      'Design a distributed rate limiter in Python using Redis Lua scripts and compare sliding window vs token bucket trade-offs.',
    strategy: 'complexity' as const,
    fail: false,
  },
  {
    label: '4. Primary Outage (Auto-Fallback)',
    prompt:
      'Architect a multi-region consensus engine comparing Raft and Paxos algorithms under network partitions.',
    strategy: 'complexity' as const,
    fail: true,
  },
];

export const Playground: React.FC<PlaygroundProps> = ({ onRequestCompleted }) => {
  const [prompt, setPrompt] = useState(PRESETS[0].prompt);
  const [strategy, setStrategy] = useState<'complexity' | 'cost' | 'balanced'>('complexity');
  const [useCache, setUseCache] = useState(true);
  const [cacheThreshold, setCacheThreshold] = useState(0.72);
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatCompletionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || loading) return;

    setLoading(true);
    setError(null);
    try {
      const res = await sendGatewayCompletion({
        prompt,
        strategy,
        useCache,
        cacheThreshold,
        simulateFailure,
      });
      setResult(res);
      onRequestCompleted();
    } catch (err: any) {
      setError(err.message || 'Failed to execute gateway request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Controls Panel */}
      <div className="lg:col-span-5 space-y-5">
        <div className="glass-card rounded-2xl p-5 space-y-5">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              Interactive Gateway Simulator
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Test prompt complexity scoring, vector cache hits, and automatic provider failover live.
            </p>
          </div>

          {/* Quick Scenario Presets */}
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              One-Click Test Scenarios
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {PRESETS.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => {
                    setPrompt(p.prompt);
                    setStrategy(p.strategy);
                    setSimulateFailure(p.fail);
                  }}
                  className="text-left text-xs p-2.5 rounded-xl bg-obsidian-950/90 hover:bg-slate-800/80 border border-slate-800 hover:border-cyan-500/40 text-slate-200 transition"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleRun} className="space-y-4">
            {/* Routing Policy Selector */}
            <div>
              <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
                Routing Policy
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['complexity', 'cost', 'balanced'] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStrategy(s)}
                    className={`py-2 px-3 rounded-xl text-xs font-medium capitalize border transition ${
                      strategy === s
                        ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-300'
                        : 'bg-obsidian-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Semantic Cache & Chaos Testing Toggles */}
            <div className="p-3.5 rounded-xl bg-obsidian-950/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-200 flex items-center gap-2">
                  <DatabaseZap className="w-4 h-4 text-cyan-400" />
                  Semantic Vector Cache
                </span>
                <input
                  type="checkbox"
                  checked={useCache}
                  onChange={(e) => setUseCache(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
                />
              </div>

              {useCache && (
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Cosine Similarity Threshold</span>
                    <span className="font-mono text-cyan-300">{cacheThreshold.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.55"
                    max="0.95"
                    step="0.01"
                    value={cacheThreshold}
                    onChange={(e) => setCacheThreshold(parseFloat(e.target.value))}
                    className="w-full accent-cyan-400"
                  />
                </div>
              )}

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-xs font-medium text-amber-300 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  Simulate Primary 429 Outage
                </span>
                <input
                  type="checkbox"
                  checked={simulateFailure}
                  onChange={(e) => setSimulateFailure(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-amber-500 focus:ring-amber-500"
                />
              </div>
            </div>

            {/* Prompt Input */}
            <div>
              <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                Prompt Payload
              </label>
              <textarea
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter any prompt to test routing, caching, or fallback..."
                className="w-full rounded-xl bg-obsidian-950 border border-slate-800 focus:border-cyan-500/60 focus:outline-none p-3 text-sm text-slate-100 placeholder-slate-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 transition disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {loading ? 'Routing Request...' : 'Dispatch Through Gateway'}
            </button>
          </form>
        </div>
      </div>

      {/* Right Execution Trace & Response Panel */}
      <div className="lg:col-span-7 space-y-5">
        {error && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
            {error}
          </div>
        )}

        {!result ? (
          <div className="glass-card rounded-2xl p-10 h-full flex flex-col items-center justify-center text-center border-dashed">
            <Sparkles className="w-10 h-10 text-cyan-400/60 mb-3" />
            <h3 className="text-base font-semibold text-white">Ready to Intercept & Route</h3>
            <p className="text-xs text-slate-400 max-w-md mt-1">
              Select a preset scenario on the left or type your own prompt to inspect real-time
              complexity classification, vector cache similarity, and failover execution traces.
            </p>
          </div>
        ) : (
          <>
            {/* Telemetry Badges Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="glass-card rounded-xl p-3.5">
                <p className="text-[11px] text-slate-400 uppercase">Selected Model</p>
                <p className="text-sm font-bold text-cyan-300 font-mono mt-0.5 truncate">
                  {result.gateway.selected_model}
                </p>
                <p className="text-[11px] text-slate-500 uppercase">{result.gateway.provider}</p>
              </div>

              <div className="glass-card rounded-xl p-3.5">
                <p className="text-[11px] text-slate-400 uppercase">Cache Status</p>
                <p
                  className={`text-sm font-bold font-mono mt-0.5 ${
                    result.gateway.cache_hit ? 'text-emerald-400' : 'text-slate-300'
                  }`}
                >
                  {result.gateway.cache_hit ? 'CACHE HIT' : 'CACHE MISS'}
                </p>
                <p className="text-[11px] text-slate-500">
                  Sim: {result.gateway.cache_similarity?.toFixed(2) ?? '0.00'}
                </p>
              </div>

              <div className="glass-card rounded-xl p-3.5">
                <p className="text-[11px] text-slate-400 uppercase flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Latency
                </p>
                <p className="text-sm font-bold text-white font-mono mt-0.5">
                  {result.gateway.latency_ms} ms
                </p>
                <p className="text-[11px] text-slate-500">
                  {result.usage.total_tokens} tokens
                </p>
              </div>

              <div className="glass-card rounded-xl p-3.5">
                <p className="text-[11px] text-slate-400 uppercase flex items-center gap-1">
                  <DollarSign className="w-3 h-3" /> Cost / Saved
                </p>
                <p className="text-sm font-bold text-emerald-400 font-mono mt-0.5">
                  ${result.gateway.cost_usd.toFixed(6)}
                </p>
                <p className="text-[11px] text-emerald-500/80">
                  Saved ${result.gateway.savings_usd.toFixed(6)}
                </p>
              </div>
            </div>

            {/* Execution Pipeline Waterfall */}
            <div className="glass-card rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white">Gateway Execution Trace</h3>
                <span className="text-xs font-mono text-slate-400">
                  Complexity: {result.gateway.complexity_score} ({result.gateway.complexity_tier})
                </span>
              </div>

              <div className="space-y-2.5">
                {result.gateway.trace.map((step, idx) => {
                  const isFailed = step.status === 'failed';
                  const isGood =
                    step.status === 'hit' ||
                    step.status === 'recovered' ||
                    step.status === 'completed';

                  return (
                    <div
                      key={idx}
                      className="flex items-start justify-between gap-3 p-3 rounded-xl bg-obsidian-950/90 border border-slate-800/90"
                    >
                      <div className="flex items-start gap-2.5">
                        {isFailed ? (
                          <XCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                        ) : isGood ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                        ) : (
                          <ArrowRight className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
                        )}
                        <div>
                          <p className="text-xs font-semibold text-slate-200">{step.step}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{step.detail}</p>
                        </div>
                      </div>
                      <span className="text-[11px] font-mono text-slate-400 shrink-0">
                        {step.duration_ms} ms
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Assistant Response Output */}
            <div className="glass-card rounded-2xl p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Completion Payload
                </span>
                <span className="text-[11px] font-mono text-slate-500">{result.id}</span>
              </div>
              <div className="p-4 rounded-xl bg-obsidian-950 border border-slate-800 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                {result.choices[0]?.message.content}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
