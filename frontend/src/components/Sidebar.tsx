import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Target,
  Users,
  ShieldCheck,
  Cpu,
  BookOpen,
  Settings,
  Sparkles,
  Zap,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Executive Dashboard', icon: LayoutDashboard },
    { to: '/campaigns', label: 'Campaign Manager', icon: Target },
    { to: '/leads', label: 'Lead Intelligence', icon: Users },
    { to: '/approvals', label: 'Human Approvals', icon: ShieldCheck, badge: 'Active' },
    { to: '/traces', label: 'Live Agent Traces', icon: Cpu },
    { to: '/knowledge', label: 'RAG Knowledge Base', icon: BookOpen },
  ];

  return (
    <aside className="w-64 bg-dark-800/90 border-r border-slate-800/80 flex flex-col justify-between select-none z-20 backdrop-blur-xl">
      <div>
        {/* Brand Logo Header */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800/60 gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-cyan to-brand-indigo flex items-center justify-center shadow-glow-cyan">
            <Zap className="w-5 h-5 text-dark-900 fill-current" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Signal<span className="text-brand-cyan">OS</span>
            </span>
            <div className="text-[10px] uppercase font-mono tracking-widest text-brand-cyan/80">
              Autonomous GTM
            </div>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 font-mono">
            Platform Workflows
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-brand-cyan/15 to-brand-indigo/15 text-brand-cyan border border-brand-cyan/30 shadow-glow-cyan/50'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-dark-700/60'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/40">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Tenant Status Footer */}
      <div className="p-4 border-t border-slate-800/60">
        <div className="p-3 rounded-xl bg-dark-700/40 border border-slate-800 flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <div className="text-xs">
            <div className="font-semibold text-slate-200">Production Engine</div>
            <div className="text-slate-400 font-mono text-[10px]">LangGraph 2.0 • pgvector</div>
          </div>
        </div>
      </div>
    </aside>
  );
};
