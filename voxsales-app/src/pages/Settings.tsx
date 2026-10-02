import { useState } from 'react';
import { Bell, Zap, Globe, Shield, Webhook, Key, ChevronRight, Save } from 'lucide-react';
import Card, { CardHeader, CardTitle } from '../components/Card';
import Button from '../components/Button';
import { useToast } from '../components/Toast';

const sections = [
  { id: 'agent', icon: Zap, label: 'Agent Persona', color: '#00e599' },
  { id: 'notifications', icon: Bell, label: 'Notifications', color: '#6366f1' },
  { id: 'integrations', icon: Webhook, label: 'Integrations', color: '#f59e0b' },
  { id: 'security', icon: Shield, label: 'Security', color: '#ef4444' },
  { id: 'api', icon: Key, label: 'API Keys', color: '#00e599' },
  { id: 'language', icon: Globe, label: 'Language & Region', color: '#6366f1' },
];

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!value)}
      className="relative w-10 h-5 rounded-full transition-colors duration-200"
      style={{ background: value ? 'var(--color-accent)' : 'var(--color-bg-elevated)' }}
    >
      <div
        className="absolute top-0.5 w-4 h-4 rounded-full transition-all duration-200"
        style={{
          left: value ? '22px' : '2px',
          background: value ? '#0a0a0f' : 'var(--color-text-muted)',
        }}
      />
    </button>
  );
}

