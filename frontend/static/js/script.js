/**
 * render_plots.js
 * Taruh di dalam <script> tag di template hasil.html / dashboard.html
 * Dipanggil setelah Plotly CDN dimuat.
 *
 * Cara pakai di Jinja2:
 *   <script>
 *     const PLOTS = {{ plots | tojson }};
 *   </script>
 *   <script src="{{ url_for('static', filename='js/render_plots.js') }}"></script>
 */

(function () {
  'use strict';

  /* ── Config default interaktif ────────────────────────────────────────── */
  const DEFAULT_CONFIG = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
    displaylogo: false,
    scrollZoom: false,
    toImageButtonOptions: { format: 'png', scale: 2 },
  };

  /* ── Map: plot key → element id di HTML ───────────────────────────────── */
  const PLOT_MAP = {
    // Grafik standar
    hist_num:        'chart-hist',
    bar_cat:         'chart-bar',
    box_cat_num:     'chart-box',
    heatmap:         'chart-heatmap',
    scatter_matrix:  'chart-scatter',
    pie_cat:         'chart-pie',
    // Grafik komparasi
    violin_compare:       'chart-violin',
    grouped_bar_compare:  'chart-grouped-bar',
    parallel_coords:      'chart-parallel',
  };

  /* ── Tab labels untuk section komparasi ───────────────────────────────── */
  const COMPARE_KEYS  = ['violin_compare', 'grouped_bar_compare', 'parallel_coords'];
  const COMPARE_LABELS = {
    violin_compare:      '🎻 Violin',
    grouped_bar_compare: '📊 Grouped Bar',
    parallel_coords:     '🔗 Parallel Coords',
  };

  /* ── Render satu plot ─────────────────────────────────────────────────── */
  function renderPlot(key, plotData) {
    const elId = PLOT_MAP[key];
    if (!elId) return;

    const el = document.getElementById(elId);
    if (!el) return;

    // Config: ambil dari data (diset di Python) atau fallback default
    const config = plotData._config || DEFAULT_CONFIG;
    delete plotData._config;  // jangan dikirim ke Plotly sebagai layout/data

    Plotly.newPlot(el, plotData.data, plotData.layout, config);

    /* ── Smooth hover: paksa unified hovermode & style via relayout ─────── */
    Plotly.relayout(el, {
      hovermode: 'x unified',
      hoverlabel: {
        bgcolor: 'rgba(10,20,50,0.92)',
        bordercolor: 'rgba(133,183,235,0.4)',
        font: { color: '#e8f3fc', size: 13, family: 'DM Sans, sans-serif' },
        namelength: -1,
      },
    });

    /* ── Animasi fade-in card parent ─────────────────────────────────────── */
    const card = el.closest('.viz-card');
    if (card) {
      card.style.opacity = '0';
      card.style.transform = 'translateY(16px)';
      requestAnimationFrame(() => {
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      });
    }
  }

  /* ── Render semua grafik ─────────────────────────────────────────────── */
  function renderAll(plots) {
    if (!plots || typeof plots !== 'object') return;
    Object.entries(plots).forEach(([key, data]) => {
      try { renderPlot(key, JSON.parse(JSON.stringify(data))); }
      catch (e) { console.warn(`[render_plots] ${key}:`, e); }
    });
  }

  /* ── Tab switching untuk section komparasi ───────────────────────────── */
  function initCompareTabs() {
    const tabBar = document.getElementById('compare-tab-bar');
    if (!tabBar) return;

    COMPARE_KEYS.forEach((key, i) => {
      const btn = document.createElement('button');
      btn.className = 'compare-tab' + (i === 0 ? ' active' : '');
      btn.textContent = COMPARE_LABELS[key];
      btn.dataset.key = key;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.compare-tab').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        COMPARE_KEYS.forEach(k => {
          const el = document.getElementById(PLOT_MAP[k]);
          if (el) el.closest('.viz-card').style.display = (k === key ? 'block' : 'none');
        });
        // Paksa Plotly resize setelah tab switch
        const active = document.getElementById(PLOT_MAP[key]);
        if (active) Plotly.Plots.resize(active);
      });
      tabBar.appendChild(btn);
    });

    // Sembunyikan semua kecuali tab pertama
    COMPARE_KEYS.slice(1).forEach(k => {
      const el = document.getElementById(PLOT_MAP[k]);
      if (el) el.closest('.viz-card').style.display = 'none';
    });
  }

  /* ── Init ────────────────────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof PLOTS !== 'undefined') {
      renderAll(PLOTS);
      initCompareTabs();
    } else {
      console.warn('[render_plots] Variabel PLOTS tidak ditemukan di halaman.');
    }
  });

  // Expose untuk penggunaan manual
  window.VizEngine = { renderAll, renderPlot, initCompareTabs };
})();