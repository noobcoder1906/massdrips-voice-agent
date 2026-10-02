import { useState } from 'react';
import { Star, Trash2, ExternalLink, FolderKanban, Users, Package } from 'lucide-react';
import Card from '../components/Card';
import { StatusBadge } from '../components/Badge';
import Button from '../components/Button';
import { useToast } from '../components/Toast';
import { mockFavorites } from '../data/mockData';

const typeIcons = {
  campaign: FolderKanban,
  lead: Users,
  product: Package,
};

const typeColors = {
  campaign: '#6366f1',
  lead: '#00e599',
  product: '#f59e0b',
};

export default function Favorites() {
  const [items, setItems] = useState(mockFavorites);
  const { showToast } = useToast();

  const remove = (id: string, name: string) => {
    setItems(prev => prev.filter(i => i.id !== id));
    showToast('info', 'Removed from favorites', name);
  };

  if (items.length === 0) {
    return (
      <div className="animate-fade-in flex flex-col items-center justify-center py-24 text-center">
        <div
          className="w-20 h-20 rounded-2xl flex items-center justify-center mb-4"
          style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}
        >
          <Star size={32} style={{ color: 'var(--color-text-muted)' }} />
        </div>
        <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>No favorites yet</h2>
        <p className="text-sm max-w-xs" style={{ color: 'var(--color-text-muted)' }}>
          Save campaigns, leads, or products from the Discover page by clicking the star icon.
        </p>
      </div>
    );
  }

  const grouped = {
    campaign: items.filter(i => i.type === 'campaign'),
    lead: items.filter(i => i.type === 'lead'),
    product: items.filter(i => i.type === 'product'),
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Summary */}
      <div className="flex items-center gap-4">
        {Object.entries(grouped).map(([type, group]) => {
          const Icon = typeIcons[type as keyof typeof typeIcons];
          const color = typeColors[type as keyof typeof typeColors];
          return (
            <div
              key={type}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl"
              style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}
            >
              <Icon size={15} style={{ color }} />
              <span className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
                {group.length} {type}{group.length !== 1 ? 's' : ''}
              </span>
            </div>
          );
        })}
      </div>

      {/* Favorited items grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, i) => {
          const Icon = typeIcons[item.type as keyof typeof typeIcons];
          const color = typeColors[item.type as keyof typeof typeColors];
          return (
            <Card
              key={item.id}
              hover
              className="animate-fade-in-up group"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: `${color}20` }}
                >
                  <Icon size={18} style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>{item.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusBadge status={item.status} />
                    <span className="text-xs font-semibold" style={{ color }}>{item.metric}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-4 pt-3" style={{ borderTop: '1px solid var(--color-border)' }}>
                <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Saved {item.savedAt}</p>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                    onClick={() => showToast('info', 'Opening...', item.name)}
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    <ExternalLink size={13} />
                  </button>
                  <button
                    className="p-1.5 rounded-lg hover:bg-white/5 transition-colors"
                    onClick={() => remove(item.id, item.name)}
                    style={{ color: '#ef4444' }}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {items.length > 0 && (
        <div className="flex justify-center">
          <Button
            variant="danger"
            size="sm"
            onClick={() => {
              setItems([]);
              showToast('info', 'All favorites cleared');
            }}
          >
            Clear All Favorites
          </Button>
        </div>
      )}
    </div>
  );
}
