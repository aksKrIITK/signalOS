import React from 'react';
import { Search, Bell, Shield, Sparkles, User as UserIcon } from 'lucide-react';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  return (
    <header className="h-16 border-b border-slate-800/80 bg-dark-900/60 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        {title && <h1 className="text-xl font-bold tracking-tight text-white">{title}</h1>}
        {subtitle && <p className="text-xs text-slate-400 font-mono mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search accounts, contacts, signals..."
            className="pl-9 pr-4 py-1.5 rounded-lg glass-input text-xs w-64 focus:w-80 transition-all font-mono"
          />
        </div>

        {/* Tenant Organization Badge */}
        <div className="px-3 py-1.5 rounded-lg bg-brand-indigo/15 border border-brand-indigo/30 flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-brand-indigo" />
          <span className="text-xs font-semibold text-brand-indigo">Acme HyperGrowth SaaS</span>
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-violet to-brand-cyan flex items-center justify-center font-bold text-xs text-dark-900">
            AM
          </div>
          <div className="text-left hidden md:block">
            <div className="text-xs font-semibold text-slate-200">Alex Mercer</div>
            <div className="text-[10px] text-slate-400 font-mono">GTM Lead (Owner)</div>
          </div>
        </div>
      </div>
    </header>
  );
};
