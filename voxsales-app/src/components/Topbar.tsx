import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Search, Bell, ChevronDown, Zap, Menu, X,
  LayoutDashboard, Compass, FolderKanban, BarChart3, Bookmark, Settings, User } from 'lucide-react';
import { useToast } from './Toast';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/discover', icon: Compass, label: 'Discover' },
  { to: '/campaigns', icon: FolderKanban, label: 'Campaigns' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/favorites', icon: Bookmark, label: 'Favorites' },
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/profile', icon: User, label: 'Profile' },
];

interface TopbarProps {
  title: string;
  subtitle?: string;
}

export default function Topbar({ title, subtitle }: TopbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const { showToast } = useToast();

  return (
    <>
      <header
        className="sticky top-0 z-30 flex items-center gap-4 px-4 lg:px-6 h-16"
        style={{
          background: 'rgba(10, 10, 15, 0.85)',
          backdropFilter: 'blur(16px)',
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        {/* Mobile menu toggle */}
        <button
          className="lg:hidden p-2 rounded-lg hover:bg-white/5 transition-colors"
          onClick={() => setMobileOpen(!mobileOpen)}
          style={{ color: 'var(--color-text-secondary)' }}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        {/* Mobile Logo */}
        <div className="flex lg:hidden items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #00e599, #00c47f)' }}
          >
            <Zap size={14} fill="white" color="white" />
          </div>
          <span className="text-sm font-bold" style={{ fontFamily: 'var(--font-display)' }}>VoxSales</span>
        </div>

        {/* Page Title — desktop */}
        <div className="hidden lg:block flex-1">
          <h2 className="text-base font-semibold leading-tight" style={{ color: 'var(--color-text-primary)' }}>{title}</h2>
          {subtitle && <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{subtitle}</p>}
        </div>

        {/* Search */}
        <div
          className={`hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200 flex-1 max-w-xs ${searchFocused ? 'ring-1 ring-[#00e599]/50' : ''}`}
          style={{ background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border-strong)' }}
        >
          <Search size={14} style={{ color: 'var(--color-text-muted)' }} />
          <input
            type="text"
            placeholder="Search leads, campaigns..."
            className="bg-transparent text-sm outline-none flex-1 min-w-0"
            style={{ color: 'var(--color-text-primary)' }}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          <kbd className="hidden md:block text-[10px] px-1.5 py-0.5 rounded" style={{ background: 'var(--color-bg-base)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border)' }}>
            ⌘K
          </kbd>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 ml-auto lg:ml-0">
          <button
            onClick={() => showToast('info', '3 new notifications', 'Ananya Roy converted + 2 more')}
            className="relative p-2 rounded-xl hover:bg-white/5 transition-colors"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            <Bell size={18} />
            <span
              className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full"
              style={{ background: 'var(--color-accent)' }}
            />
          </button>

          <button
            className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-xl hover:bg-white/5 transition-colors"
          >
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold"
              style={{ background: 'linear-gradient(135deg, #00e599, #6366f1)', color: '#fff' }}
            >
              AD
            </div>
            <ChevronDown size={12} style={{ color: 'var(--color-text-muted)' }} />
          </button>
        </div>
      </header>

      {/* Mobile Nav Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50" onClick={() => setMobileOpen(false)}>
          <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }} />
          <div
            className="absolute left-0 top-0 h-full w-72 animate-slide-in-right"
            style={{ background: 'var(--color-bg-surface)', borderRight: '1px solid var(--color-border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-5 pt-6 pb-5 flex items-center gap-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
              <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #00e599, #00c47f)' }}>
                <Zap size={16} fill="white" color="white" />
              </div>
              <div>
                <h1 className="text-sm font-bold" style={{ fontFamily: 'var(--font-display)' }}>VoxSales</h1>
                <p className="text-[10px]" style={{ color: 'var(--color-accent)' }}>AI Voice Platform</p>
              </div>
              <button onClick={() => setMobileOpen(false)} className="ml-auto p-1" style={{ color: 'var(--color-text-muted)' }}>
                <X size={18} />
              </button>
            </div>
            <nav className="p-3 space-y-0.5">
              {navItems.map(({ to, icon: Icon, label, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors ${
                      isActive ? 'text-[#0a0a0f]' : 'hover:bg-white/5'
                    }`
                  }
                  style={({ isActive }) => isActive
                    ? { background: 'var(--color-accent)', color: '#0a0a0f' }
                    : { color: 'var(--color-text-secondary)' }
                  }
                >
                  {() => (
                    <>
                      <Icon size={18} />
                      {label}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
