/* ══════════════════════════════════════════════════════════
   SocialHub — analytics.js
   Chart.js powered analytics dashboard
══════════════════════════════════════════════════════════ */

let lineChart    = null;
let platformDonut = null;

const PLATFORM_COLORS = {
  instagram: '#E1306C',
  tiktok:    '#69C9D0',
  facebook:  '#1877F2',
  youtube:   '#FF0000',
};

document.addEventListener('DOMContentLoaded', () => {

  // ── Load overall stats ──────────────────────────────
  loadSummary();

  // ── Post selector → load chart ──────────────────────
  const postSel    = document.getElementById('postSelector');
  const daysRange  = document.getElementById('daysRange');
  const metricSel  = document.getElementById('metricSelector');

  postSel?.addEventListener('change',  refreshPostChart);
  daysRange?.addEventListener('change', refreshPostChart);
  metricSel?.addEventListener('change', refreshPostChart);

  // Check if URL has ?post_id=…
  const params = new URLSearchParams(window.location.search);
  const postId = params.get('post_id');
  if (postId && postSel) {
    postSel.value = postId;
    refreshPostChart();
  }

});


/* ── Summary stats ─────────────────────────────────────── */
async function loadSummary() {
  try {
    const data = await apiFetch('/analytics/api/summary');
    setEl('totalViews',    fmtNum(data.views    || 0));
    setEl('totalLikes',    fmtNum(data.likes    || 0));
    setEl('totalComments', fmtNum(data.comments || 0));
    setEl('totalShares',   fmtNum(data.shares   || 0));
  } catch (e) {
    console.warn('Summary fetch error:', e);
  }
}


/* ── Post chart ────────────────────────────────────────── */
async function refreshPostChart() {
  const postId = document.getElementById('postSelector')?.value;
  const days   = document.getElementById('daysRange')?.value   || 30;
  const metric = document.getElementById('metricSelector')?.value || 'views';

  const placeholder  = document.getElementById('chartPlaceholder');
  const chartWrapper = document.getElementById('chartWrapper');

  if (!postId) {
    placeholder?.style.setProperty('display', '');
    chartWrapper?.style.setProperty('display', 'none');
    return;
  }

  placeholder?.style.setProperty('display', 'none');
  chartWrapper?.style.setProperty('display', 'block');

  try {
    const data = await apiFetch(`/analytics/api/post/${postId}?days=${days}`);
    renderPostChart(data, metric);
    renderPlatformDonut(data, metric);
  } catch (e) {
    console.error('Post analytics error:', e);
  }
}


