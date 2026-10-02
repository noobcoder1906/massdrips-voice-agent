import { useState } from 'react';
import { Search, Filter, Star, Phone, TrendingUp, Zap, Mic, Package } from 'lucide-react';
import Card from '../components/Card';
import { StatusBadge } from '../components/Badge';
import Button from '../components/Button';
import { useToast } from '../components/Toast';
import { mockCampaigns, mockLeads, mockProducts } from '../data/mockData';

const categories = ['All', 'Campaigns', 'Leads', 'Products', 'Insights'];

const insights = [
  {
    id: 'I1',
    title: 'Best time to call: 10am–12pm IST',
    desc: 'Analysis of 12K+ calls shows 41% higher pickup rate in morning slots.',
    icon: TrendingUp, color: '#00e599',
  },
  {
    id: 'I2',
    title: 'Hinglish converts 2.3× better',
    desc: 'Leads addressed in Hinglish show significantly higher engagement.',
    icon: Mic, color: '#6366f1',
  },
  {
    id: 'I3',
    title: 'Hoodies drive highest LTV',
    desc: 'Hoodie buyers have 3× repeat purchase rate vs other categories.',
    icon: Package, color: '#f59e0b',
  },
  {
    id: 'I4',
    title: 'Re-engagement yields 28% recovery',
    desc: 'Leads contacted after 7 days convert at nearly 1/3 rate.',
    icon: Zap, color: '#00e599',
  },
];

export default function Discover() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
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
          placeholder="Search campaigns, leads, products, insights..."
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

      {/* AI Insights */}
      {(activeCategory === 'All' || activeCategory === 'Insights') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            🤖 AI Insights
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
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
                  <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>{insight.title}</h3>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-muted)' }}>{insight.desc}</p>
                </Card>
              );
            })}
          </div>
        </section>
      )}

      {/* Featured Campaigns */}
      {(activeCategory === 'All' || activeCategory === 'Campaigns') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            🚀 Featured Campaigns
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {mockCampaigns.slice(0, 3).map((campaign, i) => (
              <Card
                key={campaign.id}
                hover
                className="animate-fade-in-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="flex items-start justify-between mb-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-sm"
                    style={{ background: 'var(--color-accent-muted)', border: '1px solid var(--color-accent-border)' }}
                  >
                    🚀
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={campaign.status} />
                    <button
                      onClick={() => toggleFav(campaign.id, campaign.name)}
                      className="p-1 rounded-lg hover:bg-white/5 transition-colors"
                      style={{ color: favorites.has(campaign.id) ? '#f59e0b' : 'var(--color-text-muted)' }}
                    >
                      <Star size={14} fill={favorites.has(campaign.id) ? '#f59e0b' : 'none'} />
                    </button>
                  </div>
                </div>
                <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>{campaign.name}</h3>
                <p className="text-xs mb-3" style={{ color: 'var(--color-text-muted)' }}>{campaign.product}</p>
                <div className="grid grid-cols-3 gap-2 pt-3" style={{ borderTop: '1px solid var(--color-border)' }}>
                  <div>
                    <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Leads</p>
                    <p className="text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>{campaign.leads.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Calls</p>
                    <p className="text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>{campaign.calls.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Conv.</p>
                    <p className="text-sm font-bold" style={{ color: 'var(--color-accent)' }}>{campaign.successRate}%</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Hot Leads */}
      {(activeCategory === 'All' || activeCategory === 'Leads') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            🔥 Hot Leads
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {mockLeads.filter(l => l.status === 'hot').map((lead, i) => (
              <Card
                key={lead.id}
                hover
                className="animate-fade-in-up"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                    style={{ background: 'linear-gradient(135deg, #00e599, #6366f1)', color: '#fff' }}
                  >
                    {lead.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>{lead.name}</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{lead.city}</p>
                  </div>
                  <button
                    onClick={() => toggleFav(lead.id, lead.name)}
                    className="ml-auto p-1"
                    style={{ color: favorites.has(lead.id) ? '#f59e0b' : 'var(--color-text-muted)' }}
                  >
                    <Star size={14} fill={favorites.has(lead.id) ? '#f59e0b' : 'none'} />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs px-2 py-0.5 rounded-full font-semibold" style={{ background: 'var(--color-accent-muted)', color: 'var(--color-accent)' }}>
                    Score: {lead.score}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    leftIcon={<Phone size={11} />}
                    onClick={() => showToast('success', `Calling ${lead.name}...`, lead.phone)}
                  >
                    Call
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Products */}
      {(activeCategory === 'All' || activeCategory === 'Products') && (
        <section>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)' }}>
            📦 Top Products
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {mockProducts.slice(0, 3).map((product, i) => (
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
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{product.category}</p>
                    <p className="text-sm font-bold mt-1" style={{ color: 'var(--color-accent)' }}>₹{product.price.toLocaleString()}</p>
                  </div>
                  <button
                    onClick={() => toggleFav(product.id, product.name)}
                    style={{ color: favorites.has(product.id) ? '#f59e0b' : 'var(--color-text-muted)' }}
                  >
                    <Star size={14} fill={favorites.has(product.id) ? '#f59e0b' : 'none'} />
                  </button>
                </div>
                <div className="flex items-center gap-4 mt-3 pt-3" style={{ borderTop: '1px solid var(--color-border)' }}>
                  <div>
                    <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Orders</p>
                    <p className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>{product.orders.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Rating</p>
                    <p className="text-xs font-semibold" style={{ color: 'var(--color-accent)' }}>⭐ {product.rating}</p>
                  </div>
                  <div>
                    <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Stock</p>
                    <p className="text-xs font-semibold" style={{ color: product.stock < 100 ? '#f59e0b' : 'var(--color-text-primary)' }}>{product.stock}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
