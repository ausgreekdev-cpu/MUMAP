import { ReactNode } from 'react';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: ReactNode;
  trend?: { value: number; isPositive: boolean };
  color?: 'indigo' | 'green' | 'amber' | 'purple' | 'red' | 'blue';
  children?: ReactNode;
}

export function StatsCard({ title, value, icon, trend, color = 'indigo', children }: StatsCardProps) {
  const colorClasses = {
    indigo: 'from-indigo-500/20 to-indigo-600/20 text-indigo-400',
    green: 'from-emerald-500/20 to-emerald-600/20 text-emerald-400',
    amber: 'from-amber-500/20 to-amber-600/20 text-amber-400',
    purple: 'from-purple-500/20 to-purple-600/20 text-purple-400',
    red: 'from-red-500/20 to-red-600/20 text-red-400',
    blue: 'from-blue-500/20 to-blue-600/20 text-blue-400',
  };

  return (
    <div className="card group hover:border-indigo-500/30 transition-all duration-300 animate-fadeIn">
      <div className="flex items-start justify-between">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center group-hover:scale-110 transition-transform`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm font-medium ${trend.isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
            <svg className={`w-4 h-4 ${!trend.isPositive ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
            </svg>
            {Math.abs(trend.value)}%
          </div>
        )}
      </div>
      
      <div className="mt-4">
        <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
        <p className="text-3xl font-bold mt-1">{value}</p>
      </div>
      
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}
