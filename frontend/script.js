// ── CONFIG ────────────────────────────────────────────────────────────
const API = 'http://localhost:5000';

// ── STATE ─────────────────────────────────────────────────────────────
let currentSessionId = null;
let currentDatasetId = null;
let charts = {};
let isTyping = false;

// ── INIT ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadHistory();
  initDragDrop();
  applyTheme(localStorage.getItem('theme') || 'dark');
});

// ── PAGE ROUTING ──────────────────────────────────────────────────────
function showPage(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');
  document.getElementById(`nav-${page}`).classList.add('active');

  const titles = { chat: 'AI Retail Assistant', dashboard: 'Trend Dashboard', upload: 'Upload Dataset' };
  document.getElementById('topbar-title').textContent = titles[page];

  if (page === 'dashboard') refreshDashboard();
}

// ── THEME ─────────────────────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : 'dark');
  const btn = document.getElementById('theme-btn');
  btn.textContent = theme === 'light' ? '🌙 Dark' : '☀️ Light';
  localStorage.setItem('theme', theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  applyTheme(current === 'light' ? 'dark' : 'light');
}

// ── SIDEBAR ───────────────────────────────────────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ── CHAT ──────────────────────────────────────────────────────────────
function startNewChat() {
  currentSessionId = null;
  const area = document.getElementById('chat-area');
  area.innerHTML = `
    <div class="welcome-screen" id="welcome-screen">
      <div class="welcome-icon">🛍️</div>
      <div class="welcome-title">Retail Trend AI</div>
      <div class="welcome-subtitle">Ask me about fashion trends, retail analytics, demand forecasts, or upload a dataset for deep insights.</div>
      <div class="suggestion-chips">
        <div class="chip" onclick="sendChip(this)">📈 What categories are trending?</div>
        <div class="chip" onclick="sendChip(this)">🥇 Top selling products this season</div>
        <div class="chip" onclick="sendChip(this)">🌍 Which region has highest demand?</div>
        <div class="chip" onclick="sendChip(this)">🔮 Predict demand for next quarter</div>
        <div class="chip" onclick="sendChip(this)">📉 Any declining product categories?</div>
        <div class="chip" onclick="sendChip(this)">💡 Recommend restocking priorities</div>
      </div>
    </div>`;
  showPage('chat');
}

function sendChip(el) {
  const text = el.textContent.replace(/^[^\w]+/, '').trim();
  document.getElementById('message-input').value = text;
  sendMessage();
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

async function sendMessage() {
  const input = document.getElementById('message-input');
  const text = input.value.trim();
  if (!text || isTyping) return;

  // Hide welcome screen
  const ws = document.getElementById('welcome-screen');
  if (ws) ws.remove();

  input.value = '';
  input.style.height = 'auto';
  setSendDisabled(true);

  appendMessage('user', text);
  const typingEl = appendTyping();
  scrollBottom();
  isTyping = true;

  try {
    const res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: currentSessionId })
    });

    // Handle non-JSON responses (e.g. HTML 500 error pages from server)
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      typingEl.remove();
      appendMessage('bot', `⚠️ Server error (HTTP ${res.status}). The backend returned an unexpected response. Please check Render logs.`);
      isTyping = false;
      setSendDisabled(false);
      return;
    }

    const data = await res.json();
    typingEl.remove();

    if (data.error) {
      appendMessage('bot', '⚠️ ' + data.error);
    } else {
      appendMessage('bot', data.reply);
      currentSessionId = data.session_id;
      loadHistory();
    }
  } catch (err) {
    typingEl.remove();
    appendMessage('bot', `⚠️ Could not reach the server. Error: ${err.message}`);
  }

  isTyping = false;
  setSendDisabled(false);
  scrollBottom();
}

function setSendDisabled(v) {
  document.getElementById('send-btn').disabled = v;
}

function appendMessage(role, content) {
  const area = document.getElementById('chat-area');
  const isUser = role === 'user';
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const row = document.createElement('div');
  row.className = `message-row ${isUser ? 'user' : ''}`;
  row.innerHTML = `
    <div class="avatar ${isUser ? 'user' : 'bot'}">${isUser ? '👤' : 'AI'}</div>
    <div class="bubble ${isUser ? 'user' : 'bot'}">
      ${formatMarkdown(content)}
      <div class="bubble-time">${time}</div>
    </div>`;
  area.appendChild(row);
  return row;
}

