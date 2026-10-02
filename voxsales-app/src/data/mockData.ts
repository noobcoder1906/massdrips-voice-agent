export interface StatItem {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  icon: string;
}

export const mockStats: StatItem[] = [
  { label: 'Total Calls Made', value: '12,847', change: '+18.4%', trend: 'up', icon: 'phone' },
  { label: 'Conversion Rate', value: '32.4%', change: '+3.2%', trend: 'up', icon: 'target' },
  { label: 'Avg Call Duration', value: '1m 45s', change: '-8s', trend: 'up', icon: 'clock' },
  { label: 'Cost Per Call', value: '₹1.20', change: '-70%', trend: 'up', icon: 'rupee' },
];

export const mockCampaigns = [
  { id: '1', name: 'Monsoon Sale Outreach', status: 'active', leads: 1240, calls: 987, conversions: 312, successRate: 31.6, product: 'Drip Hoodies' },
  { id: '2', name: 'Festive Season Push', status: 'active', leads: 850, calls: 612, conversions: 198, successRate: 32.4, product: 'Premium Tees' },
  { id: '3', name: 'Re-engagement Wave', status: 'paused', leads: 560, calls: 420, conversions: 87, successRate: 20.7, product: 'Cargo Pants' },
  { id: '4', name: 'New Collection Launch', status: 'draft', leads: 2100, calls: 0, conversions: 0, successRate: 0, product: 'Winter Collection' },
  { id: '5', name: 'Cart Abandonment Recovery', status: 'active', leads: 430, calls: 380, conversions: 156, successRate: 41.1, product: 'Mixed Products' },
  { id: '6', name: 'VIP Customer Upsell', status: 'completed', leads: 200, calls: 200, conversions: 88, successRate: 44.0, product: 'Limited Edition' },
];

export const mockLeads = [
  { id: 'L001', name: 'Rahul Sharma', phone: '+91 98765 43210', status: 'hot', score: 92, city: 'Mumbai', interests: ['Hoodies', 'Streetwear'], lastContact: '2 hours ago' },
  { id: 'L002', name: 'Priya Mehta', phone: '+91 87654 32109', status: 'warm', score: 74, city: 'Delhi', interests: ['Premium Tees', 'Joggers'], lastContact: '1 day ago' },
  { id: 'L003', name: 'Arjun Nair', phone: '+91 76543 21098', status: 'hot', score: 88, city: 'Bangalore', interests: ['Cargo Pants', 'Caps'], lastContact: '30 min ago' },
  { id: 'L004', name: 'Sneha Patil', phone: '+91 65432 10987', status: 'cold', score: 41, city: 'Pune', interests: ['Accessories'], lastContact: '5 days ago' },
  { id: 'L005', name: 'Vikram Singh', phone: '+91 54321 09876', status: 'warm', score: 67, city: 'Hyderabad', interests: ['Hoodies', 'Tees'], lastContact: '3 hours ago' },
  { id: 'L006', name: 'Ananya Roy', phone: '+91 43210 98765', status: 'hot', score: 95, city: 'Chennai', interests: ['Limited Edition', 'Streetwear'], lastContact: '15 min ago' },
  { id: 'L007', name: 'Rohit Gupta', phone: '+91 32109 87654', status: 'cold', score: 28, city: 'Kolkata', interests: ['Basics'], lastContact: '2 weeks ago' },
  { id: 'L008', name: 'Kavya Krishnan', phone: '+91 21098 76543', status: 'warm', score: 71, city: 'Ahmedabad', interests: ['Joggers', 'Caps'], lastContact: '6 hours ago' },
];

export const mockCallLogs = [
  { id: 'CALL-001', lead: 'Rahul Sharma', phone: '+91 98765 43210', duration: '2m 12s', outcome: 'converted', sentiment: 'positive', score: 91, date: 'Today, 10:24 AM', transcript: 'Agent Aria greeted warmly and offered a Drip Hoodie deal...' },
  { id: 'CALL-002', lead: 'Priya Mehta', phone: '+91 87654 32109', duration: '1m 45s', outcome: 'interested', sentiment: 'positive', score: 78, date: 'Today, 09:15 AM', transcript: 'Customer showed strong interest in Premium Tees...' },
  { id: 'CALL-003', lead: 'Arjun Nair', phone: '+91 76543 21098', duration: '3m 02s', outcome: 'converted', sentiment: 'very_positive', score: 95, date: 'Today, 08:30 AM', transcript: 'Excellent sales conversation, closed Cargo Pants deal...' },
  { id: 'CALL-004', lead: 'Sneha Patil', phone: '+91 65432 10987', duration: '0m 45s', outcome: 'not_interested', sentiment: 'negative', score: 22, date: 'Yesterday, 04:12 PM', transcript: 'Customer declined, requested do-not-call listing...' },
  { id: 'CALL-005', lead: 'Vikram Singh', phone: '+91 54321 09876', duration: '1m 58s', outcome: 'callback', sentiment: 'neutral', score: 55, date: 'Yesterday, 02:30 PM', transcript: 'Customer requested callback for evening timing...' },
  { id: 'CALL-006', lead: 'Ananya Roy', phone: '+91 43210 98765', duration: '4m 11s', outcome: 'converted', sentiment: 'very_positive', score: 98, date: 'Yesterday, 11:00 AM', transcript: 'Highest value order placed — Limited Edition bundle...' },
];

