/**
 * visualizationsMaster.js
 * Master Visualization View — 1 chart per page, sidebar-driven navigation.
 */
'use strict';

var VizMaster = (function () {
    var meta = {};
    var state = {
        category: 'numerical',
        chartType: null,
        chartIndex: 0,
        colX: null,
        colY: null,
        colZ: null,
    };

    var CATEGORY_CONFIG = {
        numerical:   { needsX: 'num', needsY: false, needsZ: false, menuId: 'menu-viz-num' },
        categorical: { needsX: 'cat', needsY: false, needsZ: false, menuId: 'menu-viz-cat' },
        bivariate:   { needsX: 'num', needsY: 'num', needsZ: 'bubble', menuId: 'menu-viz-biv' },
        catnum:      { needsX: 'cat', needsY: 'num', needsZ: false, menuId: 'menu-viz-catnum' },
        compare:     { needsX: false, needsY: false, needsZ: false, menuId: 'menu-viz-compare' },
    };

    var CHART_TYPES = {
        numerical:   ['histogram', 'boxplot', 'density', 'qq', 'violin'],
        categorical: ['bar', 'pie', 'count', 'pareto'],
        bivariate:   ['scatter', 'heatmap', 'regression', 'bubble', 'pair'],
        catnum:      ['box_by_cat', 'violin_by_cat', 'grouped_bar', 'strip'],
        compare:     ['violin_compare', 'grouped_bar_compare', 'parallel'],
    };

    function $(id) { return document.getElementById(id); }

    function isAvailable(category) {
        var n = (meta.num_cols || []).length;
        var c = (meta.cat_cols || []).length;
        var map = {
            numerical: n >= 1, categorical: c >= 1, bivariate: n >= 2,
            catnum: n >= 1 && c >= 1, compare: n >= 2,
        };
        return map[category] !== false;
    }

    function defaultColX(category) {
        if (category === 'categorical' || category === 'catnum') return (meta.cat_cols || [])[0] || null;
        return (meta.num_cols || [])[0] || null;
    }

    function defaultColY(category) {
        var nums = meta.num_cols || [];
        if (category === 'catnum') return nums[0] || null;
        if (category === 'bivariate') return nums[1] || nums[0] || null;
        return null;
    }

    function defaultColZ() {
        var nums = meta.num_cols || [];
        return nums[2] || nums[0] || null;
    }

    function populateDropdowns() {
        var cfg = CATEGORY_CONFIG[state.category] || {};
        var wrapX = $('viz-dd-x-wrap');
        var wrapY = $('viz-dd-y-wrap');
        var wrapZ = $('viz-dd-z-wrap');
        var selX = $('viz-col-x');
        var selY = $('viz-col-y');
        var selZ = $('viz-col-z');

        if (!selX) return;

        function fillSelect(sel, cols, selected) {
            sel.innerHTML = '';
            cols.forEach(function (c) {
                var opt = document.createElement('option');
                opt.value = c; opt.textContent = c;
                if (c === selected) opt.selected = true;
                sel.appendChild(opt);
            });
        }

        var showX = cfg.needsX && state.chartType !== 'heatmap' && state.chartType !== 'pair' && state.category !== 'compare';
        var showY = cfg.needsY && state.chartType !== 'heatmap' && state.chartType !== 'pair';
        var showZ = cfg.needsZ && state.chartType === 'bubble';

        if (wrapX) wrapX.style.display = showX ? 'flex' : 'none';
        if (wrapY) wrapY.style.display = showY ? 'flex' : 'none';
        if (wrapZ) wrapZ.style.display = showZ ? 'flex' : 'none';

        if (showX) {
            var colsX = cfg.needsX === 'cat' ? meta.cat_cols : meta.num_cols;
            if (!state.colX || colsX.indexOf(state.colX) < 0) state.colX = colsX[0];
            fillSelect(selX, colsX || [], state.colX);
        }
        if (showY) {
            if (!state.colY || meta.num_cols.indexOf(state.colY) < 0) state.colY = defaultColY(state.category);
            fillSelect(selY, meta.num_cols || [], state.colY);
        }
        if (showZ) {
            if (!state.colZ || meta.num_cols.indexOf(state.colZ) < 0) state.colZ = defaultColZ();
            fillSelect(selZ, meta.num_cols || [], state.colZ);
        }
    }

    function renderKpis(kpis) {
        var row = $('viz-kpi-row');
        if (!row) return;
        row.innerHTML = '';
        (kpis || []).slice(0, 5).forEach(function (k) {
            var card = document.createElement('div');
            card.className = 'viz-kpi-card';
            card.innerHTML =
                '<div class="viz-kpi-icon"><i class="fas ' + (k.icon || 'fa-chart-bar') + '"></i></div>' +
                '<div class="viz-kpi-body"><span class="viz-kpi-val">' + k.value + '</span>' +
                '<span class="viz-kpi-lbl">' + k.label + '</span></div>';
            row.appendChild(card);
        });
    }

    function showPlaceholder(msg) {
        var ph = $('viz-placeholder');
        var master = $('viz-master-chart');
        var controls = $('viz-master-controls');
        if (ph) { ph.style.display = 'flex'; ph.querySelector('p').textContent = msg; }
        if (master) master.style.display = 'none';
        if (controls) controls.style.display = 'none';
        $('viz-kpi-row').innerHTML = '';
    }

    function showChart() {
        var ph = $('viz-placeholder');
        var master = $('viz-master-chart');
        var controls = $('viz-master-controls');
        if (ph) ph.style.display = 'none';
        if (master) master.style.display = 'block';
        if (controls) controls.style.display = 'flex';
    }

    function updateNavLabel(data) {
        var el = $('viz-chart-type-label');
        var counter = $('viz-chart-counter');
        if (el) el.textContent = data.chart_label || '';
        if (counter && data.chart_total) {
            counter.textContent = (data.chart_index + 1) + ' / ' + data.chart_total;
        }
        var title = $('viz-category-title');
        var titles = {
            numerical: 'Numerical', categorical: 'Categorical',
            bivariate: 'Bivariate & Multi', catnum: 'Cat vs Num', compare: 'Comparison',
        };
        if (title) title.textContent = titles[state.category] || 'Visualizations';
    }

    function fetchAndRender() {
        if (!meta.filename) return;

        if (!isAvailable(state.category)) {
            var msgs = {
                numerical: 'Gunakan dataset dengan minimal 1 kolom numerik untuk mengaktifkan halaman ini.',
                categorical: 'Gunakan dataset dengan kolom kategorik untuk mengaktifkan halaman ini.',
                bivariate: 'Gunakan dataset dengan minimal 2 kolom numerik untuk mengaktifkan halaman ini.',
                catnum: 'Gunakan dataset dengan kolom numerik dan kategorik untuk mengaktifkan halaman ini.',
                compare: 'Gunakan dataset dengan minimal 2 kolom numerik untuk perbandingan.',
            };
            showPlaceholder(msgs[state.category] || 'Dataset tidak kompatibel.');
            return;
        }

        var types = CHART_TYPES[state.category] || [];
        if (!state.chartType) state.chartType = types[0];
        state.chartIndex = types.indexOf(state.chartType);
        if (state.chartIndex < 0) { state.chartIndex = 0; state.chartType = types[0]; }

        var params = new URLSearchParams({
            category: state.category,
            chart_type: state.chartType,
        });
        if (state.colX) params.set('col_x', state.colX);
        if (state.colY) params.set('col_y', state.colY);
        if (state.colZ) params.set('col_z', state.colZ);

        var chartEl = $('viz-master-plot');
        if (chartEl) chartEl.innerHTML = '<div class="viz-loading"><i class="fas fa-spinner fa-spin"></i> Loading chart...</div>';
        showChart();

        var requestUrl = '/api/viz-chart/' + encodeURIComponent(meta.filename) + '?' + params.toString();
        var timeoutId = null;
        var abortController = null;
        
        // Browser compatibility: gunakan AbortController jika tersedia
        if (typeof AbortController !== 'undefined') {
            abortController = new AbortController();
            timeoutId = setTimeout(function() {
                abortController.abort();
            }, 15000);
        } else {
            timeoutId = setTimeout(function() {
                if (chartEl) chartEl.innerHTML = '<div class="viz-error"><i class="fas fa-exclamation-circle"></i> Request timeout — periksa koneksi</div>';
            }, 15000);
        }

        var fetchOptions = {};
        if (abortController) {
            fetchOptions.signal = abortController.signal;
        }

        fetch(requestUrl, fetchOptions)
            .then(function (r) { 
                if (timeoutId) clearTimeout(timeoutId);
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json(); 
            })
            .then(function (data) {
                if (!data.ok) {
                    showPlaceholder(data.placeholder || 'Grafik tidak tersedia.');
                    renderKpis(data.kpis || []);
                    return;
                }
                renderKpis(data.kpis);
                updateNavLabel(data);
                state.chartType = data.chart_type;
                state.chartIndex = data.chart_index;

                if (typeof Plotly !== 'undefined' && data.chart) {
                    try {
                        var layout = Object.assign({}, data.chart.layout, {
                            autosize: true,
                            margin: { l: 54, r: 24, t: 48, b: 52 },
                        });
                        Plotly.react(chartEl, data.chart.data, layout, {
                            responsive: true,
                            displayModeBar: true,
                            displaylogo: false,
                            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                        }).then(function() {
                            // Chart rendered successfully
                        }).catch(function(plotlyErr) {
                            console.error('Plotly error:', plotlyErr);
                            if (chartEl) chartEl.innerHTML = '<div class="viz-error"><i class="fas fa-exclamation-circle"></i> Rendering failed</div>';
                        });
                    } catch (e) {
                        chartEl.innerHTML = '<div class="viz-error"><i class="fas fa-exclamation-circle"></i> Rendering error: ' + e.message + '</div>';
                    }
                }
            })
            .catch(function (err) {
                if (timeoutId) clearTimeout(timeoutId);
                var errMsg = 'Gagal memuat grafik';
                if (err.name === 'AbortError') {
                    errMsg = 'Request timeout — grafik terlalu besar atau koneksi lambat';
                } else if (err.message) {
                    errMsg += ': ' + err.message;
                }
                console.error('Viz fetch error:', err);
                if (chartEl) chartEl.innerHTML = '<div class="viz-error"><i class="fas fa-exclamation-circle"></i> ' + errMsg + '</div>';
            });
    }

    function nextChart() {
        var types = CHART_TYPES[state.category] || [];
        if (!types.length) return;
        state.chartIndex = (state.chartIndex + 1) % types.length;
        state.chartType = types[state.chartIndex];
        populateDropdowns();
        fetchAndRender();
    }

    function prevChart() {
        var types = CHART_TYPES[state.category] || [];
        if (!types.length) return;
        state.chartIndex = (state.chartIndex - 1 + types.length) % types.length;
        state.chartType = types[state.chartIndex];
        populateDropdowns();
        fetchAndRender();
    }

    function highlightSidebar() {
        document.querySelectorAll('.nav-item').forEach(function (li) { li.classList.remove('active'); });
        var cfg = CATEGORY_CONFIG[state.category];
        if (cfg && cfg.menuId) {
            var menu = document.getElementById(cfg.menuId);
            if (menu) menu.classList.add('active');
        }
        var parent = document.getElementById('menu-visualizations');
        if (parent) parent.classList.add('active');
    }

    function openCategory(category) {
        state.category = category || 'numerical';
        state.chartType = (CHART_TYPES[state.category] || [])[0];
        state.chartIndex = 0;
        state.colX = defaultColX(state.category);
        state.colY = defaultColY(state.category);
        state.colZ = defaultColZ();
        populateDropdowns();
        highlightSidebar();
        fetchAndRender();
    }

    function bindEvents() {
        var selX = $('viz-col-x');
        var selY = $('viz-col-y');
        var selZ = $('viz-col-z');
        if (selX) selX.addEventListener('change', function () { state.colX = selX.value; fetchAndRender(); });
        if (selY) selY.addEventListener('change', function () { state.colY = selY.value; fetchAndRender(); });
        if (selZ) selZ.addEventListener('change', function () { state.colZ = selZ.value; fetchAndRender(); });

        var btnNext = $('viz-btn-next');
        var btnPrev = $('viz-btn-prev');
        if (btnNext) btnNext.addEventListener('click', function (e) { e.stopPropagation(); nextChart(); });
        if (btnPrev) btnPrev.addEventListener('click', function (e) { e.stopPropagation(); prevChart(); });

        window.addEventListener('resize', function () {
            var el = $('viz-master-plot');
            if (el && el._fullLayout) Plotly.Plots.resize(el);
        });
    }

    function init(vizMeta) {
        meta = vizMeta || {};
        bindEvents();
    }

    function onTabShow() {
        if (!state.category) openCategory('numerical');
        else fetchAndRender();
    }

    return {
        init: init,
        openCategory: openCategory,
        onTabShow: onTabShow,
        nextChart: nextChart,
        prevChart: prevChart,
    };
})();

function openVizCategory(cat) {
    if (typeof switchTab === 'function') switchTab('visualizations');
    setTimeout(function () { VizMaster.openCategory(cat); }, 80);
}
