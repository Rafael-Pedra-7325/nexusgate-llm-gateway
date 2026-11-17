import React, { useState } from 'react';
import { Copy, Check, Trash2, Code2, Layers } from 'lucide-react';
import { clearCache } from '../api';

interface RoutingConfigProps {
  config: Record<string, any> | null;
  onCacheCleared: () => void;
}

export const RoutingConfig: React.FC<RoutingConfigProps> = ({ config, onCacheCleared }) => {
  const [copied, setCopied] = useState(false);
  const [clearing, setClearing] = useState(false);

  const sdkSnippet = `from openai import OpenAI

# Drop-in replacement: point OpenAI SDK to NexusGate
client = OpenAI(
    base_url="${window.location.origin}/v1",
    api_key="nexusgate-proxy-key"
)

response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Design a distributed cache"}],
    extra_headers={
        "X-Routing-Strategy": "complexity",  # complexity | cost | balanced
        "X-Cache-Threshold": "0.72"
    }
)
print(response.choices[0].message.content)`;

  const handleCopy = () => {
    navigator.clipboard.writeText(sdkSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClearCache = async () => {
    setClearing(true);
    await clearCache();
    setClearing(false);
    onCacheCleared();
  };

  const models = config?.models ? Object.entries(config.models) : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Model Pricing & Tier Matrix */}
      <div className="lg:col-span-7 glass-card rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Configured Model Catalog & Pricing Matrix
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Used by the Complexity & Cost router to calculate real-time spend and savings
            </p>
          </div>
          <button
            onClick={handleClearCache}
            disabled={clearing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-xs text-red-300 transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
            {clearing ? 'Flushing...' : 'Flush Semantic Cache'}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-mono uppercase text-slate-400">
                <th className="py-2.5 px-3">Model ID</th>
                <th className="py-2.5 px-3">Provider</th>
                <th className="py-2.5 px-3">Tier</th>
                <th className="py-2.5 px-3 text-right">Input / 1M</th>
                <th className="py-2.5 px-3 text-right">Output / 1M</th>
                <th className="py-2.5 px-3 text-right">Quality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {models.map(([id, m]: [string, any]) => (
                <tr key={id} className="hover:bg-slate-800/30">
                  <td className="py-3 px-3 font-mono text-cyan-300 font-medium">{id}</td>
                  <td className="py-3 px-3 uppercase text-slate-300">{m.provider}</td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                      {m.tier}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-slate-300">
                    ${m.input_cost_per_1m.toFixed(2)}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-slate-300">
                    ${m.output_cost_per_1m.toFixed(2)}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-emerald-400">
                    {m.quality_score}/100
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Drop-In SDK Integration Snippet */}
      <div className="lg:col-span-5 glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Code2 className="w-4 h-4 text-emerald-400" />
              Drop-In OpenAI SDK Integration
            </h3>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Zero SDK lock-in. Route existing Python, Node.js, or LangChain workloads through NexusGate
            by overriding <code className="text-cyan-300">base_url</code>.
          </p>
          <pre className="p-4 rounded-xl bg-obsidian-950 border border-slate-800 text-[11px] font-mono text-slate-200 overflow-x-auto leading-relaxed">
            {sdkSnippet}
          </pre>
        </div>

        <div className="p-3.5 rounded-xl bg-cyan-500/5 border border-cyan-500/20 text-xs text-slate-300">
          <strong className="text-cyan-300">Architecture Tip:</strong> Add your real{' '}
          <code className="font-mono">OPENAI_API_KEY</code>,{' '}
          <code className="font-mono">ANTHROPIC_API_KEY</code>, or{' '}
          <code className="font-mono">GROQ_API_KEY</code> in <code className="font-mono">.env</code>{' '}
          and set <code className="font-mono">SANDBOX_MODE=false</code> to switch from simulated
          responses to live provider traffic.
        </div>
      </div>
    </div>
  );
};
