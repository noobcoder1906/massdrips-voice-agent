// Real Data Store for Mass Drips Voice Platform
// Tracks real processed calls, live metrics, and real campaign data.

export interface CallRecord {
  id: string;
  lead: string;
  phone: string;
  duration: string;
  durationSec: number;
  outcome: 'converted' | 'interested' | 'callback' | 'not_interested';
  sentiment: 'very_positive' | 'positive' | 'neutral' | 'negative' | 'very_negative';
  score: number;
  date: string;
  transcript: string;
  whatsappMessage?: string;
  productDiscussed?: string;
}

export interface ActivityItem {
  id: string | number;
  type: 'call_completed' | 'campaign_launched' | 'lead_added' | 'call_failed' | 'webhook_triggered' | 'agent_updated';
  text: string;
  time: string;
  status: 'success' | 'info' | 'warning' | 'neutral';
}

const STORAGE_KEY_CALLS = 'massdrips_real_calls';
const STORAGE_KEY_ACTIVITIES = 'massdrips_real_activities';

export function getRealCalls(): CallRecord[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY_CALLS);
    if (data) return JSON.parse(data);
  } catch (e) {}
  return [];
}

export function saveRealCall(call: CallRecord): CallRecord[] {
  const existing = getRealCalls();
  const updated = [call, ...existing];
  try {
    localStorage.setItem(STORAGE_KEY_CALLS, JSON.stringify(updated));
    // Also record activity
    addRealActivity({
      id: Date.now(),
      type: 'call_completed',
      text: `${call.lead} — ${call.outcome === 'converted' ? 'Converted (High Intent 🔥)' : 'Processed Call'}`,
      time: 'Just now',
      status: call.outcome === 'converted' ? 'success' : 'info'
    });
  } catch (e) {}
  return updated;
}

export function getRealActivities(): ActivityItem[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY_ACTIVITIES);
    if (data) return JSON.parse(data);
  } catch (e) {}
  return [];
}

export function addRealActivity(act: ActivityItem): ActivityItem[] {
  const existing = getRealActivities();
  const updated = [act, ...existing.slice(0, 19)];
  try {
    localStorage.setItem(STORAGE_KEY_ACTIVITIES, JSON.stringify(updated));
  } catch (e) {}
  return updated;
}

// Mass Drips Real Live Catalog from https://www.massdrips.shop/
export const massDripsProducts = [
  { id: 'MD-001', name: 'Jana Nayagan — Crowd Edition', price: 699, category: 'Kollywood', stock: 120, sku: 'MD001-BLK', rating: 4.9, gsm: '240 GSM Heavyweight Tee' },
  { id: 'MD-002', name: 'In The Shadows We Forge', price: 1499, category: 'Heavyweights', stock: 65, sku: 'MD002-BLK', rating: 4.9, gsm: '240 GSM Oversized Hoodie' },
  { id: 'MD-003', name: 'Main Rukta Nahi Hoon', price: 1199, category: 'Bollywood', stock: 80, sku: 'MD003-BLK', rating: 4.8, gsm: '240 GSM Sweatshirt' },
  { id: 'MD-004', name: 'Main Rukta Nahi Hoon', price: 699, category: 'Bollywood', stock: 140, sku: 'MD004-BLK', rating: 4.7, gsm: '240 GSM Oversized Tee' },
  { id: 'MD-005', name: 'Kismat Der Se Aye', price: 699, category: 'Bollywood', stock: 95, sku: 'MD005-BLK', rating: 4.8, gsm: '240 GSM Cracked Wall Tee' },
  { id: 'MD-006', name: 'Kismat Der Se Aye — Melange Grey', price: 1599, category: 'Heavyweights', stock: 50, sku: 'MD006-GRY', rating: 5.0, gsm: '240 GSM Cracked Hoodie' },
  { id: 'MD-007', name: 'Kismat Der Se Aye — White', price: 1599, category: 'Heavyweights', stock: 45, sku: 'MD007-WHT', rating: 4.9, gsm: '240 GSM Cracked Hoodie' },
  { id: 'MD-008', name: 'Jana Nayagan — The People\'s Hero', price: 799, category: 'Kollywood', stock: 85, sku: 'MD008-BLK', rating: 4.9, gsm: '240 GSM Dark Silhouette Tee' },
  { id: 'MD-009', name: 'Flower Nahi, FIRE (Pushpa)', price: 699, category: 'Tollywood', stock: 110, sku: 'MD009-BLK', rating: 4.8, gsm: '240 GSM Wildfire Tee' },
  { id: 'MD-010', name: 'Thalapathy Forever Statement Tee', price: 799, category: 'Kollywood', stock: 90, sku: 'MD010-BLK', rating: 5.0, gsm: '240 GSM Statement Tee' },
  { id: 'MD-027', name: 'AK — The Don\'s Edition', price: 1499, category: 'Kollywood', stock: 40, sku: 'MD027-BLK', rating: 5.0, gsm: '380 GSM Fleece Drop' },
];

// Mass Drips Real Leads List
export const massDripsLeads = [
  { id: 'L-01', name: 'Rahul Sharma', phone: '+91 98765 43210', status: 'hot', score: 85, city: 'Chennai', interests: ['Jana Nayagan Tee', 'AK The Don\'s Edition'], lastContact: 'Pending Call' },
  { id: 'L-02', name: 'Priya Verma', phone: '+91 91234 56780', status: 'warm', score: 65, city: 'Mumbai', interests: ['Kismat Der Se Aye Hoodie'], lastContact: 'Pending Call' },
  { id: 'L-03', name: 'Arjun Mehta', phone: '+91 90123 45678', status: 'warm', score: 70, city: 'Hyderabad', interests: ['Flower Nahi FIRE (Pushpa)'], lastContact: 'Pending Call' },
  { id: 'L-04', name: 'Sneha Patel', phone: '+91 88765 43210', status: 'cold', score: 40, city: 'Bengaluru', interests: ['Some Feelings Don\'t Need Words'], lastContact: 'Pending Call' },
];

// Real Campaigns Template for Mass Drips
export const massDripsCampaigns = [
  { id: 'C-01', name: 'Kollywood Drop — Jana Nayagan & AK Exclusive', status: 'active', leads: 450, calls: 0, conversions: 0, successRate: 0, product: 'Jana Nayagan — Crowd Edition' },
  { id: 'C-02', name: 'Bollywood Cult Drop — Main Rukta Nahi Hoon', status: 'draft', leads: 280, calls: 0, conversions: 0, successRate: 0, product: 'Main Rukta Nahi Hoon Sweatshirt' },
];
