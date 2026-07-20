interface BarChartProps {
  data: { label: string; value: number; color?: string }[];
  maxValue?: number;
}

export function BarChart({ data, maxValue }: BarChartProps) {
  const max = maxValue || Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="flex items-end gap-2 h-32">
      {data.map((item, i) => {
        const height = Math.max((item.value / max) * 100, 4);
        
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-2">
            <span className="text-xs text-gray-400 font-medium">{item.value}</span>
            <div className="w-full relative" style={{ height: '80px' }}>
              <div
                className="chart-bar absolute bottom-0 w-full transition-all duration-500"
                style={{ 
                  height: `${height}%`,
                  background: item.color || 'var(--accent-gradient)',
                }}
              />
            </div>
            <span className="text-[10px] text-gray-500 truncate w-full text-center">{item.label}</span>
          </div>
        );
      })}
    </div>
  );
}

interface DonutChartProps {
  value: number;
  max: number;
  color?: string;
  size?: number;
}

export function DonutChart({ value, max, color = '#6366f1', size = 120 }: DonutChartProps) {
  const percentage = max > 0 ? (value / max) * 100 : 0;
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx="50%"
          cy="50%"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="8"
        />
        {/* Progress circle */}
        <circle
          cx="50%"
          cy="50%"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold">{Math.round(percentage)}%</span>
        <span className="text-xs text-gray-400">{value}/{max}</span>
      </div>
    </div>
  );
}

interface ActivityItem {
  icon: React.ReactNode;
  title: string;
  description: string;
  time: string;
  color: string;
}

interface ActivityFeedProps {
  items: ActivityItem[];
}

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <div className="space-y-4">
      {items.map((item, i) => (
        <div key={i} className="flex items-start gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${item.color}`}>
            {item.icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{item.title}</p>
            <p className="text-xs text-gray-400 truncate">{item.description}</p>
          </div>
          <span className="text-xs text-gray-500 flex-shrink-0">{item.time}</span>
        </div>
      ))}
    </div>
  );
}
