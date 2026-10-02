import { useState } from 'react';
import { Plus, Play, Pause, Eye, Trash2, Search } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../components/Card';
import { StatusBadge } from '../components/Badge';
import Button from '../components/Button';
import Modal from '../components/Modal';
import { useToast } from '../components/Toast';
import { mockCampaigns } from '../data/mockData';

type Campaign = typeof mockCampaigns[0];

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState(mockCampaigns);
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModal, setDetailModal] = useState<Campaign | null>(null);
  const [newCampaign, setNewCampaign] = useState({ name: '', product: '', leads: '' });
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const filtered = campaigns.filter(c => {
    const matchesFilter = filter === 'all' || c.status === filter;
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) || c.product.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleCreate = async () => {
    if (!newCampaign.name.trim()) {
      showToast('error', 'Name required', 'Please enter a campaign name');
      return;
    }
    setLoading(true);
    await new Promise(r => setTimeout(r, 1200));
    setCampaigns(prev => [{
      id: String(Date.now()),
      name: newCampaign.name,
      product: newCampaign.product || 'Mixed Products',
      leads: parseInt(newCampaign.leads) || 0,
      calls: 0, conversions: 0, successRate: 0,
      status: 'draft',
    }, ...prev]);
    setLoading(false);
    setModalOpen(false);
    setNewCampaign({ name: '', product: '', leads: '' });
    showToast('success', 'Campaign created!', `"${newCampaign.name}" added as draft`);
  };

  const toggleStatus = (id: string) => {
    setCampaigns(prev => prev.map(c => {
      if (c.id !== id) return c;
      const next = c.status === 'active' ? 'paused' : 'active';
      showToast('info', `Campaign ${next}`, c.name);
      return { ...c, status: next };
    }));
  };

  const deleteCampaign = (id: string, name: string) => {
    setCampaigns(prev => prev.filter(c => c.id !== id));
    showToast('warning', 'Campaign deleted', name);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Summary KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Campaigns', value: campaigns.length, color: '#6366f1' },
          { label: 'Active Now', value: campaigns.filter(c => c.status === 'active').length, color: '#00e599' },
          { label: 'Total Conversions', value: campaigns.reduce((a, c) => a + c.conversions, 0).toLocaleString(), color: '#00e599' },
          { label: 'Avg Conv. Rate', value: `${(campaigns.filter(c=>c.calls>0).reduce((a,c) => a + c.successRate, 0) / campaigns.filter(c=>c.calls>0).length).toFixed(1)}%`, color: '#f59e0b' },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="rounded-2xl p-4"
            style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}
          >
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
            <p className="text-2xl font-bold mt-1" style={{ color, fontFamily: 'var(--font-display)' }}>{value}</p>
          </div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Campaign Hub</CardTitle>
          <Button variant="primary" size="sm" leftIcon={<Plus size={14} />} onClick={() => setModalOpen(true)}>
            New Campaign
          </Button>
        </CardHeader>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-5">
          <div
            className="flex items-center gap-2 px-3 py-2 rounded-xl flex-1 min-w-48"
            style={{ background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)' }}
          >
            <Search size={13} style={{ color: 'var(--color-text-muted)' }} />
            <input
              placeholder="Search campaigns..."
              className="bg-transparent text-sm outline-none flex-1"
              style={{ color: 'var(--color-text-primary)' }}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)' }}>
            {['all', 'active', 'paused', 'draft', 'completed'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all"
                style={filter === f
                  ? { background: 'var(--color-accent)', color: '#0a0a0f' }
                  : { color: 'var(--color-text-muted)' }
                }
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto -mx-5">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {['Campaign Name', 'Status', 'Leads', 'Calls Made', 'Conversions', 'Conv. Rate', 'Actions'].map(h => (
                  <th key={h} className="text-left px-5 pb-3 text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
                    No campaigns found. Create your first one above.
                  </td>
                </tr>
              ) : filtered.map((campaign, i) => (
                <tr
                  key={campaign.id}
                  className="hover:bg-white/3 transition-colors animate-fade-in-up"
                  style={{ borderBottom: '1px solid var(--color-border)', animationDelay: `${i * 50}ms` }}
                >
                  <td className="px-5 py-3.5">
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{campaign.name}</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{campaign.product}</p>
                  </td>
                  <td className="px-5 py-3.5"><StatusBadge status={campaign.status} /></td>
                  <td className="px-5 py-3.5 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{campaign.leads.toLocaleString()}</td>
                  <td className="px-5 py-3.5 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{campaign.calls.toLocaleString()}</td>
                  <td className="px-5 py-3.5 text-sm font-semibold" style={{ color: 'var(--color-accent)' }}>{campaign.conversions.toLocaleString()}</td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 rounded-full w-16" style={{ background: 'var(--color-bg-elevated)' }}>
                        <div
                          className="h-1.5 rounded-full"
                          style={{ width: `${Math.min(campaign.successRate, 100)}%`, background: campaign.successRate > 30 ? '#00e599' : '#f59e0b' }}
                        />
                      </div>
                      <span className="text-xs font-semibold" style={{ color: campaign.successRate > 30 ? '#00e599' : '#f59e0b' }}>
                        {campaign.successRate}%
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setDetailModal(campaign)}
                        className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                        title="View details"
                        style={{ color: 'var(--color-text-muted)' }}
                      >
                        <Eye size={14} />
                      </button>
                      {campaign.status !== 'completed' && campaign.status !== 'draft' && (
                        <button
                          onClick={() => toggleStatus(campaign.id)}
                          className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                          title={campaign.status === 'active' ? 'Pause' : 'Resume'}
                          style={{ color: campaign.status === 'active' ? '#f59e0b' : '#00e599' }}
                        >
                          {campaign.status === 'active' ? <Pause size={14} /> : <Play size={14} />}
                        </button>
                      )}
                      <button
                        onClick={() => deleteCampaign(campaign.id, campaign.name)}
                        className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                        title="Delete"
                        style={{ color: '#ef4444' }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Create Campaign Modal */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Create New Campaign">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Campaign Name *</label>
            <input
              type="text"
              placeholder="e.g. Winter Sale Outreach"
              className="w-full px-3 py-2.5 rounded-xl text-sm outline-none transition-colors"
              style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
              value={newCampaign.name}
              onChange={e => setNewCampaign(p => ({ ...p, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Product Focus</label>
            <input
              type="text"
              placeholder="e.g. Drip Hoodies"
              className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
              style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
              value={newCampaign.product}
              onChange={e => setNewCampaign(p => ({ ...p, product: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Number of Leads</label>
            <input
              type="number"
              placeholder="e.g. 500"
              className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
              style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
              value={newCampaign.leads}
              onChange={e => setNewCampaign(p => ({ ...p, leads: e.target.value }))}
            />
          </div>
          <div className="flex gap-3 pt-2">
            <Button variant="secondary" className="flex-1" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" className="flex-1" loading={loading} onClick={handleCreate}>Create Campaign</Button>
          </div>
        </div>
      </Modal>

      {/* Detail Modal */}
      {detailModal && (
        <Modal open={!!detailModal} onClose={() => setDetailModal(null)} title={detailModal.name} size="lg">
          <div className="grid grid-cols-3 gap-4 mb-5">
            {[
              { label: 'Leads', value: detailModal.leads.toLocaleString() },
              { label: 'Calls Made', value: detailModal.calls.toLocaleString() },
              { label: 'Conversions', value: detailModal.conversions.toLocaleString() },
              { label: 'Conv. Rate', value: `${detailModal.successRate}%` },
              { label: 'Product', value: detailModal.product },
              { label: 'Status', value: detailModal.status },
            ].map(({ label, value }) => (
              <div key={label} className="p-3 rounded-xl" style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border)' }}>
                <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
                <p className="text-sm font-semibold mt-0.5" style={{ color: 'var(--color-text-primary)' }}>{value}</p>
              </div>
            ))}
          </div>
          <div className="h-2 rounded-full" style={{ background: 'var(--color-bg-base)' }}>
            <div
              className="h-2 rounded-full"
              style={{ width: `${(detailModal.calls / Math.max(detailModal.leads, 1)) * 100}%`, background: 'var(--color-accent)' }}
            />
          </div>
          <p className="text-xs mt-2" style={{ color: 'var(--color-text-muted)' }}>
            {((detailModal.calls / Math.max(detailModal.leads, 1)) * 100).toFixed(0)}% of leads contacted
          </p>
        </Modal>
      )}
    </div>
  );
}
