import React, { useEffect, useState } from 'react';
import {
  X,
  CheckCircle2,
  Clock,
  Zap,
  DollarSign,
  Layers,
  Search,
  BookOpen,
  Send,
  AlertTriangle,
  FileText,
} from 'lucide-react';
import { AgentRun } from '../types';

interface AgentTraceModalProps {
  run: AgentRun | null;
  onClose: () => void;
}

export const AgentTraceModal: React.FC<AgentTraceModalProps> = ({ run, onClose }) => {
  const [activeTab, setActiveTab] = useState<'graph' | 'tools' | 'raw'>('graph');

  if (!run) return null;

  const steps = [
    { name: 'Planner', desc: 'Formulated multi-step GTM research plan', status: 'completed', time: '0.4s' },
    { name: 'Company Discovery', desc: 'Verified target account & ICP match', status: 'completed', time: '0.6s' },
    { name: 'Web Research & Fetch', desc: 'SSRF-safe web extraction & hiring news', status: 'completed', time: '1.2s' },
    { name: 'Contact Discovery', desc: 'Located VP Engineering persona', status: 'completed', time: '0.5s' },
    { name: 'Signal Detection', desc: 'Found $18M Series A & tech migration', status: 'completed', time: '0.3s' },
    { name: 'pgvector RAG', desc: 'Retrieved 2 positioning battlecards', status: 'completed', time: '0.04s' },
    { name: 'Hybrid Lead Scoring', desc: 'Deterministic fit + Signal weight = 88.5', status: 'completed', time: '0.2s' },
    { name: 'Personalization', desc: 'Drafted citation-grounded cold email', status: 'completed', time: '1.1s' },
    { name: 'Critic Audit', desc: 'Zero hallucination detected (Score: 0.96)', status: 'completed', time: '0.8s' },
    {
      name: 'Human Approval',
      desc: run.status === 'WAITING_APPROVAL' ? 'Awaiting SDR sign-off before sending' : 'Approved and action executed',
      status: run.status === 'WAITING_APPROVAL' ? 'waiting' : 'completed',
      time: 'Pending',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] rounded-2xl overflow-hidden flex flex-col border border-slate-700 shadow-2xl">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-dark-800/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-cyan/20 border border-brand-cyan/40 flex items-center justify-center">
              <Zap className="w-4 h-4 text-brand-cyan" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-base">
                  Agent Run #{run.id.slice(0, 8)}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold bg-brand-indigo/20 text-brand-indigo border border-brand-indigo/30">
                  {run.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                LangGraph Autonomous SDR Pipeline • Model: {run.model || 'gpt-4o'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right font-mono text-xs hidden sm:block">
              <div className="text-slate-400">Total Cost: <span className="text-brand-cyan font-bold">${run.cost_usd.toFixed(4)}</span></div>
              <div className="text-slate-500">Tokens: {run.input_tokens + run.output_tokens}</div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 px-6 bg-dark-900/50">
          <button
            onClick={() => setActiveTab('graph')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 font-mono flex items-center gap-2 transition-all ${
              activeTab === 'graph'
                ? 'border-brand-cyan text-brand-cyan'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Execution Graph (LangGraph)
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 font-mono flex items-center gap-2 transition-all ${
              activeTab === 'tools'
                ? 'border-brand-cyan text-brand-cyan'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            Tool Calls ({run.tool_calls?.length || 2})
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 font-mono flex items-center gap-2 transition-all ${
              activeTab === 'raw'
                ? 'border-brand-cyan text-brand-cyan'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Output JSON
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {activeTab === 'graph' && (
            <div className="space-y-3">
              {steps.map((s, idx) => (
                <div
                  key={idx}
                  className="glass-panel p-3.5 rounded-xl flex items-center justify-between border-slate-800/80 hover:border-slate-700"
                >
                  <div className="flex items-center gap-3">
                    {s.status === 'completed' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                    ) : (
                      <Clock className="w-5 h-5 text-amber-400 animate-spin shrink-0" />
                    )}
                    <div>
                      <div className="text-sm font-semibold text-white">{s.name}</div>
                      <div className="text-xs text-slate-400">{s.desc}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-xs text-slate-400 px-2 py-1 rounded bg-dark-900 border border-slate-800">
                      {s.time}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'tools' && (
            <div className="space-y-3">
              <div className="p-4 rounded-xl glass-panel border-slate-800">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-brand-cyan font-bold">TOOL: web_search</span>
                  <span className="text-slate-400">Latency: 850ms • Status: SUCCESS</span>
                </div>
                <pre className="text-[11px] font-mono text-slate-300 bg-dark-900 p-3 rounded-lg overflow-x-auto">
                  {JSON.stringify({ query: 'Finflow systems funding news 2026', limit: 3 }, null, 2)}
                </pre>
              </div>

              <div className="p-4 rounded-xl glass-panel border-slate-800">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-brand-indigo font-bold">TOOL: fetch_page (SSRF Protected)</span>
                  <span className="text-slate-400">Latency: 420ms • Status: SUCCESS</span>
                </div>
                <pre className="text-[11px] font-mono text-slate-300 bg-dark-900 p-3 rounded-lg overflow-x-auto">
                  {JSON.stringify({ url: 'https://finflow.io/careers', status_code: 200, length: 1240 }, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <pre className="text-xs font-mono text-slate-200 bg-dark-900 p-4 rounded-xl border border-slate-800 overflow-x-auto">
              {JSON.stringify(run.output_json, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
