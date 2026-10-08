import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  trendPositive?: boolean;
  colorScheme?: 'cyan' | 'indigo' | 'emerald' | 'amber' | 'violet';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendPositive = true,
  colorScheme = 'cyan',
}) => {
  const colorMap = {
    cyan: 'from-brand-cyan/20 to-brand-cyan/5 border-brand-cyan/30 text-brand-cyan',
    indigo: 'from-brand-indigo/20 to-brand-indigo/5 border-brand-indigo/30 text-brand-indigo',
    emerald: 'from-brand-emerald/20 to-brand-emerald/5 border-brand-emerald/30 text-brand-emerald',
    amber: 'from-brand-amber/20 to-brand-amber/5 border-brand-amber/30 text-brand-amber',
    violet: 'from-brand-violet/20 to-brand-violet/5 border-brand-violet/30 text-brand-violet',
  };

  return (
    <div className="glass-panel rounded-2xl p-5 relative overflow-hidden transition-all duration-200 hover:border-slate-700">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider">
            {title}
          </div>
          <div className="text-2xl font-extrabold text-white mt-1 tracking-tight">{value}</div>
        </div>
        <div
          className={`p-2.5 rounded-xl bg-gradient-to-br border ${colorMap[colorScheme]} flex items-center justify-center`}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs">
        {subtitle && <span className="text-slate-400 font-mono">{subtitle}</span>}
        {trend && (
          <span
            className={`font-mono font-semibold px-2 py-0.5 rounded-md ${
              trendPositive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
            }`}
          >
            {trend}
          </span>
        )}
      </div>
    </div>
  );
};