export const mockProducts = [
  { id: 'P001', name: 'Drip Hoodie — Classic Black', price: 1899, category: 'Hoodies', stock: 245, sku: 'DH-BLK-M', rating: 4.8, orders: 1240 },
  { id: 'P002', name: 'Premium Tee — Washed White', price: 799, category: 'T-Shirts', stock: 580, sku: 'PT-WHT-L', rating: 4.6, orders: 2340 },
  { id: 'P003', name: 'Cargo Pants — Olive Green', price: 2499, category: 'Bottoms', stock: 120, sku: 'CP-OLV-32', rating: 4.7, orders: 890 },
  { id: 'P004', name: 'Street Cap — Bone White', price: 599, category: 'Accessories', stock: 890, sku: 'SC-BWH-OS', rating: 4.5, orders: 3120 },
  { id: 'P005', name: 'Jogger Set — Charcoal', price: 1699, category: 'Bottomwear', stock: 340, sku: 'JS-CHR-M', rating: 4.9, orders: 780 },
  { id: 'P006', name: 'Limited Edition Collab Tee', price: 3299, category: 'Limited', stock: 50, sku: 'LE-CLB-M', rating: 5.0, orders: 145 },
];

export const mockChartData = [
  { month: 'Apr', calls: 420, conversions: 98, revenue: 186000 },
  { month: 'May', calls: 680, conversions: 156, revenue: 294000 },
  { month: 'Jun', calls: 920, conversions: 234, revenue: 441000 },
  { month: 'Jul', calls: 1240, conversions: 398, revenue: 740000 },
  { month: 'Aug', calls: 1560, conversions: 512, revenue: 970000 },
  { month: 'Sep', calls: 1890, conversions: 623, revenue: 1180000 },
  { month: 'Oct', calls: 2120, conversions: 698, revenue: 1320000 },
];

export const mockSentimentData = [
  { name: 'Very Positive', value: 38, color: '#00e599' },
  { name: 'Positive', value: 32, color: '#34d399' },
  { name: 'Neutral', value: 18, color: '#6366f1' },
  { name: 'Negative', value: 9, color: '#f59e0b' },
  { name: 'Very Negative', value: 3, color: '#ef4444' },
];

export const mockActivity = [
  { id: 1, type: 'call_completed', text: 'Ananya Roy — Converted (₹3,299 order)', time: '15 min ago', status: 'success' },
  { id: 2, type: 'campaign_launched', text: 'Monsoon Sale Outreach — 1,240 leads queued', time: '1 hour ago', status: 'info' },
  { id: 3, type: 'call_completed', text: 'Arjun Nair — Converted (₹2,499 order)', time: '2 hours ago', status: 'success' },
  { id: 4, type: 'lead_added', text: '48 new leads imported from Shopify export', time: '3 hours ago', status: 'info' },
  { id: 5, type: 'call_failed', text: 'Sneha Patil — Declined, added to DNC list', time: '4 hours ago', status: 'warning' },
  { id: 6, type: 'call_completed', text: 'Rahul Sharma — Converted (₹1,899 order)', time: '5 hours ago', status: 'success' },
  { id: 7, type: 'webhook_triggered', text: 'WhatsApp follow-up sent to 12 warm leads', time: '6 hours ago', status: 'info' },
  { id: 8, type: 'agent_updated', text: 'Agent "Aria" persona updated — Friendly & Energetic', time: 'Yesterday', status: 'neutral' },
];

export const mockFavorites = [
  { id: 'C1', type: 'campaign', name: 'Festive Season Push', status: 'active', metric: '32.4% conv.', savedAt: '2 days ago' },
  { id: 'C2', type: 'lead', name: 'Ananya Roy', status: 'hot', metric: 'Score: 95', savedAt: '3 days ago' },
  { id: 'C3', type: 'product', name: 'Limited Edition Collab Tee', status: 'low_stock', metric: '₹3,299', savedAt: '1 week ago' },
  { id: 'C4', type: 'campaign', name: 'VIP Customer Upsell', status: 'completed', metric: '44.0% conv.', savedAt: '1 week ago' },
  { id: 'C5', type: 'lead', name: 'Rahul Sharma', status: 'hot', metric: 'Score: 92', savedAt: '2 weeks ago' },
];
