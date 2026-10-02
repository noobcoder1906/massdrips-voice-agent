import React, { useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../components/Card';
import { mockChartData, mockSentimentData, mockCallLogs } from '../data/mockData';
import { StatusBadge } from '../components/Badge';

function BarGroup({ data, maxVal, label, valueKey, color }: {
  data: typeof mockChartData;
  maxVal: number;
  label: string;
  valueKey: keyof typeof mockChartData[0];
  color: string;
}) {
  return (
    <div className="flex flex-col gap-1 flex-1">
      <p className="text-[10px] font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
      <div className="flex items-end gap-1 h-32">
        {data.map((d, i) => {
          const val = d[valueKey] as number;
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
              <div
                className="w-full rounded-t-sm transition-all duration-300 hover:opacity-80 cursor-pointer"
                style={{ height: `${(val / maxVal) * 100}%`, background: color }}
                title={`${d.month}: ${val.toLocaleString()}`}
              />
              <span className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>{d.month}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function KpiCard({ label, value, change, trend, sub }: {
  label: string; value: string; change: string; trend: 'up' | 'down'; sub: string;
}) {
  return (
    <div className="rounded-2xl p-5" style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
      <p className="text-xs mb-2" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
      <div className="flex items-end justify-between">
        <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}>{value}</p>
        <span
          className="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full"
          style={{
            color: trend === 'up' ? '#00e599' : '#ef4444',
            background: trend === 'up' ? 'rgba(0,229,153,0.12)' : 'rgba(239,68,68,0.12)',
          }}
        >
          {trend === 'up' ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
          {change}
        </span>
      </div>
      <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>{sub}</p>
    </div>
  );
}

export default function Analytics() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');
  const maxCalls = Math.max(...mockChartData.map(d => d.calls));
  const maxConv = Math.max(...mockChartData.map(d => d.conversions));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Period selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-primary)' }}>
          Performance Overview
        </h2>
        <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
          {(['7d', '30d', '90d'] as const).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={period === p
                ? { background: 'var(--color-accent)', color: '#0a0a0f' }
                : { color: 'var(--color-text-muted)' }
              }
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total Calls" value="12,847" change="+18.4%" trend="up" sub="vs prev period" />
        <KpiCard label="Conversions" value="4,163" change="+12.7%" trend="up" sub="Total converted leads" />
        <KpiCard label="Revenue Generated" value="₹78.6L" change="+22.1%" trend="up" sub="Estimated from calls" />
        <KpiCard label="Avg Handle Time" value="1m 45s" change="-8s" trend="up" sub="Lower is better" />
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-5 gap-4">
        {/* Bar Charts — 3 cols */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Calls & Conversions by Month</CardTitle>
          </CardHeader>
          <div className="flex gap-6">
            <BarGroup data={mockChartData} maxVal={maxCalls} label="Total Calls" valueKey="calls" color="rgba(0,229,153,0.6)" />
            <BarGroup data={mockChartData} maxVal={maxConv} label="Conversions" valueKey="conversions" color="#00e599" />
          </div>
          <div className="flex items-center gap-4 mt-4 pt-4" style={{ borderTop: '1px solid var(--color-border)' }}>
            <div className="flex items-center gap-2">
              <div className="w-3 h-2 rounded-sm" style={{ background: 'rgba(0,229,153,0.6)' }} />
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Total Calls</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-2 rounded-sm" style={{ background: '#00e599' }} />
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Conversions</span>
            </div>
          </div>
        </Card>

        {/* Sentiment Donut — 2 cols */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Sentiment Breakdown</CardTitle>
          </CardHeader>
          {/* Custom donut using CSS */}
          <div className="flex items-center justify-center mb-4">
            <div className="relative w-28 h-28">
              <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                {mockSentimentData.reduce<{ elements: React.ReactNode[]; offset: number }>(
                  ({ elements, offset }, seg) => {
                    const el = (
                      <circle
                        key={seg.name}
                        cx="18" cy="18" r="15.9"
                        fill="none"
                        stroke={seg.color}
                        strokeWidth="3.5"
                        strokeDasharray={`${seg.value} ${100 - seg.value}`}
                        strokeDashoffset={-offset}
                      />
                    );
                    return { elements: [...elements, el], offset: offset + seg.value };
                  },
                  { elements: [], offset: 0 }
                ).elements}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-lg font-bold" style={{ color: '#00e599' }}>78%</p>
                <p className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>Positive</p>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            {mockSentimentData.map(seg => (
              <div key={seg.name} className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: seg.color }} />
                <p className="text-xs flex-1" style={{ color: 'var(--color-text-secondary)' }}>{seg.name}</p>
                <p className="text-xs font-semibold" style={{ color: seg.color }}>{seg.value}%</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Revenue Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Trend (₹)</CardTitle>
          <span className="text-xs font-semibold" style={{ color: 'var(--color-accent)' }}>
            +22.1% overall growth
          </span>
        </CardHeader>
        <div className="relative h-20">
          <svg viewBox={`0 0 ${mockChartData.length * 60} 80`} className="w-full h-full" preserveAspectRatio="none">
            {(() => {
              const max = Math.max(...mockChartData.map(d => d.revenue));
              const points = mockChartData.map((d, i) => `${i * 60 + 30},${80 - (d.revenue / max) * 72}`).join(' ');
              const areaPoints = `30,80 ${points} ${(mockChartData.length - 1) * 60 + 30},80`;
              return (
                <>
                  <defs>
                    <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#00e599" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#00e599" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <polygon points={areaPoints} fill="url(#revGrad)" />
                  <polyline points={points} fill="none" stroke="#00e599" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  {mockChartData.map((d, i) => (
                    <circle
                      key={i}
                      cx={i * 60 + 30}
                      cy={80 - (d.revenue / max) * 72}
                      r="3"
                      fill="#00e599"
                    />
                  ))}
                </>
              );
            })()}
          </svg>
        </div>
        <div className="flex justify-between mt-2">
          {mockChartData.map(d => (
            <div key={d.month} className="text-center">
              <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{d.month}</p>
              <p className="text-[10px] font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                ₹{(d.revenue / 100000).toFixed(1)}L
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Call Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Call Transcripts</CardTitle>
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Showing last 6 calls</span>
        </CardHeader>
        <div className="overflow-x-auto -mx-5">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {['Call ID', 'Lead', 'Duration', 'Outcome', 'Sentiment', 'Score', 'Date'].map(h => (
                  <th key={h} className="text-left px-5 pb-3 text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {mockCallLogs.map((call, i) => (
                <tr
                  key={call.id}
                  className="hover:bg-white/3 transition-colors animate-fade-in-up"
                  style={{ borderBottom: '1px solid var(--color-border)', animationDelay: `${i * 50}ms` }}
                >
                  <td className="px-5 py-3 text-xs font-mono" style={{ color: 'var(--color-text-muted)' }}>{call.id}</td>
                  <td className="px-5 py-3 text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{call.lead}</td>
                  <td className="px-5 py-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{call.duration}</td>
                  <td className="px-5 py-3"><StatusBadge status={call.outcome} /></td>
                  <td className="px-5 py-3"><StatusBadge status={call.sentiment} /></td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-bold" style={{ color: call.score >= 80 ? '#00e599' : call.score >= 50 ? '#f59e0b' : '#ef4444' }}>
                      {call.score}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-xs" style={{ color: 'var(--color-text-muted)' }}>{call.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