function renderPostChart(data, metric) {
  const ctx = document.getElementById('analyticsChart');
  if (!ctx) return;

  // Collect all unique dates across all platforms
  const allDates = [...new Set(
    Object.values(data).flatMap(d => d.labels)
  )].sort();

  const datasets = Object.entries(data).map(([platform, d]) => {
    const color = PLATFORM_COLORS[platform] || '#A78BFA';
    const values = allDates.map(date => {
      const idx = d.labels.indexOf(date);
      return idx >= 0 ? d[metric][idx] : 0;
    });
    return {
      label:           platform.charAt(0).toUpperCase() + platform.slice(1),
      data:            values,
      borderColor:     color,
      backgroundColor: color + '22',
      borderWidth:     2,
      pointRadius:     3,
      tension:         0.4,
      fill:            true,
    };
  });

  lineChart?.destroy();
  lineChart = new Chart(ctx, {
    type: 'line',
    data: { labels: allDates, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {
          grid:  { color: 'rgba(255,255,255,.06)' },
          ticks: { color: '#94A3B8', maxTicksLimit: 10 },
        },
        y: {
          grid:  { color: 'rgba(255,255,255,.06)' },
          ticks: { color: '#94A3B8', callback: v => fmtNum(v) },
          beginAtZero: true,
        },
      },
      plugins: {
        legend: { labels: { color: '#E2E8F0', boxWidth: 12, padding: 16 } },
        tooltip: {
          backgroundColor: '#1A1A2E',
          borderColor: 'rgba(255,255,255,.1)',
          borderWidth: 1,
          titleColor: '#E2E8F0',
          bodyColor: '#94A3B8',
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${fmtNum(ctx.parsed.y)}`,
          },
        },
      },
    },
  });
}


function renderPlatformDonut(data, metric) {
  const ctx = document.getElementById('platformChart');
  const legendEl = document.getElementById('platformLegend');
  if (!ctx) return;

  const labels  = [];
  const values  = [];
  const colors  = [];
  const bgColors = [];

  Object.entries(data).forEach(([platform, d]) => {
    const total = d[metric].reduce((a, b) => a + b, 0);
    labels.push(platform.charAt(0).toUpperCase() + platform.slice(1));
    values.push(total);
    const c = PLATFORM_COLORS[platform] || '#A78BFA';
    colors.push(c);
    bgColors.push(c + 'BB');
  });

  platformDonut?.destroy();
  platformDonut = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data:            values,
        backgroundColor: bgColors,
        borderColor:     colors,
        borderWidth:     2,
        hoverOffset:     6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1A1A2E',
          borderColor: 'rgba(255,255,255,.1)',
          borderWidth: 1,
          titleColor: '#E2E8F0',
          bodyColor: '#94A3B8',
          callbacks: {
            label: ctx => `${ctx.label}: ${fmtNum(ctx.parsed)}`,
          },
        },
      },
    },
  });

  // Custom legend
  if (legendEl) {
    const total = values.reduce((a, b) => a + b, 0) || 1;
    legendEl.innerHTML = labels.map((lbl, i) => `
      <div class="d-flex align-items-center justify-content-between mb-2">
        <div class="d-flex align-items-center gap-2">
          <span style="width:10px;height:10px;border-radius:50%;background:${colors[i]};display:inline-block"></span>
          <span class="text-muted small">${lbl}</span>
        </div>
        <span class="fw-semibold small">${fmtNum(values[i])}</span>
      </div>
    `).join('');
  }
}


/* ── Platform account analytics ─────────────────────────── */
window.loadPlatformAnalytics = async function (accountId, platform, name) {
  const days   = document.getElementById('daysRange')?.value   || 30;
  const metric = document.getElementById('metricSelector')?.value || 'views';
  const placeholder  = document.getElementById('chartPlaceholder');
  const chartWrapper = document.getElementById('chartWrapper');

  placeholder?.style.setProperty('display', 'none');
  chartWrapper?.style.setProperty('display', 'block');

  try {
    const data  = await apiFetch(`/analytics/api/platform/${accountId}?days=${days}`);
    const color = PLATFORM_COLORS[platform] || '#A78BFA';
    const ctx   = document.getElementById('analyticsChart');
    if (!ctx) return;

    lineChart?.destroy();
    lineChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [{
          label:           `${name} (${platform})`,
          data:            data[metric] || [],
          backgroundColor: color + '55',
          borderColor:     color,
          borderWidth:     2,
          borderRadius:    6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: 'rgba(255,255,255,.06)' }, ticks: { color: '#94A3B8' } },
          y: { grid: { color: 'rgba(255,255,255,.06)' }, ticks: { color: '#94A3B8', callback: v => fmtNum(v) }, beginAtZero: true },
        },
        plugins: {
          legend: { labels: { color: '#E2E8F0' } },
          tooltip: {
            backgroundColor: '#1A1A2E',
            borderColor: 'rgba(255,255,255,.1)',
            borderWidth: 1,
            callbacks: { label: ctx => `${ctx.dataset.label}: ${fmtNum(ctx.parsed.y)}` },
          },
        },
      },
    });
  } catch (e) {
    console.error('Platform analytics error:', e);
  }
};


/* ── Helpers ───────────────────────────────────────────── */
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
