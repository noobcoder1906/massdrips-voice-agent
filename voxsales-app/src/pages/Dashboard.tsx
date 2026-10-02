import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Mic, Zap, Phone, Clock, Activity, CheckCircle, AlertTriangle, Info, Minus } from 'lucide-react';
import StatsCard from '../components/StatsCard';
import Card, { CardHeader, CardTitle } from '../components/Card';
import { StatusBadge } from '../components/Badge';
import Button from '../components/Button';
import { SkeletonCard } from '../components/Skeleton';
import { useToast } from '../components/Toast';
import { mockStats, mockCallLogs, mockActivity, mockCampaigns } from '../data/mockData';

// Simple inline bar chart (no external charting lib needed)
function MiniChart({ data }: { data: number[] }) {
  const max = Math.max(...data);
  return (
    <div className="flex items-end gap-0.5 h-10">
      {data.map((v, i) => (
        <div
          key={i}
          className="flex-1 rounded-sm transition-all duration-300 hover:opacity-80"
          style={{
            height: `${(v / max) * 100}%`,
            background: i === data.length - 1
              ? 'var(--color-accent)'
              : 'rgba(0,229,153,0.3)',
          }}
        />
      ))}
    </div>
  );
}

function ActivityIcon({ type }: { type: string }) {
  const map: Record<string, { icon: typeof CheckCircle; color: string }> = {
    call_completed: { icon: CheckCircle, color: '#00e599' },
    campaign_launched: { icon: Zap, color: '#6366f1' },
    lead_added: { icon: Activity, color: '#00e599' },
    call_failed: { icon: AlertTriangle, color: '#f59e0b' },
    webhook_triggered: { icon: Info, color: '#6366f1' },
    agent_updated: { icon: Minus, color: '#9090a8' },
  };
  const cfg = map[type] ?? { icon: Activity, color: '#9090a8' };
  const Icon = cfg.icon;
  return (
    <div
      className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
      style={{ background: `${cfg.color}20`, border: `1px solid ${cfg.color}40` }}
    >
      <Icon size={14} style={{ color: cfg.color }} />
    </div>
  );
}

