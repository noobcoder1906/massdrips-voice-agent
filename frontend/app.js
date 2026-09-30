/**
 * VoxSales Client Dashboard Application Logic
 */

const API_BASE = 'http://localhost:8000';
let currentTenantId = '6abd262975108fde8f7b524c';

document.addEventListener('DOMContentLoaded', () => {
  loadTenants();
  loadOverviewData();
  loadLeads();
  loadProducts();
  loadCampaigns();
});

function switchView(viewId) {
  document.querySelectorAll('.view-container').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  const targetView = document.getElementById(`view-${viewId}`);
  if (targetView) targetView.classList.add('active');

  const titleMap = {
    'overview': 'Overview & Analytics',
    'campaigns': 'Campaign Hub',
    'live-call': 'Live Call Monitor',
    'call-logs': 'Call Transcripts',
    'leads': 'Lead Directory',
    'products': 'Product Catalog',
    'agent-config': 'Agent Persona Configuration'
  };

  document.getElementById('pageTitle').textContent = titleMap[viewId] || 'Dashboard';
}

async function loadTenants() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/tenants`);
    const data = await res.json();
    if (data.success && data.data && data.data.length > 0) {
      const select = document.getElementById('tenantSelect');
      select.innerHTML = '';
      data.data.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = `${t.name} (${t.plan.toUpperCase()})`;
        select.appendChild(opt);
      });
      currentTenantId = select.value;
    }
  } catch (err) {
    console.warn('Using default tenant ID');
  }
}

function onTenantChanged() {
  currentTenantId = document.getElementById('tenantSelect').value;
  loadOverviewData();
  loadLeads();
  loadProducts();
  loadCampaigns();
}

async function loadOverviewData() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/leads?tenant_id=${currentTenantId}`);
    const data = await res.json();
    if (data.success && data.data) {
      const tbody = document.getElementById('overviewTableBody');
      tbody.innerHTML = '';
      const recent = data.data.slice(0, 5);
      recent.forEach(lead => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${lead.name}</strong></td>
          <td>${lead.phone}</td>
          <td><span class="badge badge-green">${lead.status}</span></td>
          <td><strong>${lead.lead_score || 0} / 100</strong></td>
          <td>Just now</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error('Failed to load overview data', err);
  }
}

async function loadLeads() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/leads?tenant_id=${currentTenantId}`);
    const data = await res.json();
    if (data.success && data.data) {
      const tbody = document.getElementById('leadsTableBody');
      const simSelect = document.getElementById('simLeadSelect');
      tbody.innerHTML = '';
      if (simSelect) simSelect.innerHTML = '';

      data.data.forEach(l => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${l.name}</strong></td>
          <td>${l.phone}</td>
          <td><span class="badge badge-blue">${l.status}</span></td>
          <td>${l.lead_score || 0}</td>
          <td>${(l.interests || []).join(', ') || 'General'}</td>
        `;
        tbody.appendChild(tr);

        if (simSelect) {
          const opt = document.createElement('option');
          opt.value = l.id;
          opt.textContent = `${l.name} (${l.phone})`;
          simSelect.appendChild(opt);
        }
      });
    }
  } catch (err) {
    console.error('Failed to load leads', err);
  }
}

async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/products?tenant_id=${currentTenantId}`);
    const data = await res.json();
    if (data.success && data.data) {
      const tbody = document.getElementById('productsTableBody');
      tbody.innerHTML = '';
      data.data.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${p.name}</strong></td>
          <td>₹ ${p.price}</td>
          <td>${p.category || 'General'}</td>
          <td><span class="badge ${p.in_stock ? 'badge-green' : 'badge-amber'}">${p.in_stock ? 'In Stock' : 'Out of Stock'}</span></td>
          <td><code>${p.sku || '-'}</code></td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error('Failed to load products', err);
  }
}

async function loadCampaigns() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/campaigns?tenant_id=${currentTenantId}`);
    const data = await res.json();
    if (data.success && data.data) {
      const tbody = document.getElementById('campaignsTableBody');
      tbody.innerHTML = '';
      data.data.forEach(c => {
        const isRunning = c.status === 'running';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${c.name}</strong></td>
          <td><span class="badge ${isRunning ? 'badge-green' : 'badge-purple'}">${c.status}</span></td>
          <td>${c.total_leads || 0}</td>
          <td>${c.calls_made || 0}</td>
          <td>${c.conversions || 0}</td>
          <td>
            <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="toggleCampaign('${c.id}', '${isRunning ? 'pause' : 'start'}')">
              ${isRunning ? '⏸️ Pause' : '▶️ Start'}
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error('Failed to load campaigns', err);
  }
}

async function toggleCampaign(campaignId, action) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/campaigns/${campaignId}/${action}?tenant_id=${currentTenantId}`, {
      method: 'POST'
    });
    const data = await res.json();
    if (data.success) {
      loadCampaigns();
    }
  } catch (err) {
    alert(`Failed to ${action} campaign`);
  }
}

function savePersona(e) {
  e.preventDefault();
  alert('Agent Persona updated successfully!');
}

function simulateLiveCall() {
  const leadSelect = document.getElementById('simLeadSelect');
  const leadName = leadSelect ? leadSelect.options[leadSelect.selectedIndex]?.text : 'Rahul Sharma';

  const box = document.getElementById('liveTranscript');
  box.innerHTML += `
    <div class="chat-bubble chat-agent">
      <strong>Aria (Mass Drips Agent):</strong> "Namaste ${leadName.split(' ')[0]} ji! Main Mass Drips se Aria bol rahi hoon. Aapne hamara Drip Hoodie check kiya tha?"
    </div>
  `;
  box.scrollTop = box.scrollHeight;
}
