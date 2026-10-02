import { useState, useRef, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Compass, FolderKanban, BarChart3, Bookmark,
  Settings, User, Zap, ChevronDown, Bell, LogOut, HelpCircle
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/discover', icon: Compass, label: 'Discover' },
  { to: '/campaigns', icon: FolderKanban, label: 'Campaigns' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/favorites', icon: Bookmark, label: 'Favorites' },
];

const bottomItems = [
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <aside
      className="hidden lg:flex flex-col fixed left-0 top-0 h-full w-60 z-40"
      style={{
        background: 'var(--color-bg-surface)',
        borderRight: '1px solid var(--color-border)',
      }}
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-5" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 glow-accent"
            style={{ background: 'linear-gradient(135deg, #00e599, #00c47f)' }}
          >
            <Zap size={18} fill="white" color="white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight" style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}>
              VoxSales
            </h1>
            <p className="text-[10px] font-medium" style={{ color: 'var(--color-accent)' }}>AI Voice Platform</p>
          </div>
        </div>
      </div>

      {/* Tenant Badge */}
      <div className="mx-4 mt-4 mb-2">
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg"
          style={{ background: 'var(--color-accent-muted)', border: '1px solid var(--color-accent-border)' }}
        >
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--color-accent)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--color-accent)' }}>Mass Drips (Tenant #1)</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 pt-2 space-y-0.5 overflow-y-auto">
        <p className="px-2 py-2 text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'var(--color-text-muted)' }}>
          Main Menu
        </p>
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'text-[#0a0a0f]'
                  : 'hover:bg-white/5'
              }`
            }
            style={({ isActive }) => isActive
              ? { background: 'var(--color-accent)', color: '#0a0a0f' }
              : { color: 'var(--color-text-secondary)' }
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} className={isActive ? 'text-[#0a0a0f]' : 'group-hover:text-white transition-colors'} />
                {label}
              </>
            )}
          </NavLink>
        ))}

        <p className="px-2 py-2 mt-4 text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'var(--color-text-muted)' }}>
          Account
        </p>
        {bottomItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                isActive ? 'text-[#0a0a0f]' : 'hover:bg-white/5'
              }`
            }
            style={({ isActive }) => isActive
              ? { background: 'var(--color-accent)', color: '#0a0a0f' }
              : { color: 'var(--color-text-secondary)' }
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} className={isActive ? '' : 'group-hover:text-white transition-colors'} />
                {label}
              </>
            )}
          </NavLink>
        ))}
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${isActive ? 'text-[#0a0a0f]' : 'hover:bg-white/5'}`
          }
          style={({ isActive }) => isActive
            ? { background: 'var(--color-accent)', color: '#0a0a0f' }
            : { color: 'var(--color-text-secondary)' }
          }
        >
          {({ isActive }) => (
            <>
              <User size={16} className={isActive ? '' : 'group-hover:text-white transition-colors'} />
              Profile
            </>
          )}
        </NavLink>
      </nav>

      {/* User Profile */}
      <div className="p-3 mt-auto" style={{ borderTop: '1px solid var(--color-border)' }} ref={menuRef}>
        <button
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 transition-colors group"
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
            style={{ background: 'linear-gradient(135deg, #00e599, #6366f1)', color: '#fff' }}
          >
            AD
          </div>
          <div className="flex-1 text-left min-w-0">
            <p className="text-xs font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>Aditya Dev</p>
            <p className="text-[10px] truncate" style={{ color: 'var(--color-text-muted)' }}>Admin · Mass Drips</p>
          </div>
          <ChevronDown
            size={14}
            className="transition-transform duration-200 shrink-0"
            style={{
              color: 'var(--color-text-muted)',
              transform: userMenuOpen ? 'rotate(180deg)' : 'none'
            }}
          />
        </button>

        {userMenuOpen && (
          <div
            className="mt-2 rounded-xl overflow-hidden animate-slide-down shadow-2xl"
            style={{ background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border-strong)' }}
          >
            <NavLink to="/profile" onClick={() => setUserMenuOpen(false)}
              className="flex items-center gap-2 px-4 py-3 text-sm hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              <User size={14} /> View Profile
            </NavLink>
            <button className="flex items-center gap-2 px-4 py-3 text-sm w-full text-left hover:bg-white/5 transition-colors" style={{ color: 'var(--color-text-secondary)' }}>
              <Bell size={14} /> Notifications
            </button>
            <button className="flex items-center gap-2 px-4 py-3 text-sm w-full text-left hover:bg-white/5 transition-colors" style={{ color: 'var(--color-text-secondary)' }}>
              <HelpCircle size={14} /> Help & Docs
            </button>
            <div style={{ borderTop: '1px solid var(--color-border)' }}>
              <button className="flex items-center gap-2 px-4 py-3 text-sm w-full text-left hover:bg-white/5 transition-colors" style={{ color: '#ef4444' }}>
                <LogOut size={14} /> Sign Out
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
