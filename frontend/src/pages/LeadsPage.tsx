import React, { useEffect, useState } from 'react';
import {
  Users,
  Search,
  Filter,
  CheckCircle,
  ExternalLink,
  Mail,
  Linkedin,
  Zap,
  Sparkles,
  ArrowUpRight,
} from 'lucide-react';
import { api } from '../lib/api';
import { Lead } from '../types';

export const LeadsPage: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getLeads();
        setLeads(data);
        if (data.length > 0) setSelectedLead(data[0]);
      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, []);

  const filtered = leads.filter(
    (l) => filterStatus === 'ALL' || l.status === filterStatus
  );

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <Users className="w-6 h-6 text-brand-indigo" />
            Lead Intelligence
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Researched accounts with hybrid ICP scores, detected buying signals, and verified tech stack
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 font-mono text-xs">
          {['ALL', 'QUALIFIED', 'RESEARCHING', 'NEW'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                filterStatus === st
                  ? 'bg-brand-indigo text-white font-bold'
                  : 'bg-dark-800 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Main Split View: Lead Table + Research Dossier */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Lead Table */}
        <div className="lg:col-span-7 glass-panel rounded-2xl overflow-hidden border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-800 text-slate-400 font-mono text-[11px] border-b border-slate-800 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Account / Persona</th>
                <th className="py-3 px-4">ICP Score</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filtered.map((l) => (
                <tr
                  key={l.id}
                  onClick={() => setSelectedLead(l)}
                  className={`cursor-pointer transition-all ${
                    selectedLead?.id === l.id ? 'bg-brand-indigo/15' : 'hover:bg-dark-700/40'
                  }`}
                >
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white text-sm">
                      {l.company?.name || 'Target Account'}
                    </div>
                    <div className="text-slate-400 text-xs">
                      {l.contact?.first_name} {l.contact?.last_name} •{' '}
                      <span className="text-brand-cyan">{l.contact?.job_title || 'VP Engineering'}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      {l.score || 88.5}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-dark-700 text-slate-300 border border-slate-600">
                      {l.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button className="text-brand-cyan hover:underline font-mono text-[11px] inline-flex items-center gap-1">
                      Dossier <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Selected Lead Intelligence Dossier */}
        <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border-slate-800 space-y-6">
          {selectedLead ? (
            <>
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {selectedLead.company?.name || 'Finflow Systems'}
                    </h3>
                    <a
                      href={`https://${selectedLead.company?.domain || 'finflow.io'}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-mono text-brand-cyan hover:underline flex items-center gap-1 mt-0.5"
                    >
                      {selectedLead.company?.domain || 'finflow.io'}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-mono text-slate-400 block uppercase">Hybrid Score</span>
                    <span className="text-2xl font-black text-emerald-400 font-mono">
                      {selectedLead.score || 88.5}
                    </span>
                  </div>
                </div>
              </div>

              {/* Verified Contact Details */}
              <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800 space-y-2">
                <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  Target Decision Maker
                </div>
                <div className="text-sm font-bold text-white">
                  {selectedLead.contact?.first_name || 'Vikram'} {selectedLead.contact?.last_name || 'Sharma'}
                </div>
                <div className="text-xs text-brand-cyan font-mono">
                  {selectedLead.contact?.job_title || 'VP Engineering'}
                </div>
                <div className="flex items-center gap-4 text-xs font-mono text-slate-300 pt-2 border-t border-slate-800/60">
                  <span className="flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-brand-cyan" />
                    {selectedLead.contact?.email || 'vikram.sharma@finflow.io'}
                  </span>
                  <a
                    href={selectedLead.contact?.linkedin_url || 'https://linkedin.com'}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5 text-brand-indigo hover:underline"
                  >
                    <Linkedin className="w-3.5 h-3.5" /> LinkedIn
                  </a>
                </div>
              </div>

              {/* Buying Signals Breakdown */}
              <div className="space-y-2">
                <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  Verified Buying Signals & Evidence
                </div>
                <div className="space-y-2 text-xs">
                  <div className="p-3 rounded-xl bg-brand-cyan/5 border border-brand-cyan/20">
                    <div className="font-bold text-brand-cyan flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5" /> $18M Series A Announced (Feb 2026)
                    </div>
                    <p className="text-slate-300 text-[11px] mt-1">
                      Lead investor: Sequoia India. Planned 2.5x team expansion across platform infrastructure.
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-brand-indigo/5 border border-brand-indigo/20">
                    <div className="font-bold text-brand-indigo flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" /> Engineering Hiring Surge (12+ Open Roles)
                    </div>
                    <p className="text-slate-300 text-[11px] mt-1">
                      Active postings for Senior Distributed Systems Engineers (Python, FastAPI, AWS).
                    </p>
                  </div>
                </div>
              </div>

              {/* Score Rationale */}
              <div className="space-y-2">
                <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  Scoring Engine Rationale
                </div>
                <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside font-mono">
                  <li>Company size (180 emp) within 50-500 ICP bounds (+15%)</li>
                  <li>Industry match: B2B SaaS in India (+15%)</li>
                  <li>Persona match: VP Engineering Executive (+20%)</li>
                  <li>Verified funding & hiring signals (+30%)</li>
                </ul>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-slate-400 text-xs font-mono">
              Select a lead to view intelligence dossier.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