export default function Settings() {
  const [activeSection, setActiveSection] = useState('agent');
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const [agentSettings, setAgentSettings] = useState({
    name: 'Aria',
    brand: 'Mass Drips',
    language: 'hinglish',
    tone: 'friendly',
    autoCallback: true,
    whatsappFollowup: true,
    dncRespect: true,
    maxCallDuration: '300',
  });

  const [notifSettings, setNotifSettings] = useState({
    emailOnConversion: true,
    emailOnCampaignEnd: true,
    slackAlerts: false,
    weeklyReport: true,
  });

  const handleSave = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 1000));
    setLoading(false);
    showToast('success', 'Settings saved!', 'Changes applied to your AI agent');
  };

  return (
    <div className="grid lg:grid-cols-4 gap-4 animate-fade-in">
      {/* Left nav */}
      <div className="lg:col-span-1">
        <Card>
          <nav className="space-y-0.5 -mx-5 px-3">
            {sections.map(({ id, icon: Icon, label, color }) => (
              <button
                key={id}
                onClick={() => setActiveSection(id)}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all hover:bg-white/5"
                style={activeSection === id
                  ? { background: 'var(--color-accent-muted)', color: 'var(--color-accent)', border: '1px solid var(--color-accent-border)' }
                  : { color: 'var(--color-text-secondary)' }
                }
              >
                <Icon size={15} style={{ color: activeSection === id ? 'var(--color-accent)' : color }} />
                {label}
                <ChevronRight size={12} className="ml-auto" style={{ color: 'var(--color-text-muted)' }} />
              </button>
            ))}
          </nav>
        </Card>
      </div>

      {/* Right content */}
      <div className="lg:col-span-3 space-y-4">
        {activeSection === 'agent' && (
          <Card>
            <CardHeader>
              <CardTitle>Agent Persona Configuration</CardTitle>
            </CardHeader>
            <div className="space-y-5">
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  { label: 'Agent Name', key: 'name', type: 'text', placeholder: 'e.g. Aria' },
                  { label: 'Brand Name', key: 'brand', type: 'text', placeholder: 'e.g. Mass Drips' },
                ].map(({ label, key, type, placeholder }) => (
                  <div key={key}>
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>{label}</label>
                    <input
                      type={type}
                      placeholder={placeholder}
                      className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                      style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
                      value={agentSettings[key as keyof typeof agentSettings] as string}
                      onChange={e => setAgentSettings(p => ({ ...p, [key]: e.target.value }))}
                    />
                  </div>
                ))}
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Primary Language</label>
                  <select
                    className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                    style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
                    value={agentSettings.language}
                    onChange={e => setAgentSettings(p => ({ ...p, language: e.target.value }))}
                  >
                    <option value="hinglish">Hinglish (Hindi + English)</option>
                    <option value="hindi">Hindi Only</option>
                    <option value="english">English Only</option>
                    <option value="tamil">Tamil</option>
                    <option value="telugu">Telugu</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Tone of Voice</label>
                  <select
                    className="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                    style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border-strong)', color: 'var(--color-text-primary)' }}
                    value={agentSettings.tone}
                    onChange={e => setAgentSettings(p => ({ ...p, tone: e.target.value }))}
                  >
                    <option value="friendly">Friendly & Energetic</option>
                    <option value="professional">Professional</option>
                    <option value="casual">Casual Streetwear</option>
                    <option value="formal">Formal</option>
                  </select>
                </div>
              </div>

              <div className="space-y-3 pt-2" style={{ borderTop: '1px solid var(--color-border)' }}>
                <p className="text-xs font-semibold" style={{ color: 'var(--color-text-muted)' }}>Behavior Settings</p>
                {[
                  { key: 'autoCallback', label: 'Auto-schedule callbacks', desc: 'Automatically schedule follow-up calls for busy contacts' },
                  { key: 'whatsappFollowup', label: 'WhatsApp follow-up', desc: 'Send post-call WhatsApp messages to interested leads' },
                  { key: 'dncRespect', label: 'Respect DNC list', desc: 'Never call leads who have opted out' },
                ].map(({ key, label, desc }) => (
                  <div key={key} className="flex items-center justify-between py-2">
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{label}</p>
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{desc}</p>
                    </div>
                    <Toggle
                      value={agentSettings[key as keyof typeof agentSettings] as boolean}
                      onChange={v => setAgentSettings(p => ({ ...p, [key]: v }))}
                    />
                  </div>
                ))}
              </div>

              <Button variant="primary" leftIcon={<Save size={14} />} loading={loading} onClick={handleSave}>
                Save Agent Settings
              </Button>
            </div>
          </Card>
        )}

        {activeSection === 'notifications' && (
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
            </CardHeader>
            <div className="space-y-3">
              {[
                { key: 'emailOnConversion', label: 'Email on conversion', desc: 'Get notified when a lead converts' },
                { key: 'emailOnCampaignEnd', label: 'Campaign completion email', desc: 'Summary report when a campaign finishes' },
                { key: 'slackAlerts', label: 'Slack alerts', desc: 'Real-time Slack notifications (requires integration)' },
                { key: 'weeklyReport', label: 'Weekly performance report', desc: 'Detailed weekly email digest every Monday' },
              ].map(({ key, label, desc }) => (
                <div key={key} className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{label}</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{desc}</p>
                  </div>
                  <Toggle
                    value={notifSettings[key as keyof typeof notifSettings]}
                    onChange={v => setNotifSettings(p => ({ ...p, [key]: v }))}
                  />
                </div>
              ))}
            </div>
            <Button variant="primary" leftIcon={<Save size={14} />} loading={loading} onClick={handleSave} className="mt-4">
              Save Preferences
            </Button>
          </Card>
        )}

        {activeSection === 'api' && (
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
            </CardHeader>
            <div className="space-y-4">
              {[
                { label: 'Production API Key', value: 'vox_prod_sk_••••••••••••••••4f2a', active: true },
                { label: 'Development API Key', value: 'vox_dev_sk_••••••••••••••••8b1c', active: false },
              ].map(({ label, value, active }) => (
                <div key={label} className="p-4 rounded-xl" style={{ background: 'var(--color-bg-base)', border: '1px solid var(--color-border)' }}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{label}</p>
                    <span
                      className="text-xs px-2 py-0.5 rounded-full font-medium"
                      style={active
                        ? { background: 'var(--color-accent-muted)', color: 'var(--color-accent)' }
                        : { background: 'var(--color-bg-elevated)', color: 'var(--color-text-muted)' }
                      }
                    >
                      {active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <code className="text-xs font-mono" style={{ color: 'var(--color-text-muted)' }}>{value}</code>
                  <div className="flex gap-2 mt-3">
                    <Button size="sm" variant="secondary" onClick={() => showToast('info', 'Copied to clipboard!')}>Copy</Button>
                    <Button size="sm" variant="danger" onClick={() => showToast('warning', 'Key regenerated', 'Old key is now invalid')}>Regenerate</Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {!['agent', 'notifications', 'api'].includes(activeSection) && (
          <Card>
            <div className="py-12 text-center">
              <p className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>
                {sections.find(s => s.id === activeSection)?.label} settings
              </p>
              <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Configuration panel coming soon.</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
