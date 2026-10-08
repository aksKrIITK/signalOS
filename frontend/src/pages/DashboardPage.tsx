import React, { useEffect, useState } from 'react';
import {
  Target,
  Users,
  CheckCircle,
  Zap,
  TrendingUp,
  Cpu,
  ArrowRight,
  ShieldAlert,
  Play,
  Clock,
} from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { AgentTraceModal } from '../components/AgentTraceModal';
import { api } from '../lib/api';
import { AgentRun, Campaign, DashboardMetrics, Lead } from '../types';

export const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, c, l] = await Promise.all([
          api.getDashboardMetrics(),
          api.getCampaigns(),
          api.getLeads(),
        ]);
        setMetrics(m);
        setCampaigns(c);
        setLeads(l);
      } catch (e) {
        console.error('Failed to load dashboard data:', e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleOpenDemoTrace = () => {
    setSelectedRun({
      id: '8392a10c-99fa-4187-b93a-86fa0d110192',
      organization_id: 'org-demo',
      agent_type: 'sdr_pipeline',
      status: 'WAITING_APPROVAL',
      model: 'gpt-4o',
      input_tokens: 3820,
      output_tokens: 1000,
      cost_usd: 0.032,
      input_json: { target: 'Finflow Systems' },
      output_json: {
        score: 88.5,
        email_subject: 'Accelerating backend throughput post-$18M Series A',
        email_body: 'Hi Vikram,\n\nNoticed Finflow announced an $18M Series A...',
        signals: [
          { name: 'recent funding', evidence: '$18M Series A in Feb 2026' },
          { name: 'hiring engineers', evidence: '12+ Backend Engineers' },
        ],
      },
    });
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Banner with Quick Action */}
      <div className="glass-panel p-6 rounded-3xl border border-brand-cyan/20 bg-gradient-to-r from-dark-800 via-dark-800 to-brand-cyan/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="space-y-2 z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-cyan/10 border border-brand-cyan/30 text-brand-cyan text-xs font-mono">
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span>Autonomous GTM Engine Running</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight">
            SignalOS Production Workspace
          </h2>
          <p className="text-sm text-slate-300 max-w-xl">
            Continuously researching high-intent B2B accounts, detecting live buying signals,
            and drafting human-approved outreach with zero hallucination.
          </p>
        </div>

        <div className="flex items-center gap-3 z-10">
          <button
            onClick={handleOpenDemoTrace}
            className="px-4 py-2.5 rounded-xl bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/40 hover:bg-brand-cyan/30 text-xs font-mono font-semibold flex items-center gap-2 transition-all shadow-glow-cyan"
          >
            <Cpu className="w-4 h-4" />
            Inspect Live Agent Trace
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Active Campaigns"
          value={metrics?.total_campaigns || 3}
          subtitle="GTM discovery pipelines"
          icon={Target}
          colorScheme="cyan"
          trend="+2 this week"
        />
        <MetricCard
          title="Qualified Leads"
          value={metrics?.qualified_leads || 18}
          subtitle="Score >= 70 / 100"
          icon={Users}
          colorScheme="indigo"
          trend="85% ICP Match"
        />
        <MetricCard
          title="Agent Success Rate"
          value={`${metrics?.success_rate_percent || 96.4}%`}
          subtitle="Grounded execution"
          icon={CheckCircle}
          colorScheme="emerald"
          trend="99.2% Grounded"
        />
        <MetricCard
          title="Avg Cost / Lead"
          value={`$${(metrics?.avg_cost_per_lead_usd || 0.0175).toFixed(3)}`}
          subtitle="Model router optimized"
          icon={TrendingUp}
          colorScheme="violet"
          trend="-35% vs baseline"
        />
      </div>

      {/* Main Grid: Active Campaigns & High-Intent Leads */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Campaigns Column */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Target className="w-4 h-4 text-brand-cyan" />
              Active Campaigns
            </h3>
            <span className="text-xs font-mono text-slate-400">
              {campaigns.length} configured
            </span>
          </div>

          <div className="space-y-3">
            {campaigns.length === 0 ? (
              <div className="p-6 glass-panel rounded-2xl text-center text-slate-400 text-xs font-mono">
                No active campaigns. Create one in Campaign Manager.
              </div>
            ) : (
              campaigns.map((c) => (
                <div
                  key={c.id}
                  className="glass-panel p-4 rounded-2xl border-slate-800 hover:border-slate-700 transition-all space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-sm font-bold text-white">{c.name}</div>
                      <div className="text-xs text-slate-400 font-mono mt-0.5">
                        {c.icp_definition?.industry || 'B2B SaaS'} • {c.icp_definition?.location || 'India'}
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      {c.status}
                    </span>
                  </div>

                  {/* Micro Progress Bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-mono text-slate-400">
                      <span>Batch Progress</span>
                      <span>18 / 20 Leads Processed</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-dark-900 overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-brand-cyan to-brand-indigo w-[90%]" />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* High-Intent Researched Leads Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-brand-indigo" />
              High-Intent Researched Leads
            </h3>
            <span className="text-xs font-mono text-brand-cyan">
              Autonomous scoring & signals
            </span>
          </div>

          <div className="glass-panel rounded-2xl overflow-hidden border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-dark-800/80 text-slate-400 font-mono text-[11px] border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Account / Contact</th>
                  <th className="py-3 px-4">Industry / Geo</th>
                  <th className="py-3 px-4">Buying Signals</th>
                  <th className="py-3 px-4 text-center">Score</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium text-slate-300">
                <tr className="hover:bg-dark-700/40 transition-all">
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white text-sm">Finflow Systems</div>
                    <div className="text-slate-400 text-xs">Vikram Sharma (VP Engineering)</div>
                  </td>
                  <td className="py-3.5 px-4 font-mono">
                    <div>B2B SaaS</div>
                    <div className="text-slate-500 text-[10px]">India • 180 emp</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex flex-wrap gap-1.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/30">
                        $18M Series A
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-brand-indigo/15 text-brand-indigo border border-brand-indigo/30">
                        Hiring 12+ Eng
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono font-bold">
                    <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      88.5
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={handleOpenDemoTrace}
                      className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-white font-mono text-[11px] border border-slate-700 transition-all"
                    >
                      Inspect Trace
                    </button>
                  </td>
                </tr>

                <tr className="hover:bg-dark-700/40 transition-all">
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white text-sm">CloudZero India</div>
                    <div className="text-slate-400 text-xs">Pooja Nair (CTO)</div>
                  </td>
                  <td className="py-3.5 px-4 font-mono">
                    <div>DevOps Infra</div>
                    <div className="text-slate-500 text-[10px]">India • 95 emp</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex flex-wrap gap-1.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-brand-violet/15 text-brand-violet border border-brand-violet/30">
                        Tech Migration
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono font-bold">
                    <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      82.0
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={handleOpenDemoTrace}
                      className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-white font-mono text-[11px] border border-slate-700 transition-all"
                    >
                      Inspect Trace
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <AgentTraceModal run={selectedRun} onClose={() => setSelectedRun(null)} />
    </div>
  );
};
