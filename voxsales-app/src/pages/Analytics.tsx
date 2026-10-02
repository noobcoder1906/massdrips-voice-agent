import { useState, useEffect } from 'react';
import { Phone, Sparkles, MessageSquare, ChevronRight } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../components/Card';
import { StatusBadge } from '../components/Badge';
import Button from '../components/Button';
import { getRealCalls, type CallRecord } from '../data/realStore';

export default function Analytics() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null);

  useEffect(() => {
    setCalls(getRealCalls());
  }, []);

  const totalCalls = calls.length;
  const conversions = calls.filter(c => c.outcome === 'converted').length;
  const convRate = totalCalls > 0 ? ((conversions / totalCalls) * 100).toFixed(1) + '%' : '0.0%';
  const avgDurationSec = totalCalls > 0 ? Math.round(calls.reduce((acc, c) => acc + c.durationSec, 0) / totalCalls) : 0;
  const avgDuration = avgDurationSec > 0 ? `${Math.floor(avgDurationSec / 60)}m ${avgDurationSec % 60}s` : '0s';
  const avgScore = totalCalls > 0 ? Math.round(calls.reduce((acc, c) => acc + c.score, 0) / totalCalls) : 0;

  const sentimentCounts = {
    very_positive: calls.filter(c => c.sentiment === 'very_positive').length,
    positive: calls.filter(c => c.sentiment === 'positive').length,
    neutral: calls.filter(c => c.sentiment === 'neutral').length,
    negative: calls.filter(c => c.sentiment === 'negative' || c.sentiment === 'very_negative').length,
  };

  const sentimentData = [
    { name: 'Very Positive', count: sentimentCounts.very_positive, pct: totalCalls > 0 ? Math.round((sentimentCounts.very_positive / totalCalls) * 100) : 0, color: '#00e599' },
    { name: 'Positive', count: sentimentCounts.positive, pct: totalCalls > 0 ? Math.round((sentimentCounts.positive / totalCalls) * 100) : 0, color: '#34d399' },
    { name: 'Neutral', count: sentimentCounts.neutral, pct: totalCalls > 0 ? Math.round((sentimentCounts.neutral / totalCalls) * 100) : 0, color: '#6366f1' },
    { name: 'Negative', count: sentimentCounts.negative, pct: totalCalls > 0 ? Math.round((sentimentCounts.negative / totalCalls) * 100) : 0, color: '#f59e0b' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-white">Mass Drips Call Intelligence & Analytics</h1>
        <p className="text-xs text-white/50 mt-1">Real-time LLM post-call evaluations, sentiment distribution, and lead scoring.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Calls Analyzed', val: totalCalls.toString(), sub: `${conversions} high-intent buyers` },
          { label: 'Real Conversion Rate', val: convRate, sub: 'Based on actual dialogue' },
          { label: 'Avg Call Duration', val: avgDuration, sub: 'Real talk time' },
          { label: 'Avg Lead Score', val: `${avgScore}/100`, sub: totalCalls > 0 ? 'AI qualification' : 'No data yet' },
        ].map((kpi) => (
          <div key={kpi.label} className="p-5 rounded-2xl bg-white/5 border border-white/10">
            <p className="text-xs text-white/50 mb-1">{kpi.label}</p>
            <p className="text-2xl font-bold text-white">{kpi.val}</p>
            <p className="text-[11px] text-emerald-400 mt-1">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Main Breakdown */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Real Sentiment Breakdown */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Customer Sentiment</CardTitle>
          </CardHeader>
          <div className="space-y-3 pt-2">
            {sentimentData.map((s) => (
              <div key={s.name} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-white/70">{s.name} ({s.count})</span>
                  <span className="font-bold" style={{ color: s.color }}>{s.pct}%</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-500" style={{ width: `${s.pct}%`, background: s.color }} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-white/10">
            <p className="text-xs text-white/60">
              {totalCalls > 0 ? `Evaluated over ${totalCalls} processed customer sessions.` : 'No live call sessions completed yet.'}
            </p>
          </div>
        </Card>

        {/* Real Call Transcripts & Intelligence Logs */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Processed Call Records & Transcripts</CardTitle>
          </CardHeader>

          {calls.length === 0 ? (
            <div className="text-center py-12 px-4 space-y-3">
              <Phone size={24} className="mx-auto text-white/30" />
              <p className="text-sm font-semibold text-white">No calls processed yet</p>
              <p className="text-xs text-white/50 max-w-sm mx-auto">
                Launch a live voice call from the Dashboard or Discover page. Once completed, your real transcript, sentiment, and WhatsApp message will be recorded here.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
              {calls.map((call) => (
                <div
                  key={call.id}
                  onClick={() => setSelectedCall(call)}
                  className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-emerald-500/40 hover:bg-white/10 transition-all cursor-pointer flex items-center justify-between"
                >
                  <div className="space-y-1 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-bold text-white">{call.lead}</p>
                      <span className="text-xs text-white/40">({call.phone})</span>
                      <StatusBadge status={call.outcome} />
                    </div>
                    <p className="text-xs text-white/60 truncate">
                      {call.transcript.slice(0, 90)}...
                    </p>
                    <p className="text-[10px] text-emerald-400">
                      Duration: {call.duration} · Score: {call.score}/100 · {call.date}
                    </p>
                  </div>
                  <ChevronRight size={16} className="text-white/30 shrink-0 ml-2" />
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Selected Call Detail Modal */}
      {selectedCall && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#111116] border border-white/10 rounded-2xl p-6 max-w-xl w-full space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3 className="font-bold text-white text-base">{selectedCall.lead}</h3>
                <p className="text-xs text-white/50">{selectedCall.phone} · Score: {selectedCall.score}/100</p>
              </div>
              <StatusBadge status={selectedCall.outcome} />
            </div>

            <div className="space-y-2">
              <p className="text-xs font-semibold text-white flex items-center gap-1.5">
                <Sparkles size={13} className="text-emerald-400" /> Full Transcript
              </p>
              <div className="p-3.5 rounded-xl bg-black/50 border border-white/10 text-xs text-white/80 whitespace-pre-wrap max-h-48 overflow-y-auto">
                {selectedCall.transcript}
              </div>
            </div>

            {selectedCall.whatsappMessage && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <MessageSquare size={13} className="text-emerald-400" /> WhatsApp Follow-up Payload
                </p>
                <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/20 text-xs text-emerald-300">
                  {selectedCall.whatsappMessage}
                </div>
              </div>
            )}

            <Button variant="secondary" className="w-full" onClick={() => setSelectedCall(null)}>
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