function appendTyping() {
  const area = document.getElementById('chat-area');
  const row = document.createElement('div');
  row.className = 'message-row';
  row.innerHTML = `
    <div class="avatar bot">AI</div>
    <div class="bubble bot">
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  area.appendChild(row);
  return row;
}

function formatMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(108,99,255,0.15);padding:1px 5px;border-radius:4px;font-size:13px">$1</code>')
    .replace(/\n/g, '<br>');
}

function scrollBottom() {
  const area = document.getElementById('chat-area');
  setTimeout(() => { area.scrollTop = area.scrollHeight; }, 50);
}

// ── HISTORY ───────────────────────────────────────────────────────────
async function loadHistory() {
  try {
    const res = await fetch(`${API}/history`);
    const sessions = await res.json();
    renderHistory(sessions);
  } catch (_) {}
}

function renderHistory(sessions) {
  const list = document.getElementById('history-list');
  if (!sessions.length) {
    list.innerHTML = `<div class="empty-state" style="padding:20px"><div class="empty-icon" style="font-size:24px">💭</div><p style="font-size:12px">No chats yet</p></div>`;
    return;
  }
  list.innerHTML = sessions.map(s => `
    <div class="history-item ${s.id === currentSessionId ? 'active' : ''}" onclick="loadSession(${s.id})">
      <span style="font-size:13px">💬</span>
      <span class="history-item-text">${escHtml(s.title)}</span>
      <button class="history-delete" onclick="deleteSession(event,${s.id})" title="Delete">✕</button>
    </div>`).join('');
}

async function loadSession(id) {
  currentSessionId = id;
  showPage('chat');
  try {
    const res = await fetch(`${API}/history/${id}`);
    const messages = await res.json();
    const area = document.getElementById('chat-area');
    area.innerHTML = '';
    messages.forEach(m => appendMessage(m.role === 'assistant' ? 'bot' : 'user', m.content));
    scrollBottom();
    loadHistory();
  } catch (err) {
    toast('Could not load session', 'error');
  }
}

async function deleteSession(e, id) {
  e.stopPropagation();
  await fetch(`${API}/history/${id}`, { method: 'DELETE' });
  if (currentSessionId === id) startNewChat();
  loadHistory();
}

// ── UPLOAD ────────────────────────────────────────────────────────────
function initDragDrop() {
  const zone = document.getElementById('upload-zone');
  if (!zone) return;
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) uploadFile(file);
}

async function clearDatasetContext() {
  try {
    await fetch(`${API}/clear-context`, { method: 'POST' });

    // Reset state
    currentDatasetId = null;

    // --- Topbar ---
    document.getElementById('dataset-indicator').classList.add('hidden');
    document.getElementById('dataset-name').textContent = 'Dataset loaded';

    // --- Upload page ---
    document.getElementById('dataset-info').style.display = 'none';
    document.getElementById('action-btns').classList.add('hidden');
    document.getElementById('info-filename').textContent = '';
    document.getElementById('info-rows').textContent = '';
    document.getElementById('info-cols').textContent = '';
    document.getElementById('info-format').textContent = '';
    document.getElementById('info-column-tags').innerHTML = '';

    // --- Dashboard stats ---
    ['stat-records','stat-units','stat-products','stat-categories','stat-range','stat-region']
      .forEach(id => { const el = document.getElementById(id); if (el) el.textContent = '—'; });

    // --- Dashboard charts ---
    ['chart-timeseries','chart-products','chart-category','chart-seasonal']
      .forEach(id => {
        if (charts[id]) { charts[id].destroy(); delete charts[id]; }
        const canvas = document.getElementById(id);
        if (canvas) { const ctx = canvas.getContext('2d'); ctx.clearRect(0, 0, canvas.width, canvas.height); }
      });

    // --- Predictions & trend scores ---
    const pred = document.getElementById('predictions-list');
    if (pred) pred.innerHTML = `<div class="empty-state"><div class="empty-icon">🔮</div><p>Run analysis to see predictions</p></div>`;
    const trends = document.getElementById('trend-scores');
    if (trends) trends.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Upload and analyze a dataset to see trend scores.</p></div>`;

    toast('🗑️ Dataset cleared successfully', 'success');
  } catch (err) {
    toast('Failed to clear dataset', 'error');
  }
}

async function uploadFile(file) {
  const allowed = ['text/csv', 'application/json', 'text/plain'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['csv', 'json'].includes(ext)) {
    toast('Only CSV and JSON files are supported', 'error');
    return;
  }

  showProgress(true);
  animateProgress(0, 60, 800);

  const fd = new FormData();
  fd.append('file', file);

  try {
    const res = await fetch(`${API}/upload`, { method: 'POST', body: fd });
    const data = await res.json();

    animateProgress(60, 100, 400);
    await sleep(400);
    showProgress(false);

    if (data.error) { toast(data.error, 'error'); return; }

    currentDatasetId = data.dataset_id;
    showDatasetInfo(data);
    document.getElementById('action-btns').classList.remove('hidden');
    document.getElementById('dataset-indicator').classList.remove('hidden');
    document.getElementById('dataset-name').textContent = data.filename;
    toast(`✅ ${data.filename} uploaded — ${data.row_count.toLocaleString()} rows`, 'success');
  } catch (err) {
    showProgress(false);
    toast('Upload failed — is the server running?', 'error');
  }
}

