import { useState } from 'react';
import { Edit3, Save, MapPin, Mail, Phone, Calendar, Award, TrendingUp, Zap } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../components/Card';
import Button from '../components/Button';
import { useToast } from '../components/Toast';

const achievements = [
  { icon: '🏆', label: '100 Conversions', date: 'Sep 2026' },
  { icon: '🚀', label: 'First Campaign', date: 'Apr 2026' },
  { icon: '⚡', label: 'Sub-500ms Latency', date: 'Jun 2026' },
  { icon: '🎯', label: '30%+ Conv. Rate', date: 'Aug 2026' },
];

const activityHeatmap = Array.from({ length: 52 }, () =>
  Array.from({ length: 7 }, () => Math.floor(Math.random() * 5))
);

export default function Profile() {
  const [editing, setEditing] = useState(false);
  const [profile, setProfile] = useState({
    name: 'Aditya Dev',
    role: 'Platform Admin',
    company: 'Mass Drips',
    email: 'aditya@massdrips.in',
    phone: '+91 98765 43210',
    location: 'Mumbai, India',
    bio: 'Building the future of AI-powered voice sales for India\'s fast-growing e-commerce ecosystem.',
    joinDate: 'April 2026',
  });
  const { showToast } = useToast();

  const handleSave = () => {
    setEditing(false);
    showToast('success', 'Profile updated!', 'Changes saved successfully');
  };

  const colors = ['var(--color-bg-elevated)', 'rgba(0,229,153,0.2)', 'rgba(0,229,153,0.4)', 'rgba(0,229,153,0.65)', '#00e599'];

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Profile Hero */}
      <Card>
        <div className="flex flex-col sm:flex-row items-start gap-5">
          <div className="relative">
            <div
              className="w-20 h-20 rounded-2xl flex items-center justify-center text-2xl font-bold"
              style={{ background: 'linear-gradient(135deg, #00e599, #6366f1)', color: '#fff', fontFamily: 'var(--font-display)' }}
            >
              AD
            </div>
            <div
              className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center"
              style={{ background: '#00e599', border: '2px solid var(--color-bg-card)' }}
            >
              <div className="w-2 h-2 rounded-full bg-black animate-pulse" />
            </div>
          </div>

          <div className="flex-1">
            {editing ? (
              <div className="grid sm:grid-cols-2 gap-3">
                {[
                  { key: 'name', label: 'Full Name' },
                  { key: 'role', label: 'Role' },
                  { key: 'company', label: 'Company' },
                  { key: 'location', label: 'Location' },
                ].map(({ key, label }) => (
                  <div key={key}>
                    <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-muted)' }}>{label}</label>
                    <input
                      className="w-full px-3 py-2 rounded-xl text-sm outline-none"
                      style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
                      value={profile[key as keyof typeof profile]}
                      onChange={e => setProfile(p => ({ ...p, [key]: e.target.value }))}
                    />
                  </div>
                ))}
                <div className="sm:col-span-2">
                  <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-muted)' }}>Bio</label>
                  <textarea
                    className="w-full px-3 py-2 rounded-xl text-sm outline-none resize-none"
                    rows={2}
                    style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
                    value={profile.bio}
                    onChange={e => setProfile(p => ({ ...p, bio: e.target.value }))}
                  />
                </div>
              </div>
            ) : (
              <>
                <h2 className="text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-primary)' }}>
                  {profile.name}
                </h2>
                <p className="text-sm mt-0.5" style={{ color: 'var(--color-accent)' }}>{profile.role} · {profile.company}</p>
                <p className="text-sm mt-2 max-w-lg" style={{ color: 'var(--color-text-secondary)' }}>{profile.bio}</p>
                <div className="flex flex-wrap gap-4 mt-3">
                  {[
                    { icon: MapPin, text: profile.location },
                    { icon: Mail, text: profile.email },
                    { icon: Phone, text: profile.phone },
                    { icon: Calendar, text: `Joined ${profile.joinDate}` },
                  ].map(({ icon: Icon, text }) => (
                    <div key={text} className="flex items-center gap-1.5">
                      <Icon size={12} style={{ color: 'var(--color-text-muted)' }} />
                      <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{text}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          <Button
            variant={editing ? 'primary' : 'secondary'}
            size="sm"
            leftIcon={editing ? <Save size={13} /> : <Edit3 size={13} />}
            onClick={editing ? handleSave : () => setEditing(true)}
          >
            {editing ? 'Save' : 'Edit'}
          </Button>
        </div>
      </Card>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { icon: TrendingUp, label: 'Total Calls Managed', value: '12,847', color: '#00e599' },
          { icon: Zap, label: 'Campaigns Launched', value: '6', color: '#6366f1' },
          { icon: Award, label: 'Conversions Driven', value: '4,163', color: '#f59e0b' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="rounded-2xl p-4 text-center" style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)' }}>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center mx-auto mb-2" style={{ background: `${color}20` }}>
              <Icon size={16} style={{ color }} />
            </div>
            <p className="text-xl font-bold" style={{ color, fontFamily: 'var(--font-display)' }}>{value}</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Activity Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle>Activity Heatmap</CardTitle>
            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Last 12 months</span>
          </CardHeader>
          <div className="flex gap-0.5 overflow-x-auto pb-2">
            {activityHeatmap.slice(-26).map((week, wi) => (
              <div key={wi} className="flex flex-col gap-0.5">
                {week.map((val, di) => (
                  <div
                    key={di}
                    className="w-3 h-3 rounded-sm transition-opacity hover:opacity-70"
                    style={{ background: colors[val] }}
                    title={`${val} activities`}
                  />
                ))}
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-3">
            <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Less</span>
            {colors.map((c, i) => (
              <div key={i} className="w-3 h-3 rounded-sm" style={{ background: c }} />
            ))}
            <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>More</span>
          </div>
        </Card>

        {/* Achievements */}
        <Card>
          <CardHeader>
            <CardTitle>Achievements</CardTitle>
          </CardHeader>
          <div className="grid grid-cols-2 gap-3">
            {achievements.map((ach) => (
              <div
                key={ach.label}
                className="flex items-center gap-3 p-3 rounded-xl"
                style={{ background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)' }}
              >
                <span className="text-2xl">{ach.icon}</span>
                <div>
                  <p className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>{ach.label}</p>
                  <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{ach.date}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
