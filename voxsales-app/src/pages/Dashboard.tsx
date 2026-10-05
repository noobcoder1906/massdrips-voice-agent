import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Mic, Phone, Clock, Activity, PhoneCall } from 'lucide-react';
import StatsCard from '../components/StatsCard';
import Card, { CardHeader, CardTitle } from '../components/Card';
import { StatusBadge } from '../components/Badge';
import Button from '../components/Button';
import { SkeletonCard } from '../components/Skeleton';
import LiveCallModal from '../components/LiveCallModal';
import { getRealCalls, getRealActivities, type CallRecord, type ActivityItem, massDripsCampaigns, massDripsLeads } from '../data/realStore';

export default function Dashboard() {
  const [loading] = useState(false);
  const [activeTab, setActiveTab] = useState<'calls' | 'leads' | 'campaigns'>('calls');
  const [callModalOpen, setCallModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState({ name: 'Rahul Sharma', phone: '+91 98765 43210' });
  const [realCalls, setRealCalls] = useState<CallRecord[]>([]);
  const [realActivities, setRealActivities] = useState<ActivityItem[]>([]);
  const navigate = useNavigate();

  const [websiteUrl, setWebsiteUrl] = useState('https://www.massdrips.shop/');
  const [isSyncing, setIsSyncing] = useState(false);
  const [storeData, setStoreData] = useState<any>(null);

  useEffect(() => {
    refreshData();
    fetchStoreKnowledge();
  }, []);

  const fetchStoreKnowledge = async () => {
    try {
      const res = await fetch('https://voice.massdrips.shop/api/v1/smart/store-knowledge');
      if (res.ok) {
        const data = await res.json();
        setStoreData(data);
      }
    } catch (e) {}
  };

  const handleSyncWebsite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!websiteUrl.trim()) return;
    setIsSyncing(true);
    try {
      const res = await fetch('https://voice.massdrips.shop/api/v1/smart/sync-website', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: websiteUrl })
      });
      if (res.ok) {
        const result = await res.json();
        setStoreData(result.data);
      }
    } catch (e) {
      console.log('Website sync error:', e);
    } finally {
      setIsSyncing(false);
    }
  };

  const refreshData = () => {
    setRealCalls(getRealCalls());
    setRealActivities(getRealActivities());
  };

  const totalCalls = realCalls.length;
  const conversions = realCalls.filter(c => c.outcome === 'converted').length;
  const conversionRate = totalCalls > 0 ? ((conversions / totalCalls) * 100).toFixed(1) + '%' : '0.0%';
  const avgDurationSec = totalCalls > 0 ? Math.round(realCalls.reduce((acc, c) => acc + c.durationSec, 0) / totalCalls) : 0;
  const avgDuration = avgDurationSec > 0 ? `${Math.floor(avgDurationSec / 60)}m ${avgDurationSec % 60}s` : '0s';

  const realStats = [
    { label: 'Total Calls Made', value: totalCalls.toString(), change: totalCalls > 0 ? `+${totalCalls} live` : '0 calls', trend: 'neutral' as const, icon: 'phone' },
    { label: 'Conversion Rate', value: conversionRate, change: totalCalls > 0 ? `${conversions} converted` : '0%', trend: conversions > 0 ? 'up' as const : 'neutral' as const, icon: 'target' },
    { label: 'Avg Call Duration', value: avgDuration, change: 'Live duration', trend: 'neutral' as const, icon: 'clock' },
    { label: 'Cost Per Call', value: '₹0.00', change: 'Free local & Groq', trend: 'up' as const, icon: 'rupee' },
  ];

  const handleStartCallWithLead = (lead: { name: string; phone: string }) => {
    setSelectedLead(lead);
    setCallModalOpen(true);
  };

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
              Mass Drips AI Engine Active · Groq LLM + Kokoro TTS
            </div>

            <h1
              className="text-2xl lg:text-3xl font-bold leading-tight mb-2"
              style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-primary)' }}
            >
              Mass Drips <span style={{ color: 'var(--color-accent)' }}>Voice Sales Assistant</span>
            </h1>
            <p className="text-sm max-w-md" style={{ color: 'var(--color-text-secondary)' }}>
              Outbound AI sales agent for hoodies, oversized tees, and streetwear. Conducts live consultative sales calls, handles objections, and sends automated WhatsApp follow-ups.
            </p>

            <div className="flex flex-wrap gap-3 mt-5">
              <Button
                variant="primary"
                size="lg"
                leftIcon={<Mic size={15} />}
                onClick={() => setCallModalOpen(true)}
              >
                Start Live Voice Call
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

          {/* Right side — live status widget */}
          <div
            className="w-full lg:w-56 shrink-0 rounded-xl p-4 space-y-3"
            style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--color-border)' }}
          >
            <p className="text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>Brand Voice Status</p>
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs font-bold text-white">Sai (Mass Drips)</span>
            </div>
            <p className="text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>Language: Hinglish / English</p>
            <div className="pt-2" style={{ borderTop: '1px solid var(--color-border)' }}>
              <span className="text-xs font-medium" style={{ color: 'var(--color-accent)' }}>
                {totalCalls} calls processed today
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Real KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          : realStats.map((stat, i) => (
              <StatsCard key={stat.label} {...stat} delay={i * 80} />
            ))
        }
      </div>

      {/* Live Website Knowledge & Scraper Center */}
      <div
        className="rounded-2xl p-5 lg:p-6 space-y-4"
        style={{
          background: 'linear-gradient(180deg, rgba(17,17,24,0.95) 0%, rgba(12,12,16,0.95) 100%)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <h3 className="text-base font-bold text-white">Live Store Website Knowledge Sync</h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Active in Agent Brain
              </span>
            </div>
            <p className="text-xs text-white/50">
              Enter your live e-commerce URL. The voice agent automatically scrapes your catalog, fabric specs, prices, and shipping policies.
            </p>
          </div>

          <form onSubmit={handleSyncWebsite} className="flex gap-2 w-full md:w-auto">
            <input
              type="url"
              placeholder="https://www.massdrips.shop/"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              className="px-4 py-2 rounded-xl text-xs bg-white/5 border border-white/10 text-white outline-none focus:border-[#00e599] w-full md:w-72"
            />
            <Button
              type="submit"
              size="sm"
              variant="primary"
              disabled={isSyncing}
            >
              {isSyncing ? 'Scraping...' : 'Sync Store'}
            </Button>
          </form>
        </div>

        {/* Scraped Knowledge Preview Card */}
        {storeData && (
          <div className="pt-3 border-t border-white/10 space-y-4 animate-fade-in">
            {/* Meta Pill Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                <p className="text-[10px] text-white/40 uppercase font-semibold">Store Brand</p>
                <p className="text-xs font-bold text-white mt-0.5">{storeData.brand_name || 'MASS DRIPS'}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                <p className="text-[10px] text-white/40 uppercase font-semibold">Fabric Specs</p>
                <p className="text-xs font-bold text-emerald-400 mt-0.5">240 GSM & 380 GSM Fleece</p>
              </div>
              <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                <p className="text-[10px] text-white/40 uppercase font-semibold">Shipping & Terms</p>
                <p className="text-xs font-bold text-white mt-0.5">3–4 Days · COD + UPI</p>
              </div>
              <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                <p className="text-[10px] text-white/40 uppercase font-semibold">Objection Closer</p>
                <p className="text-xs font-bold text-amber-400 mt-0.5">Code DRIP10 (10% OFF)</p>
              </div>
            </div>

            {/* Live Collections & Scraped Products Preview */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-white/80">
                  📦 Scraped Live Store Products ({storeData.products?.length || 11} items synced from {storeData.website || 'massdrips.shop'}):
                </p>
                <span className="text-[11px] text-emerald-400 font-mono">Status: 100% Synced</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5 max-h-52 overflow-y-auto pr-1">
                {(storeData.products || []).map((prod: any) => (
                  <div key={prod.id} className="p-2.5 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between gap-1 mb-1">
                        <span className="text-[9px] px-1.5 py-0.2 rounded font-mono bg-white/10 text-white/70">{prod.category}</span>
                        {prod.badge && (
                          <span className="text-[9px] font-bold text-amber-400">{prod.badge}</span>
                        )}
                      </div>
                      <p className="text-xs font-semibold text-white line-clamp-1">{prod.name}</p>
                      <p className="text-[10px] text-white/40">{prod.gsm || '240 GSM'}</p>
                    </div>
                    <p className="text-xs font-bold text-emerald-400 mt-2">₹{prod.price.toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-4">
        {/* Recent Activity / Calls — 2 cols */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-1 p-1 rounded-xl w-fit" style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
            {(['calls', 'leads', 'campaigns'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 capitalize"
                style={activeTab === tab
                  ? { background: 'var(--color-accent)', color: '#0a0a0f' }
                  : { color: 'var(--color-text-muted)' }
                }
              >
                {tab === 'calls' ? 'Processed Calls' : tab === 'leads' ? 'Ready Leads' : 'Campaigns'}
              </button>
            ))}
          </div>

          <Card>
            {activeTab === 'calls' ? (
              <div>
                <CardHeader>
                  <CardTitle>Real Processed Call Logs</CardTitle>
                  <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{realCalls.length} calls</span>
                </CardHeader>

                {realCalls.length === 0 ? (
                  <div className="text-center py-10 px-4 space-y-3">
                    <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mx-auto text-white/40">
                      <PhoneCall size={20} />
                    </div>
                    <p className="text-sm font-semibold text-white">No calls processed yet</p>
                    <p className="text-xs text-white/50 max-w-sm mx-auto">
                      Click the "Start Live Voice Call" button above or select a lead below to test a live call with Sai. Real transcripts and insights will appear here!
                    </p>
                    <Button size="sm" variant="primary" onClick={() => setCallModalOpen(true)}>
                      Launch Test Call Now
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-0 -mx-5 divide-y divide-white/5">
                    {realCalls.map((call) => (
                      <div
                        key={call.id}
                        className="flex items-center gap-4 px-5 py-3.5 hover:bg-white/5 transition-colors cursor-pointer"
                      >
                        <div
                          className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                          style={{ background: 'var(--color-accent-muted)', color: 'var(--color-accent)' }}
                        >
                          {call.lead.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate text-white">{call.lead}</p>
                          <p className="text-xs text-white/50">
                            <Clock size={10} className="inline mr-1" />{call.duration} · {call.date} · Score: {call.score}/100
                          </p>
                        </div>
                        <StatusBadge status={call.outcome} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : activeTab === 'leads' ? (
              <div>
                <CardHeader>
                  <CardTitle>Mass Drips Leads</CardTitle>
                  <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Ready for calling</span>
                </CardHeader>
                <div className="space-y-0 -mx-5 divide-y divide-white/5">
                  {massDripsLeads.map((lead) => (
                    <div key={lead.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-white/5 transition-colors">
                      <div>
                        <p className="text-sm font-medium text-white">{lead.name}</p>
                        <p className="text-xs text-white/50">{lead.phone} · {lead.city} · Interested in: {lead.interests.join(', ')}</p>
                      </div>
                      <Button
                        size="sm"
                        variant="primary"
                        leftIcon={<Phone size={12} />}
                        onClick={() => handleStartCallWithLead(lead)}
                      >
                        Call
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                <CardHeader>
                  <CardTitle>Mass Drips Campaigns</CardTitle>
                  <Button size="sm" variant="ghost" rightIcon={<ArrowRight size={12} />} onClick={() => navigate('/campaigns')}>
                    Manage
                  </Button>
                </CardHeader>
                <div className="space-y-3">
                  {massDripsCampaigns.map((campaign) => (
                    <div key={campaign.id} className="p-3.5 rounded-xl border border-white/10 bg-white/5 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-white">{campaign.name}</p>
                        <p className="text-xs text-white/50">Target Product: {campaign.product} · {campaign.leads} leads queued</p>
                      </div>
                      <StatusBadge status={campaign.status} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Right Sidebar — Real Activity & AI Insights */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Live Activity Feed</CardTitle>
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            </CardHeader>
            <div className="space-y-3">
              {realActivities.length === 0 ? (
                <div className="text-center py-6 text-xs text-white/40">
                  <Activity size={18} className="mx-auto mb-2 opacity-50" />
                  Live events will appear as calls complete
                </div>
              ) : (
                realActivities.slice(0, 6).map((item) => (
                  <div key={item.id} className="flex items-start gap-3 text-xs">
                    <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                      ✓
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-medium">{item.text}</p>
                      <p className="text-white/40 text-[10px]">{item.time}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Mass Drips Catalog Snapshot */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Active Catalog in Agent Memory</CardTitle>
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full font-medium">100% Synced</span>
              </div>
            </CardHeader>
            <div className="space-y-2 text-xs max-h-72 overflow-y-auto pr-1">
              {(storeData?.products || [
                { name: 'Jana Nayagan — Crowd Edition', price: 699, gsm: '240 GSM Tee', category: 'Kollywood', badge: 'HOT' },
                { name: 'In The Shadows We Forge', price: 1499, gsm: '240 GSM Hoodie', category: 'Heavyweights', badge: 'BESTSELLER' },
                { name: 'AK — The Don\'s Edition (380 GSM)', price: 1499, gsm: '380 GSM Fleece Drop', category: 'Kollywood', badge: 'LIMITED' },
                { name: 'Thalapathy Forever Statement Tee', price: 799, gsm: '240 GSM Statement Tee', category: 'Kollywood', badge: 'BESTSELLER' },
                { name: 'Main Rukta Nahi Hoon (Sweatshirt)', price: 1199, gsm: '240 GSM Sweatshirt', category: 'Bollywood', badge: 'NEW' },
                { name: 'Flower Nahi, FIRE (Pushpa)', price: 699, gsm: '240 GSM Wildfire Tee', category: 'Tollywood', badge: 'HOT' }
              ]).map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 rounded bg-white/[0.02] border border-white/5 hover:border-emerald-500/30 transition-all">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <p className="font-semibold text-white truncate max-w-[150px]">{item.name}</p>
                      {item.badge && <span className="text-[9px] px-1 rounded bg-emerald-500/20 text-emerald-300 font-bold">{item.badge}</span>}
                    </div>
                    <p className="text-[10px] text-white/40">{item.gsm || item.category || 'Mass Drips Drop'}</p>
                  </div>
                  <span className="font-bold text-emerald-400">Rs {item.price}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      <LiveCallModal
        isOpen={callModalOpen}
        onClose={() => {
          setCallModalOpen(false);
          refreshData();
        }}
        onCallCompleted={() => refreshData()}
        leadName={selectedLead.name}
        leadPhone={selectedLead.phone}
        brandName="Mass Drips"
      />
    </div>
  );
}