function showDatasetInfo(data) {
  document.getElementById('dataset-info').style.display = 'block';
  document.getElementById('info-filename').textContent = data.filename;
  document.getElementById('info-rows').textContent = data.row_count.toLocaleString();
  document.getElementById('info-cols').textContent = data.columns.length;
  document.getElementById('info-format').textContent = data.filename.endsWith('.json') ? 'JSON' : 'CSV';
  document.getElementById('info-column-tags').innerHTML = data.columns.map(c =>
    `<span class="column-tag">${c}</span>`).join('');
}

function showProgress(show) {
  document.getElementById('upload-progress').style.display = show ? 'flex' : 'none';
  document.getElementById('progress-bar').style.width = show ? '0%' : '0%';
}

function animateProgress(from, to, duration) {
  const bar = document.getElementById('progress-bar');
  const start = performance.now();
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    bar.style.width = (from + (to - from) * p) + '%';
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

async function runAnalysis() {
  const btn = document.getElementById('analyze-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Analyzing…';

  try {
    const body = currentDatasetId ? { dataset_id: currentDatasetId } : {};
    const res = await fetch(`${API}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { toast(data.error, 'error'); return; }
    toast('✅ Analysis complete! Switching to Dashboard…', 'success');
    setTimeout(() => showPage('dashboard'), 800);
  } catch (err) {
    toast('Analysis failed — server error', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🚀 Run Trend Analysis';
  }
}

function loadSampleData() {
  // Trigger download of sample CSV
  const a = document.createElement('a');
  a.href = '/data/sample_retail_data.csv';
  a.download = 'sample_retail_data.csv';
  a.click();
}

// ── DASHBOARD ─────────────────────────────────────────────────────────
async function refreshDashboard() {
  try {
    const res = await fetch(`${API}/dashboard`);
    const data = await res.json();
    if (data.error) {
      showDashboardEmpty(data.error);
      return;
    }
    renderDashboard(data);
  } catch (err) {
    showDashboardEmpty('Could not connect to backend.');
  }
}

function showDashboardEmpty(msg) {
  document.getElementById('stat-records').textContent = '—';
  toast(msg + ' Please upload a dataset first.', 'error');
}

function renderDashboard(data) {
  // Stats
  const s = data.summary || {};
  document.getElementById('stat-records').textContent = (s.total_records || 0).toLocaleString();
  document.getElementById('stat-units').textContent = (s.total_units_sold || 0).toLocaleString();
  document.getElementById('stat-products').textContent = s.unique_products || '—';
  document.getElementById('stat-categories').textContent = s.unique_categories || '—';
  document.getElementById('stat-range').textContent = s.date_range || '—';
  document.getElementById('stat-region').textContent = s.top_region || '—';

  // Time series
  if (data.time_series) {
    renderChart('chart-timeseries', 'line', data.time_series.labels, data.time_series.values, {
      gradient: true, fill: true, label: 'Units Sold'
    });
  }

  // Top products
  if (data.top_products) {
    renderChart('chart-products', 'bar', data.top_products.labels, data.top_products.values, {
      label: 'Units Sold', horizontal: false
    });
  }

  // Category
  if (data.category_demand) {
    renderChart('chart-category', 'doughnut', data.category_demand.labels, data.category_demand.values, {
      label: 'Units'
    });
  }

  // Seasonal
  if (data.seasonal) {
    const order = ['Spring', 'Summer', 'Autumn', 'Winter'];
    const labels = [], values = [];
    order.forEach(s => {
      const idx = data.seasonal.labels.indexOf(s);
      if (idx !== -1) { labels.push(s); values.push(data.seasonal.values[idx]); }
    });
    renderChart('chart-seasonal', 'polarArea', labels, values, { label: 'Units' });
  }

  // Predictions
  renderPredictions(data.predictions || []);

  // Trend scores
  renderTrendScores(data.trend_scores || []);
}

function renderChart(id, type, labels, values, opts = {}) {
  const canvas = document.getElementById(id);
  if (!canvas) return;

  if (charts[id]) { charts[id].destroy(); }

  const ctx = canvas.getContext('2d');
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const textColor = isDark ? '#8b87b8' : '#5a5690';
  const gridColor = isDark ? 'rgba(108,99,255,0.08)' : 'rgba(108,99,255,0.12)';
  const accent = '#6c63ff';
  const accent2 = '#ff6b9d';
  const accent3 = '#00d4aa';

  const palette = [accent, accent2, accent3, '#f7c94e', '#60a5fa', '#a78bfa', '#34d399', '#fb923c'];

  let dataset = {
    label: opts.label || 'Value',
    data: values,
    borderRadius: type === 'bar' ? 6 : 0,
  };

  if (type === 'line') {
    dataset.borderColor = accent;
    dataset.borderWidth = 2.5;
    dataset.pointBackgroundColor = accent;
    dataset.pointRadius = 4;
    dataset.pointHoverRadius = 6;
    dataset.tension = 0.4;
    if (opts.fill) {
      dataset.fill = true;
      const grad = ctx.createLinearGradient(0, 0, 0, 240);
      grad.addColorStop(0, 'rgba(108,99,255,0.25)');
      grad.addColorStop(1, 'rgba(108,99,255,0)');
      dataset.backgroundColor = grad;
    }
  } else if (type === 'bar') {
    dataset.backgroundColor = values.map((_, i) => palette[i % palette.length] + 'cc');
    dataset.borderColor = values.map((_, i) => palette[i % palette.length]);
    dataset.borderWidth = 1;
  } else if (type === 'doughnut') {
    dataset.backgroundColor = palette.slice(0, values.length).map(c => c + 'dd');
    dataset.borderColor = palette.slice(0, values.length);
    dataset.borderWidth = 2;
  } else if (type === 'polarArea') {
    dataset.backgroundColor = palette.slice(0, values.length).map(c => c + 'aa');
    dataset.borderColor = palette.slice(0, values.length);
    dataset.borderWidth = 1;
  }

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: ['doughnut', 'polarArea'].includes(type),
        labels: { color: textColor, font: { family: "'DM Sans'" }, padding: 16, boxWidth: 12 }
      },
      tooltip: {
        backgroundColor: isDark ? '#1a1a2e' : '#fff',
        titleColor: isDark ? '#e8e6ff' : '#1a1a2e',
        bodyColor: textColor,
        borderColor: 'rgba(108,99,255,0.3)',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: ctx => ` ${ctx.parsed.y !== undefined ? ctx.parsed.y.toLocaleString() : ctx.parsed.toLocaleString()} units`
        }
      }
    },
  };

  if (!['doughnut', 'polarArea'].includes(type)) {
    commonOptions.scales = {
      x: { ticks: { color: textColor, font: { size: 11 } }, grid: { color: gridColor } },
      y: { ticks: { color: textColor, font: { size: 11 } }, grid: { color: gridColor } }
    };
  }

  charts[id] = new Chart(ctx, { type, data: { labels, datasets: [dataset] }, options: commonOptions });
}

function renderPredictions(predictions) {
  const el = document.getElementById('predictions-list');
  if (!predictions.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-icon">🔮</div><p>No predictions available. Run analysis first.</p></div>`;
    return;
  }
  el.innerHTML = predictions.map(p => `
    <div class="prediction-item">
      <div class="pred-arrow">${p.direction === 'rise' ? '📈' : '📉'}</div>
      <div class="pred-name">${escHtml(p.product)}</div>
      <div class="pred-change ${p.direction === 'rise' ? 'up' : 'down'}">
        ${p.direction === 'rise' ? '+' : '-'}${p.change_pct}%
      </div>
      <div class="pred-conf">${p.confidence}</div>
    </div>`).join('');
}

function renderTrendScores(scores) {
  const el = document.getElementById('trend-scores');
  if (!scores.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Upload and analyze a dataset to see trend scores.</p></div>`;
    return;
  }
  const max = scores[0]?.score || 100;
  el.innerHTML = scores.map(s => `
    <div class="trend-score-item">
      <div class="trend-score-name">${escHtml(s.product)}</div>
      <div class="trend-score-bar-wrap">
        <div class="trend-score-bar" style="width:${(s.score / max * 100).toFixed(1)}%"></div>
      </div>
      <div class="trend-score-num">${s.score}</div>
    </div>`).join('');
}

// ── PDF DOWNLOAD ──────────────────────────────────────────────────────
async function downloadReport() {
  try {
    const res = await fetch(`${API}/report/download`);
    if (!res.ok) { toast('Run analysis first to generate a report', 'error'); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'retail_trend_report.pdf'; a.click();
    URL.revokeObjectURL(url);
    toast('✅ Report downloaded', 'success');
  } catch (err) {
    toast('Report download failed', 'error');
  }
}

// ── TOAST ─────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ── UTILS ─────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
