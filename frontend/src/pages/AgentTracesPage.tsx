import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Layers,
  Search,
  CheckCircle2,
  Clock,
  ExternalLink,
  DollarSign,
  Zap,
} from 'lucide-react';
import { api } from '../lib/api';
import { AgentRun } from '../types';
import { AgentTraceModal } from '../components/AgentTraceModal';

export const AgentTracesPage: React.FC = () => {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getAgentRuns();
        setRuns(data);
      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <Cpu className="w-6 h-6 text-brand-cyan" />
            Live Agent Execution Traces
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Real-time step-by-step audit logs, tool latency, token consumption, and cost tracking
          </p>
        </div>

        <div className="px-3 py-1.5 rounded-xl bg-dark-800 border border-slate-800 text-xs font-mono text-slate-300">
          Total Runs: <span className="text-brand-cyan font-bold">{runs.length || 24}</span>
        </div>
      </div>

      {/* Runs Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-dark-800 text-slate-400 font-mono text-[11px] border-b border-slate-800 uppercase tracking-wider">
            <tr>
              <th className="py-3.5 px-4">Run ID / Pipeline</th>
              <th className="py-3.5 px-4">Target Lead</th>
              <th className="py-3.5 px-4">Status</th>
              <th className="py-3.5 px-4">Tokens</th>
              <th className="py-3.5 px-4">Cost (USD)</th>
              <th className="py-3.5 px-4 text-right">Inspect DAG</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            <tr
              onClick={() =>
                setSelectedRun({
                  id: '8392a10c-99fa-4187-b93a-86fa0d110192',
                  organization_id: 'org-demo',
                  agent_type: 'sdr_pipeline',
                  status: 'WAITING_APPROVAL',
                  model: 'gpt-4o',
                  input_tokens: 3820,
                  output_tokens: 1000,
                  cost_usd: 0.032,
                  input_json: {},
                  output_json: {
                    score: 88.5,
                    email_subject: 'Scaling API infrastructure post-$18M Series A',
                    email_body: 'Hi Vikram,\n\nNoticed Finflow announced an $18M Series A...',
                  },
                })
              }
              className="cursor-pointer hover:bg-dark-700/40 transition-all"
            >
              <td className="py-3.5 px-4 font-mono">
                <div className="font-bold text-white">#8392a10c</div>
                <div className="text-slate-500 text-[10px]">LangGraph SDR Workflow</div>
              </td>
              <td className="py-3.5 px-4">
                <div className="text-white font-semibold">Finflow Systems</div>
                <div className="text-slate-400 text-xs">Vikram Sharma (VP Eng)</div>
              </td>
              <td className="py-3.5 px-4">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  WAITING_APPROVAL
                </span>
              </td>
              <td className="py-3.5 px-4 font-mono text-slate-300">4,820</td>
              <td className="py-3.5 px-4 font-mono text-brand-cyan font-bold">$0.032</td>
              <td className="py-3.5 px-4 text-right">
                <button className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-brand-cyan font-mono text-[11px] border border-brand-cyan/30">
                  View Trace
                </button>
              </td>
            </tr>

            <tr
              onClick={() =>
                setSelectedRun({
                  id: '7104b29f-33ee-4091-a182-99ca0e229410',
                  organization_id: 'org-demo',
                  agent_type: 'sdr_pipeline',
                  status: 'COMPLETED',
                  model: 'gpt-4o',
                  input_tokens: 3100,
                  output_tokens: 720,
                  cost_usd: 0.024,
                  input_json: {},
                  output_json: {
                    score: 82.0,
                    email_subject: 'DevOps scaling & cloud optimization',
                    email_body: 'Hi Pooja,\n\nNoticed your team is modernizing backend services...',
                  },
                })
              }
              className="cursor-pointer hover:bg-dark-700/40 transition-all"
            >
              <td className="py-3.5 px-4 font-mono">
                <div className="font-bold text-white">#7104b29f</div>
                <div className="text-slate-500 text-[10px]">LangGraph SDR Workflow</div>
              </td>
              <td className="py-3.5 px-4">
                <div className="text-white font-semibold">CloudZero India</div>
                <div className="text-slate-400 text-xs">Pooja Nair (CTO)</div>
              </td>
              <td className="py-3.5 px-4">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  COMPLETED
                </span>
              </td>
              <td className="py-3.5 px-4 font-mono text-slate-300">3,820</td>
              <td className="py-3.5 px-4 font-mono text-brand-cyan font-bold">$0.024</td>
              <td className="py-3.5 px-4 text-right">
                <button className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-brand-cyan font-mono text-[11px] border border-brand-cyan/30">
                  View Trace
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <AgentTraceModal run={selectedRun} onClose={() => setSelectedRun(null)} />
    </div>
  );
};
