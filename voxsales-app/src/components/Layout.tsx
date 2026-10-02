import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

const pageMeta: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'Good morning, Aditya 👋 Here\'s your AI sales overview' },
  '/discover': { title: 'Discover', subtitle: 'Explore campaigns, insights and new opportunities' },
  '/campaigns': { title: 'Campaigns', subtitle: 'Manage and monitor your outreach campaigns' },
  '/analytics': { title: 'Analytics', subtitle: 'Deep dive into your performance data' },
  '/favorites': { title: 'Favorites', subtitle: 'Your saved campaigns, leads and products' },
  '/settings': { title: 'Settings', subtitle: 'Configure your platform and agent preferences' },
  '/profile': { title: 'Profile', subtitle: 'Manage your account and workspace' },
};

export default function Layout() {
  const location = useLocation();
  const meta = pageMeta[location.pathname] ?? { title: 'VoxSales', subtitle: '' };

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen lg:pl-60">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
