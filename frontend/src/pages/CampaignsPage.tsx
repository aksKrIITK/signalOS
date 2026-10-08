import React, { useEffect, useState } from 'react';
import {
  Target,
  Plus,
  Play,
  Pause,
  Clock,
  Sparkles,
  Search,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../lib/api';
import { Campaign } from '../types';

export const CampaignsPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);

  // New Campaign Form State
  const [name, setName] = useState('Indian B2B SaaS CTOs — Post-Funding');
  const [description, setDescription] = useState(
    'Find SaaS companies in India with 50-500 employees that recently raised funding, identify CTOs, research tech stack, and generate personalized outreach.'
  );
  const [industry, setIndustry] = useState('B2B SaaS');
  const [location, setLocation] = useState('India');
  const [minEmp, setMinEmp] = useState(50);
  const [maxEmp, setMaxEmp] = useState(500);
  const [personas, setPersonas] = useState('CTO, VP Engineering, Head of Engineering');
  const [signals, setSignals] = useState('recent funding, hiring engineers, technology migration');

  const loadCampaigns = async () => {
    try {
      const data = await api.getCampaigns();
      setCampaigns(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCampaign({
        name,
        description,
        icp_definition: {
          industry,
          location,
          min_employees: Number(minEmp),
          max_employees: Number(maxEmp),
          target_personas: personas.split(',').map((p) => p.trim()),
        },
        signal_definition: {
          required_signals: signals.split(',').map((s) => s.trim()),
        },
      });
      setShowModal(false);
      loadCampaigns();
    } catch (err) {
      alert('Error creating campaign');
    }
  };

  const handleTriggerRun = async (id: string) => {
    setRunningId(id);
    try {
      await api.runCampaign(id);
      setTimeout(() => {
        loadCampaigns();
        setRunningId(null);
      }, 1500);
    } catch (e) {
      setRunningId(null);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <Target className="w-6 h-6 text-brand-cyan" />
            Campaign Manager
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Configure agentic ICP targets, signal triggers, and batch lead discovery workflows
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-indigo text-dark-900 font-bold text-xs font-mono flex items-center gap-2 hover:opacity-95 transition-all shadow-glow-cyan"
        >
          <Plus className="w-4 h-4" />
          Create GTM Campaign
        </button>
      </div>

      {/* Campaigns List */}
      <div className="space-y-4">
        {campaigns.length === 0 ? (
          <div className="glass-panel p-12 rounded-3xl text-center space-y-3">
            <Target className="w-10 h-10 text-slate-500 mx-auto" />
            <div className="text-sm font-bold text-white">No campaigns found</div>
            <p className="text-xs text-slate-400 font-mono">
              Click &quot;Create GTM Campaign&quot; to initiate your first autonomous lead research pipeline.
            </p>
          </div>
        ) : (
          campaigns.map((camp) => (
            <div
              key={camp.id}
              className="glass-panel p-6 rounded-2xl border-slate-800 hover:border-slate-700 transition-all space-y-4"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-bold text-white">{camp.name}</h3>
                    <span className="px-2.5 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      {camp.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl">{camp.description}</p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleTriggerRun(camp.id)}
                    disabled={runningId === camp.id}
                    className="px-4 py-2 rounded-xl bg-dark-700 hover:bg-dark-600 text-brand-cyan font-mono text-xs font-semibold border border-brand-cyan/30 flex items-center gap-2 transition-all"
                  >
                    {runningId === camp.id ? (
                      <Clock className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5 fill-current" />
                    )}
                    {runningId === camp.id ? 'Queuing Batch...' : 'Run Agent Batch'}
                  </button>
                </div>
              </div>

              {/* ICP & Signal Tags */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-slate-800/80 text-xs font-mono">
                <div className="p-3 rounded-xl bg-dark-900/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] block uppercase">Target Industry</span>
                  <span className="text-slate-200 font-semibold">{camp.icp_definition?.industry || 'B2B SaaS'}</span>
                </div>
                <div className="p-3 rounded-xl bg-dark-900/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] block uppercase">Geography & Size</span>
                  <span className="text-slate-200 font-semibold">
                    {camp.icp_definition?.location || 'India'} ({camp.icp_definition?.min_employees || 50}-
                    {camp.icp_definition?.max_employees || 500} emp)
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-dark-900/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] block uppercase">Personas</span>
                  <span className="text-slate-200 font-semibold truncate block">
                    {(camp.icp_definition?.target_personas || ['CTO', 'VP Engineering']).join(', ')}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-dark-900/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] block uppercase">Monitored Signals</span>
                  <span className="text-brand-cyan font-semibold truncate block">
                    {(camp.signal_definition?.required_signals || ['recent funding', 'hiring']).join(', ')}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Campaign Modal Wizard */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel w-full max-w-2xl rounded-2xl overflow-hidden border border-slate-700 shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-dark-800">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <Target className="w-4 h-4 text-brand-cyan" />
                Configure New GTM Campaign
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Campaign Title</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full p-2.5 rounded-xl glass-input text-xs font-medium"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Campaign Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full p-2.5 rounded-xl glass-input text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Industry</label>
                  <input
                    type="text"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full p-2.5 rounded-xl glass-input text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Geography</label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full p-2.5 rounded-xl glass-input text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Min Employees</label>
                  <input
                    type="number"
                    value={minEmp}
                    onChange={(e) => setMinEmp(Number(e.target.value))}
                    className="w-full p-2.5 rounded-xl glass-input text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Max Employees</label>
                  <input
                    type="number"
                    value={maxEmp}
                    onChange={(e) => setMaxEmp(Number(e.target.value))}
                    className="w-full p-2.5 rounded-xl glass-input text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Target Personas (comma-separated)</label>
                <input
                  type="text"
                  value={personas}
                  onChange={(e) => setPersonas(e.target.value)}
                  className="w-full p-2.5 rounded-xl glass-input text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Buying Signals to Detect</label>
                <input
                  type="text"
                  value={signals}
                  onChange={(e) => setSignals(e.target.value)}
                  className="w-full p-2.5 rounded-xl glass-input text-xs"
                />
              </div>

              <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-dark-700 text-slate-300 font-mono text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-indigo text-dark-900 font-bold font-mono text-xs shadow-glow-cyan"
                >
                  Save & Launch Campaign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
