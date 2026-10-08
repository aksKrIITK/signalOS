import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Zap,
  Mail,
  Send,
  AlertTriangle,
  FileCheck,
} from 'lucide-react';
import { api } from '../lib/api';
import { AgentRun } from '../types';

export const ApprovalsPage: React.FC = () => {
  const [pendingRuns, setPendingRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [editedSubject, setEditedSubject] = useState<string>('');
  const [editedBody, setEditedBody] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  const loadApprovals = async () => {
    try {
      const data = await api.getPendingApprovals();
      setPendingRuns(data);
      if (data.length > 0) {
        setSelectedRun(data[0]);
        setEditedSubject(data[0].output_json?.email_subject || '');
        setEditedBody(data[0].output_json?.email_body || '');
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleSelect = (run: AgentRun) => {
    setSelectedRun(run);
    setEditedSubject(run.output_json?.email_subject || '');
    setEditedBody(run.output_json?.email_body || '');
  };

  const handleApprove = async () => {
    if (!selectedRun) return;
    setSubmitting(true);
    try {
      await api.approveAction(selectedRun.id, editedSubject, editedBody);
      alert('Action Approved and Email Dispatched via Idempotent Executor!');
      loadApprovals();
    } catch (e) {
      alert('Error approving action');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!selectedRun) return;
    setSubmitting(true);
    try {
      await api.rejectAction(selectedRun.id, 'Draft did not meet tone standards.');
      alert('Action Rejected.');
      loadApprovals();
    } catch (e) {
      alert('Error rejecting action');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-brand-cyan" />
            Human-in-the-Loop Approvals
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Review, edit, and authorize agent-generated outreach before side-effect execution
          </p>
        </div>

        <div className="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-xs flex items-center gap-2">
          <Clock className="w-4 h-4" />
          <span>{pendingRuns.length} Pending Actions</span>
        </div>
      </div>

      {pendingRuns.length === 0 ? (
        <div className="glass-panel p-16 rounded-3xl text-center space-y-3">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <div className="text-base font-bold text-white">All Caught Up!</div>
          <p className="text-xs text-slate-400 font-mono">
            No pending agent actions require human approval right now.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Pending Queue List */}
          <div className="lg:col-span-4 space-y-3">
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
              Pending Queue
            </div>
            {pendingRuns.map((r) => (
              <div
                key={r.id}
                onClick={() => handleSelect(r)}
                className={`glass-panel p-4 rounded-2xl border-slate-800 cursor-pointer transition-all ${
                  selectedRun?.id === r.id ? 'border-brand-cyan bg-brand-cyan/10' : 'hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white">Finflow Systems</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 font-semibold">
                    WAITING
                  </span>
                </div>
                <div className="text-xs text-slate-400 truncate">
                  To: Vikram Sharma (VP Engineering)
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-2">
                  GTM Lead Score: <span className="text-emerald-400 font-bold">88.5</span>
                </div>
              </div>
            ))}
          </div>

          {/* Action Approval Editor */}
          <div className="lg:col-span-8 glass-panel p-6 rounded-2xl border-slate-800 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-brand-cyan" />
                <h3 className="font-bold text-white text-base">Cold Outreach Draft & Evidence Review</h3>
              </div>
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <FileCheck className="w-3.5 h-3.5" /> Critic Grounded (No Hallucination)
              </span>
            </div>

            {/* Email Editor Form */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Subject Line</label>
                <input
                  type="text"
                  value={editedSubject}
                  onChange={(e) => setEditedSubject(e.target.value)}
                  className="w-full p-3 rounded-xl glass-input text-xs font-semibold text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Email Body (Markdown / Text)</label>
                <textarea
                  rows={8}
                  value={editedBody}
                  onChange={(e) => setEditedBody(e.target.value)}
                  className="w-full p-3 rounded-xl glass-input text-xs font-mono leading-relaxed"
                />
              </div>

              {/* Verified Evidence Claims Cited */}
              <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800 space-y-2">
                <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                  Grounding Evidence Citations
                </div>
                <div className="space-y-1.5 text-xs font-mono text-slate-300">
                  <div className="flex items-center gap-2 text-brand-cyan">
                    <span>[1]</span>
                    <span>$18M Series A round led by Sequoia India (TechCrunch, Feb 2026)</span>
                  </div>
                  <div className="flex items-center gap-2 text-brand-indigo">
                    <span>[2]</span>
                    <span>12+ open roles for Senior Backend Engineers / Distributed Systems (Finflow Careers)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <button
                onClick={handleReject}
                disabled={submitting}
                className="px-5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-mono font-semibold flex items-center gap-2 transition-all"
              >
                <XCircle className="w-4 h-4" /> Reject Draft
              </button>

              <button
                onClick={handleApprove}
                disabled={submitting}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-indigo hover:opacity-95 text-dark-900 font-bold text-xs font-mono flex items-center gap-2 transition-all shadow-glow-cyan"
              >
                <Send className="w-4 h-4" /> Authorize & Send Email
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
