import { useState } from 'react';
import { Search, Filter, Star, Phone, Zap, Mic, Package } from 'lucide-react';
import Card from '../components/Card';
import { StatusBadge } from '../components/Badge';
import Button from '../components/Button';
import { useToast } from '../components/Toast';
import { massDripsCampaigns, massDripsLeads, massDripsProducts } from '../data/realStore';
import LiveCallModal from '../components/LiveCallModal';

const categories = ['All', 'Products', 'Leads', 'Campaigns', 'Insights'];

const insights = [
  {
    id: 'I1',
    title: 'Hinglish converts 2.3× better for Indian Streetwear',
    desc: 'Speaking in natural Hinglish with colloquial terms (like "fit", "fabric", "oversized") increases customer engagement by 70%.',
    icon: Mic, color: '#00e599',
  },
  {
    id: 'I2',
    title: 'Acid Wash Tees drive highest first-order conversions',
    desc: 'Leads pitched the 240 GSM Acid Wash Oversized Tee have the highest same-day checkout rate.',
    icon: Package, color: '#6366f1',
  },
  {
    id: 'I3',
    title: '10% Coupon (DRIP10) resolves 85% price objections',
    desc: 'Offering a 10% first-order discount code during the objection handling stage closes 8 out of 10 hesitant buyers.',
    icon: Zap, color: '#f59e0b',
  },
];

export default function Discover() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [callModalOpen, setCallModalOpen] = useState(false);
  const [activeLead, setActiveLead] = useState<{ name: string; phone: string }>({ name: 'Rahul Sharma', phone: '+91 98765 43210' });
  const { showToast } = useToast();

  const toggleFav = (id: string, name: string) => {
    setFavorites(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        showToast('info', 'Removed from favorites', name);
      } else {
        next.add(id);
        showToast('success', 'Saved to favorites!', name);
      }
      return next;
    });
  };

  const handleLaunchCall = (lead: { name: string; phone: string }) => {
    setActiveLead(lead);
    setCallModalOpen(true);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Search bar */}
      <div
        className="flex items-center gap-3 p-4 rounded-2xl"
        style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}
      >
        <Search size={18} style={{ color: 'var(--color-text-muted)' }} />
        <input
          type="text"
          placeholder="Search Mass Drips products, leads, campaigns..."
          className="flex-1 bg-transparent text-sm outline-none"
          style={{ color: 'var(--color-text-primary)' }}
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        <Button size="sm" variant="secondary" leftIcon={<Filter size={13} />}>Filter</Button>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all"
            style={activeCategory === cat
              ? { background: 'var(--color-accent)', color: '#0a0a0f' }
              : { background: 'var(--color-bg-card)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border)' }
            }
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Streetwear Catalog */}
      {(activeCategory === 'All' || activeCategory === 'Products') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            📦 Mass Drips Active Product Catalog
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {massDripsProducts.map((product, i) => (
              <Card
                key={product.id}
                hover
                className="animate-fade-in-up"
                style={{ animationDelay: `${i * 70}ms` }}
              >
                <div className="flex items-start gap-3">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0"
                    style={{ background: 'var(--color-bg-elevated)' }}
                  >
                    👕
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>{product.name}</p>
                    <p className="text-xs text-white/40">{product.gsm}</p>
                    <p className="text-sm font-bold mt-1 text-emerald-400">₹{product.price.toLocaleString()}</p>
                  </div>
                  <button
                    onClick={() => toggleFav(product.id, product.name)}
                    style={{ color: favorites.has(product.id) ? '#f59e0b' : 'var(--color-text-muted)' }}
                  >
                    <Star size={14} fill={favorites.has(product.id) ? '#f59e0b' : 'none'} />
                  </button>
                </div>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/10 text-xs">
                  <span className="text-white/50">Stock: <strong className="text-white">{product.stock} units</strong></span>
                  <span className="text-emerald-400 font-semibold">⭐ {product.rating}</span>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Target Leads */}
      {(activeCategory === 'All' || activeCategory === 'Leads') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            🔥 Mass Drips Leads
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {massDripsLeads.map((lead, i) => (
              <Card
                key={lead.id}
                hover
                className="animate-fade-in-up"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold shrink-0 text-black"
                    style={{ background: 'var(--color-accent)' }}
                  >
                    {lead.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold truncate text-white">{lead.name}</p>
                    <p className="text-xs text-white/40">{lead.city}</p>
                  </div>
                </div>
                <div className="text-xs text-white/50 mb-3 truncate">
                  {lead.interests.join(' · ')}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Score: {lead.score}
                  </span>
                  <Button
                    size="sm"
                    variant="primary"
                    leftIcon={<Phone size={11} />}
                    onClick={() => handleLaunchCall(lead)}
                  >
                    Call
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Active Outreach Campaigns */}
      {(activeCategory === 'All' || activeCategory === 'Campaigns') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            🚀 Active Campaigns
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-2 gap-4">
            {massDripsCampaigns.map((campaign, i) => (
              <Card
                key={campaign.id}
                hover
                className="animate-fade-in-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white">{campaign.name}</h3>
                  <StatusBadge status={campaign.status} />
                </div>
                <p className="text-xs text-white/50 mb-3">Target Product: {campaign.product}</p>
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-white/10 text-xs">
                  <div>
                    <p className="text-white/40 text-[10px]">Leads Queued</p>
                    <p className="text-sm font-bold text-white">{campaign.leads}</p>
                  </div>
                  <div>
                    <p className="text-white/40 text-[10px]">Persona</p>
                    <p className="text-sm font-bold text-emerald-400">Aria (Hinglish)</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* AI Insights */}
      {(activeCategory === 'All' || activeCategory === 'Insights') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            🤖 AI Sales Insights & Strategies
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {insights.map((insight, i) => {
              const Icon = insight.icon;
              return (
                <Card key={insight.id} hover className="animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
                    style={{ background: `${insight.color}20` }}
                  >
                    <Icon size={18} style={{ color: insight.color }} />
                  </div>
                  <h3 className="text-sm font-semibold mb-1 text-white">{insight.title}</h3>
                  <p className="text-xs leading-relaxed text-white/60">{insight.desc}</p>
                </Card>
              );
            })}
          </div>
        </section>
      )}

      <LiveCallModal
        isOpen={callModalOpen}
        onClose={() => setCallModalOpen(false)}
        leadName={activeLead.name}
        leadPhone={activeLead.phone}
        brandName="Mass Drips"
      />
    </div>
  );
}
