import { TrendingUp, TrendingDown, Phone, Target, Clock, IndianRupee, Mic, Users, Activity, Zap } from 'lucide-react';

interface StatsCardProps {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  icon: string;
  delay?: number;
}

const iconMap: Record<string, React.ComponentType<{ size: number; className?: string }>> = {
  phone: Phone,
  target: Target,
  clock: Clock,
  rupee: IndianRupee,
  mic: Mic,
  users: Users,
  activity: Activity,
  zap: Zap,
};

export default function StatsCard({ label, value, change, trend, icon, delay = 0 }: StatsCardProps) {
  const Icon = iconMap[icon] || Activity;

  return (
    <div
      className="rounded-2xl p-5 animate-fade-in-up hover:-translate-y-0.5 transition-all duration-200 group"
      style={{
        animationDelay: `${delay}ms`,
        background: 'var(--color-bg-card)',
        border: '1px solid var(--color-border)',
      }}
    >
      <div className="flex items-start justify-between">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-200"
          style={{ background: 'var(--color-accent-muted)', border: '1px solid var(--color-accent-border)' }}
        >
          <Icon size={18} className="text-[#00e599]" />
        </div>
        <span
          className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
            trend === 'up' ? 'text-[#00e599]' : trend === 'down' ? 'text-[#ef4444]' : 'text-[#9090a8]'
          }`}
          style={{
            background: trend === 'up' ? 'rgba(0,229,153,0.12)' : trend === 'down' ? 'rgba(239,68,68,0.12)' : 'rgba(144,144,168,0.1)',
          }}
        >
          {trend === 'up' ? <TrendingUp size={11} /> : trend === 'down' ? <TrendingDown size={11} /> : null}
          {change}
        </span>
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}>
          {value}
        </p>
        <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
      </div>
    </div>
  );
}