export default function Dashboard() {
  const [loading] = useState(false);
  const [activeTab, setActiveTab] = useState<'calls' | 'campaigns'>('calls');
  const navigate = useNavigate();
  const { showToast } = useToast();

  const weekData = [420, 680, 920, 1240, 1560, 1890, 2120];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero Section */}
      <div
        className="relative rounded-2xl overflow-hidden p-6 lg:p-8"
        style={{
          background: 'linear-gradient(135deg, #0d2218 0%, #111118 50%, #0f0d1f 100%)',
          border: '1px solid var(--color-border)',
        }}
      >
        {/* Background glow orbs */}
        <div
          className="absolute -top-20 -right-20 w-64 h-64 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(0,229,153,0.08) 0%, transparent 70%)' }}
        />
        <div
          className="absolute -bottom-20 -left-10 w-48 h-48 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)' }}
        />

        <div className="relative flex flex-col lg:flex-row items-start lg:items-center gap-6">
          <div className="flex-1">
            <div
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold mb-3"
              style={{ background: 'var(--color-accent-muted)', color: 'var(--color-accent)', border: '1px solid var(--color-accent-border)' }}
            >
              <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--color-accent)' }} />
              AI Engine Online · 420ms avg latency
            </div>

            <h1
              className="text-2xl lg:text-3xl font-bold leading-tight mb-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-primary)' }}
            >
              Your AI sales team is{' '}
              <span style={{ color: 'var(--color-accent)' }}>crushing it today</span>
            </h1>
            <p className="text-sm max-w-md" style={{ color: 'var(--color-text-secondary)' }}>
              698 calls made · 32.4% conversion rate · ₹1.20 per call. Mass Drips AI is outperforming the industry average by 3×.
            </p>

            <div className="flex flex-wrap gap-3 mt-5">
              <Button
                variant="primary"
                size="lg"
                leftIcon={<Mic size={15} />}
                onClick={() => {
                  showToast('success', 'Call initiated!', 'Connecting to lead Ananya Roy...');
                }}
              >
                Start Voice Call
              </Button>
              <Button
                variant="secondary"
                size="lg"
                rightIcon={<ArrowRight size={15} />}
                onClick={() => navigate('/campaigns')}
              >
                View Campaigns
              </Button>
            </div>
          </div>

          {/* Right side — live stats mini-widget */}
          <div
            className="w-full lg:w-56 shrink-0 rounded-xl p-4 space-y-3"
            style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--color-border)' }}
          >
            <p className="text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>Weekly Calls</p>
            <MiniChart data={weekData} />
            <div className="flex items-center justify-between">
              <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>This week</p>
              <p className="text-xs font-bold" style={{ color: 'var(--color-accent)' }}>+18.4%</p>
            </div>
            <div className="pt-2" style={{ borderTop: '1px solid var(--color-border)' }}>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--color-accent)' }} />
                <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>3 active campaigns</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          : mockStats.map((stat, i) => (
              <StatsCard key={stat.label} {...stat} delay={i * 80} />
            ))
        }
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-4">
        {/* Recent Activity / Calls — takes 2 columns */}
        <div className="lg:col-span-2 space-y-4">
          {/* Tabs */}
          <div className="flex gap-1 p-1 rounded-xl w-fit" style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
            {(['calls', 'campaigns'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 capitalize"
                style={activeTab === tab
                  ? { background: 'var(--color-accent)', color: '#0a0a0f' }
                  : { color: 'var(--color-text-muted)' }
                }
              >
                {tab === 'calls' ? 'Recent Calls' : 'Campaigns'}
              </button>
            ))}
          </div>

          <Card>
            {activeTab === 'calls' ? (
              <div>
                <CardHeader>
                  <CardTitle>Call History</CardTitle>
                  <Button size="sm" variant="ghost" rightIcon={<ArrowRight size={12} />} onClick={() => navigate('/analytics')}>
                    View All
                  </Button>
                </CardHeader>
                <div className="space-y-0 -mx-5">
                  {mockCallLogs.slice(0, 5).map((call, i) => (
                    <div
                      key={call.id}
                      className="flex items-center gap-4 px-5 py-3 hover:bg-white/3 transition-colors cursor-pointer"
                      style={{ borderTop: i > 0 ? '1px solid var(--color-border)' : 'none' }}
                    >
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                        style={{ background: 'var(--color-accent-muted)', color: 'var(--color-accent)' }}
                      >
                        {call.lead.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>{call.lead}</p>
                        <p className="text-xs truncate" style={{ color: 'var(--color-text-muted)' }}>
                          <Clock size={10} className="inline mr-1" />{call.duration} · {call.date}
                        </p>
                      </div>
                      <StatusBadge status={call.outcome} />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                <CardHeader>
                  <CardTitle>Active Campaigns</CardTitle>
                  <Button size="sm" variant="ghost" rightIcon={<ArrowRight size={12} />} onClick={() => navigate('/campaigns')}>
                    Manage
                  </Button>
                </CardHeader>
                <div className="space-y-3">
                  {mockCampaigns.filter(c => c.status === 'active').map((campaign) => (
                    <div
                      key={campaign.id}
                      className="p-3 rounded-xl hover:bg-white/3 transition-colors"
                      style={{ border: '1px solid var(--color-border)' }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{campaign.name}</p>
                        <StatusBadge status={campaign.status} />
                      </div>
                      <div className="flex gap-4">
                        <div>
                          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Calls</p>
                          <p className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>{campaign.calls.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Conv.</p>
                          <p className="text-sm font-semibold" style={{ color: 'var(--color-accent)' }}>{campaign.successRate}%</p>
                        </div>
                        <div>
                          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Product</p>
                          <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>{campaign.product}</p>
                        </div>
                      </div>
                      {/* Progress bar */}
                      <div className="mt-2 h-1 rounded-full" style={{ background: 'var(--color-bg-elevated)' }}>
                        <div
                          className="h-1 rounded-full transition-all"
                          style={{
                            width: `${(campaign.calls / campaign.leads) * 100}%`,
                            background: 'var(--color-accent)',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Activity Feed */}
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Live Activity</CardTitle>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--color-accent)' }} />
              <span className="text-xs" style={{ color: 'var(--color-accent)' }}>Live</span>
            </div>
          </CardHeader>
          <div className="space-y-3 -mx-5 px-5">
            {mockActivity.map((item, i) => (
              <div
                key={item.id}
                className="flex gap-3 py-2 animate-fade-in-up"
                style={{ animationDelay: `${i * 60}ms`, borderTop: i > 0 ? '1px solid var(--color-border)' : 'none' }}
              >
                <ActivityIcon type={item.type} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs leading-snug" style={{ color: 'var(--color-text-secondary)' }}>{item.text}</p>
                  <p className="text-[10px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Bottom Row: Quick Actions + Sentiment */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <div className="grid grid-cols-2 gap-2">
            {[
              { icon: Mic, label: 'New Voice Call', color: '#00e599', action: () => showToast('info', 'Launching call simulator...') },
              { icon: Zap, label: 'Launch Campaign', color: '#6366f1', action: () => navigate('/campaigns') },
              { icon: Phone, label: 'Import Leads', color: '#f59e0b', action: () => showToast('success', '48 leads imported!', 'From Shopify export') },
              { icon: Activity, label: 'View Analytics', color: '#00e599', action: () => navigate('/analytics') },
            ].map(({ icon: Icon, label, color, action }) => (
              <button
                key={label}
                onClick={action}
                className="flex flex-col items-center gap-2 p-4 rounded-xl hover:bg-white/5 transition-all duration-150 hover:-translate-y-0.5 group"
                style={{ border: '1px solid var(--color-border)' }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform"
                  style={{ background: `${color}20` }}
                >
                  <Icon size={18} style={{ color }} />
                </div>
                <span className="text-xs font-medium text-center" style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Customer Sentiment</CardTitle>
            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Last 500 calls</span>
          </CardHeader>
          <div className="space-y-3">
            {[
              { label: 'Very Positive', pct: 38, color: '#00e599' },
              { label: 'Positive', pct: 32, color: '#34d399' },
              { label: 'Neutral', pct: 18, color: '#6366f1' },
              { label: 'Negative', pct: 9, color: '#f59e0b' },
              { label: 'Very Negative', pct: 3, color: '#ef4444' },
            ].map(({ label, pct, color }) => (
              <div key={label} className="flex items-center gap-3">
                <p className="text-xs w-24 shrink-0" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
                <div className="flex-1 h-1.5 rounded-full" style={{ background: 'var(--color-bg-elevated)' }}>
                  <div
                    className="h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, background: color }}
                  />
                </div>
                <p className="text-xs font-semibold w-8 text-right" style={{ color }}>{pct}%</p>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--color-border)' }}>
            <p className="text-xl font-bold" style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-display)' }}>
              78% Positive
            </p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
              Based on real-time LLM post-call evaluation
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
