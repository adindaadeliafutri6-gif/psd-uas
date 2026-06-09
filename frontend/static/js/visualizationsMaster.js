'use strict';

/**
 * visualizationsMaster.js — Fixed & Complete
 *
 * Chart type names MUST match backend viz_engine.py CATEGORY_CHARTS exactly:
 *   numerical   : histogram, boxplot, density, qq, violin
 *   categorical : bar, pie, count, pareto
 *   bivariate   : scatter, heatmap, scatter_matrix, regression_plot, bubble_chart
 *   catnum      : box_cat_num, violin_cat_num, grouped_bar, strip_plot
 *   compare     : violin_compare, grouped_bar_compare, parallel_coords
 */
var VizMaster = (function () {

    var meta  = {};
    var state = {
        category   : 'numerical',
        chartType  : null,
        chartIndex : 0,
        colX       : null,
        colY       : null,
        colZ       : null,
        loading    : false,
    };

    var _activeController = null;

    var CHART_TYPES = {
        numerical   : ['histogram', 'boxplot', 'density', 'qq', 'violin'],
        categorical : ['bar', 'pie', 'count', 'pareto'],
        bivariate   : ['scatter', 'heatmap', 'scatter_matrix', 'regression_plot', 'bubble_chart'],
        catnum      : ['box_cat_num', 'violin_cat_num', 'grouped_bar', 'strip_plot'],
        compare     : ['violin_compare', 'grouped_bar_compare', 'parallel_coords'],
    };

    var CHART_LABELS = {
        histogram           : 'Histogram + KDE',
        boxplot             : 'Box Plot',
        density             : 'Density Plot (KDE)',
        qq                  : 'QQ Plot — Normality',
        violin              : 'Violin Plot',
        bar                 : 'Bar Chart',
        pie                 : 'Donut / Pie Chart',
        count               : 'Count Plot',
        pareto              : 'Pareto Chart',
        scatter             : 'Scatter Plot',
        heatmap             : 'Correlation Heatmap',
        scatter_matrix      : 'Pair Plot / Scatter Matrix',
        regression_plot     : 'Regression + 95% CI',
        bubble_chart        : 'Bubble Chart',
        box_cat_num         : 'Boxplot by Category',
        violin_cat_num      : 'Violin by Category',
        grouped_bar         : 'Grouped Bar Chart',
        strip_plot          : 'Strip Plot',
        violin_compare      : 'Violin Comparison',
        grouped_bar_compare : 'Mean Std Comparison',
        parallel_coords     : 'Parallel Coordinates',
    };

    var CATEGORY_CONFIG = {
        numerical   : { needsX: 'num', needsY: false, needsZ: false },
        categorical : { needsX: 'cat', needsY: false, needsZ: false },
        bivariate   : { needsX: 'num', needsY: 'num', needsZ: 'num' },
        catnum      : { needsX: 'cat', needsY: 'num', needsZ: false },
        compare     : { needsX: false, needsY: false, needsZ: false },
    };

    var NO_DROPDOWN_CHARTS = {
        heatmap             : true,
        scatter_matrix      : true,
        parallel_coords     : true,
        violin_compare      : true,
        grouped_bar_compare : true,
    };

    function $$(id) { return document.getElementById(id); }

    // ── Binary decode: handle Plotly's bdata+dtype format ──────────────────────
    // Plotly serialises large numeric arrays as base64 binary to save bandwidth.
    // We must decode them back to JS arrays before passing to Plotly.newPlot.
    function _decodeBinaryField(field) {
        if (!field || typeof field !== 'object' || !field.bdata) return field;

        var dtype  = field.dtype || 'f8';
        var binary = atob(field.bdata);
        var len    = binary.length;
        var buf    = new ArrayBuffer(len);
        var view   = new Uint8Array(buf);
        for (var i = 0; i < len; i++) view[i] = binary.charCodeAt(i);

        var arr;
        if      (dtype === 'f8')  arr = new Float64Array(buf);
        else if (dtype === 'f4')  arr = new Float32Array(buf);
        else if (dtype === 'i4')  arr = new Int32Array(buf);
        else if (dtype === 'i2')  arr = new Int16Array(buf);
        else if (dtype === 'i1')  arr = new Int8Array(buf);
        else if (dtype === 'u4')  arr = new Uint32Array(buf);
        else if (dtype === 'u2')  arr = new Uint16Array(buf);
        else if (dtype === 'u1')  arr = new Uint8Array(buf);
        else                      arr = new Float64Array(buf); // fallback

        // Convert TypedArray to plain JS array for Plotly compatibility
        return Array.from(arr);
    }

    function _decodeTrace(trace) {
        if (!trace || typeof trace !== 'object') return trace;
        var decoded = Object.assign({}, trace);

        // ── Standard x/y/z fields ────────────────────────────────────────────
        var fields = ['x', 'y', 'z', 'values', 'labels', 'ids',
                      'open', 'high', 'low', 'close', 'lat', 'lon'];
        fields.forEach(function (f) {
            if (decoded[f] && typeof decoded[f] === 'object' && decoded[f].bdata) {
                decoded[f] = _decodeBinaryField(decoded[f]);
            }
        });

        // ── marker.size binary ────────────────────────────────────────────────
        if (decoded.marker && decoded.marker.size &&
            typeof decoded.marker.size === 'object' && decoded.marker.size.bdata) {
            decoded.marker = Object.assign({}, decoded.marker);
            decoded.marker.size = _decodeBinaryField(decoded.marker.size);
        }

        // ── parcoords: dimensions[i].values binary ────────────────────────────
        if (decoded.type === 'parcoords' && Array.isArray(decoded.dimensions)) {
            decoded.dimensions = decoded.dimensions.map(function (dim) {
                if (!dim || typeof dim !== 'object') return dim;
                var d = Object.assign({}, dim);
                if (d.values && typeof d.values === 'object' && d.values.bdata) {
                    d.values = _decodeBinaryField(d.values);
                }
                return d;
            });
        }

        // ── parcoords: line.color binary ──────────────────────────────────────
        if (decoded.line && typeof decoded.line === 'object') {
            var line = Object.assign({}, decoded.line);
            if (line.color && typeof line.color === 'object' && line.color.bdata) {
                line.color = _decodeBinaryField(line.color);
            }
            decoded.line = line;
        }

        return decoded;
    }

    function _decodeChartData(chartObj) {
        if (!chartObj || !Array.isArray(chartObj.data)) return chartObj;
        return Object.assign({}, chartObj, {
            data: chartObj.data.map(_decodeTrace),
        });
    }
    // ── End binary decode ──────────────────────────────────────────────────────

    function isAvailable(category) {
        var n = (meta.num_cols || []).length;
        var c = (meta.cat_cols || []).length;
        var map = {
            numerical   : n >= 1,
            categorical : c >= 1,
            bivariate   : n >= 2,
            catnum      : n >= 1 && c >= 1,
            compare     : n >= 2,
        };
        return map[category] !== false;
    }

    function defaultX(cat) {
        var cfg = CATEGORY_CONFIG[cat] || {};
        if (cfg.needsX === 'cat') return (meta.cat_cols || [])[0] || null;
        return (meta.num_cols || [])[0] || null;
    }
    function defaultY(cat) {
        var nums = meta.num_cols || [];
        if (cat === 'catnum')    return nums[0] || null;
        if (cat === 'bivariate') return nums[1] || nums[0] || null;
        return null;
    }
    function defaultZ() {
        var nums = meta.num_cols || [];
        return nums[2] || nums[1] || nums[0] || null;
    }

    function populateDropdowns() {
        var cfg  = CATEGORY_CONFIG[state.category] || {};
        var ct   = state.chartType;
        var noDD = NO_DROPDOWN_CHARTS[ct] || false;
        var isCompare = (state.category === 'compare');

        var wrapX = $$('viz-dd-x-wrap');
        var wrapY = $$('viz-dd-y-wrap');
        var wrapZ = $$('viz-dd-z-wrap');
        var selX  = $$('viz-col-x');
        var selY  = $$('viz-col-y');
        var selZ  = $$('viz-col-z');
        if (!selX) return;

        var showX = !!(cfg.needsX) && !noDD && !isCompare;
        var showY = !!(cfg.needsY) && !noDD;
        var showZ = !!(cfg.needsZ) && (ct === 'bubble_chart');

        if (wrapX) wrapX.style.display = showX ? 'flex' : 'none';
        if (wrapY) wrapY.style.display = showY ? 'flex' : 'none';
        if (wrapZ) wrapZ.style.display = showZ ? 'flex' : 'none';

        function fill(sel, cols, selected) {
            sel.innerHTML = '';
            (cols || []).forEach(function (c) {
                var opt = document.createElement('option');
                opt.value = c; opt.textContent = c;
                if (c === selected) opt.selected = true;
                sel.appendChild(opt);
            });
        }

        if (showX && selX) {
            var colsX = cfg.needsX === 'cat' ? (meta.cat_cols || []) : (meta.num_cols || []);
            if (!state.colX || colsX.indexOf(state.colX) < 0) state.colX = colsX[0] || null;
            fill(selX, colsX, state.colX);
        }
        if (showY && selY) {
            var colsY = meta.num_cols || [];
            if (!state.colY || colsY.indexOf(state.colY) < 0) state.colY = defaultY(state.category);
            fill(selY, colsY, state.colY);
        }
        if (showZ && selZ) {
            var colsZ = meta.num_cols || [];
            if (!state.colZ || colsZ.indexOf(state.colZ) < 0) state.colZ = defaultZ();
            fill(selZ, colsZ, state.colZ);
        }

        if (state.category === 'bivariate' && state.chartType === 'bubble_chart') {
            var nums = meta.num_cols || [];
            if (!state.colZ || nums.indexOf(state.colZ) < 0) state.colZ = defaultZ();
            if (selZ && (!selZ.value || selZ.value === 'null')) {
                fill(selZ, nums, state.colZ);
            }
        }
    }

    function renderKpis(kpis) {
        var row = $$('viz-kpi-row');
        if (!row) return;
        row.innerHTML = '';
        (kpis || []).slice(0, 5).forEach(function (k) {
            var card = document.createElement('div');
            card.className = 'viz-kpi-card';
            card.innerHTML =
                '<div class="viz-kpi-icon"><i class="fas ' + (k.icon || 'fa-chart-bar') + '"></i></div>' +
                '<div class="viz-kpi-body">' +
                '<span class="viz-kpi-val">' + k.value + '</span>' +
                '<span class="viz-kpi-lbl">' + k.label + '</span>' +
                '</div>';
            row.appendChild(card);
        });
    }

    function updateLabel(data) {
        var el  = $$('viz-chart-type-label');
        var ctr = $$('viz-chart-counter');
        var types = CHART_TYPES[state.category] || [];
        if (el)  el.textContent  = CHART_LABELS[state.chartType] || (data && data.chart_label) || '';
        if (ctr) {
            var idx = (data && data.chart_index != null) ? data.chart_index : types.indexOf(state.chartType);
            var tot = (data && data.chart_total)  ? data.chart_total  : types.length;
            ctr.textContent = (idx + 1) + ' / ' + tot;
        }
        var titles = {
            numerical   : 'Numerical',
            categorical : 'Categorical',
            bivariate   : 'Bivariate & Multi',
            catnum      : 'Cat vs Num',
            compare     : 'Comparison',
        };
        var titleEl = $$('viz-category-title');
        if (titleEl) titleEl.textContent = titles[state.category] || 'Visualizations';
    }

    function showPlaceholder(msg) {
        var ph   = $$('viz-placeholder');
        var mc   = $$('viz-master-chart');
        var ctrl = $$('viz-master-controls');
        if (ph) {
            ph.style.display = 'flex';
            var p = ph.querySelector('p');
            if (p) p.textContent = msg || 'Dataset tidak kompatibel.';
        }
        if (mc)   mc.style.display   = 'none';
        if (ctrl) ctrl.style.display = 'none';
        var kr = $$('viz-kpi-row');
        if (kr) kr.innerHTML = '';
    }

    function showChart() {
        var ph   = $$('viz-placeholder');
        var mc   = $$('viz-master-chart');
        var ctrl = $$('viz-master-controls');
        if (ph)   ph.style.display   = 'none';
        if (mc)   mc.style.display   = 'block';
        if (ctrl) ctrl.style.display = 'flex';
    }

    function setLoading(plotEl) {
        if (!plotEl) return;
        plotEl.innerHTML =
            '<div class="viz-loading" style="display:flex;align-items:center;justify-content:center;height:100%;">' +
            '<i class="fas fa-spinner fa-spin" style="font-size:1.5rem;color:#7EA9FF;"></i>' +
            '<span style="font-size:.9rem;color:#7EA9FF;margin-left:10px;">Loading chart...</span>' +
            '</div>';
    }

    function setError(plotEl, msg) {
        if (!plotEl) return;
        plotEl.innerHTML =
            '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;' +
            'height:100%;padding:24px;text-align:center;">' +
            '<i class="fas fa-exclamation-circle" style="font-size:2rem;color:#ee5d50;margin-bottom:12px;"></i>' +
            '<p style="color:#ee5d50;margin-bottom:14px;font-size:.9rem;">' + (msg || 'Gagal memuat grafik') + '</p>' +
            '<button onclick="VizMaster.retry()" style="padding:7px 18px;border-radius:8px;' +
            'border:1px solid rgba(126,169,255,.4);background:rgba(126,169,255,.12);' +
            'color:#c8d8f0;cursor:pointer;font-family:inherit;font-size:.8rem;">' +
            '<i class="fas fa-redo"></i> Coba Lagi</button>' +
            '</div>';
    }

    function fetchAndRender(isRetry) {
        if (!meta.filename) return;

        if (!isAvailable(state.category)) {
            var MSGS = {
                numerical   : 'Gunakan dataset dengan minimal 1 kolom numerik.',
                categorical : 'Gunakan dataset dengan kolom kategorik.',
                bivariate   : 'Gunakan dataset dengan minimal 2 kolom numerik.',
                catnum      : 'Gunakan dataset dengan kolom numerik dan kategorik.',
                compare     : 'Gunakan dataset dengan minimal 2 kolom numerik.',
            };
            showPlaceholder(MSGS[state.category] || 'Dataset tidak kompatibel.');
            return;
        }

        var types = CHART_TYPES[state.category] || [];
        if (!state.chartType || types.indexOf(state.chartType) < 0) {
            state.chartType  = types[0];
            state.chartIndex = 0;
        } else {
            state.chartIndex = types.indexOf(state.chartType);
        }

        if (_activeController) try { _activeController.abort(); } catch (e) {}
        var controller = null, signal = undefined;
        if (typeof AbortController !== 'undefined') {
            controller = new AbortController();
            _activeController = controller;
            signal = controller.signal;
        }

        var params = new URLSearchParams({
            category  : state.category,
            chart_type: state.chartType,
        });
        if (state.colX && !NO_DROPDOWN_CHARTS[state.chartType]) params.set('col_x', state.colX);
        if (state.colY && !NO_DROPDOWN_CHARTS[state.chartType]) params.set('col_y', state.colY);
        if (state.colZ && state.chartType === 'bubble_chart')   params.set('col_z', state.colZ);

        var url = '/api/viz-chart/' + encodeURIComponent(meta.filename) + '?' + params.toString();

        showChart();
        var plotEl = $$('viz-master-plot');
        setLoading(plotEl);
        state.loading = true;

        var tid = setTimeout(function () {
            if (controller) try { controller.abort(); } catch (e) {}
        }, 25000);

        fetch(url, signal ? { signal: signal } : {})
            .then(function (r) {
                clearTimeout(tid);
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (data) {
                state.loading = false;
                _activeController = null;

                if (!data.ok) {
                    showPlaceholder(data.placeholder || 'Grafik tidak tersedia.');
                    renderKpis(data.kpis || []);
                    return;
                }

                renderKpis(data.kpis || []);
                state.chartType  = data.chart_type  || state.chartType;
                state.chartIndex = data.chart_index != null ? data.chart_index : state.chartIndex;
                updateLabel(data);

                if (typeof Plotly === 'undefined') {
                    setError(plotEl, 'Plotly.js belum dimuat.');
                    return;
                }
                if (!data.chart) {
                    setError(plotEl, 'Data grafik kosong dari server.');
                    return;
                }

                // ── Decode binary data sebelum render ────────────────────────
                var chartDecoded = _decodeChartData(data.chart);
                // ────────────────────────────────────────────────────────────

                try { Plotly.purge(plotEl); } catch (e) {}
                plotEl.innerHTML = '';

                var layout = Object.assign({}, chartDecoded.layout || {}, {
                    autosize: true,
                    margin  : { l: 54, r: 24, t: 56, b: 52 },
                });

                Plotly.newPlot(plotEl, chartDecoded.data || [], layout, {
                    responsive             : true,
                    displayModeBar         : true,
                    displaylogo            : false,
                    modeBarButtonsToRemove : ['lasso2d', 'select2d', 'autoScale2d'],
                    toImageButtonOptions   : { format: 'png', scale: 2 },
                }).catch(function (err) {
                    setError(plotEl, 'Rendering error: ' + err.message);
                });
            })
            .catch(function (err) {
                clearTimeout(tid);
                state.loading = false;
                _activeController = null;
                if (err.name === 'AbortError') return;
                if (!isRetry) {
                    setTimeout(function () { fetchAndRender(true); }, 900);
                    return;
                }
                setError(plotEl, 'Gagal memuat grafik: ' + (err.message || 'Unknown error'));
            });
    }

    function nextChart() {
        var types = CHART_TYPES[state.category] || [];
        if (!types.length) return;
        state.chartIndex = (state.chartIndex + 1) % types.length;
        state.chartType  = types[state.chartIndex];
        populateDropdowns();
        fetchAndRender();
    }

    function prevChart() {
        var types = CHART_TYPES[state.category] || [];
        if (!types.length) return;
        state.chartIndex = (state.chartIndex - 1 + types.length) % types.length;
        state.chartType  = types[state.chartIndex];
        populateDropdowns();
        fetchAndRender();
    }

    function highlightSidebar(category) {
        document.querySelectorAll('.nav-sub-item').forEach(function (li) { li.classList.remove('active'); });
        var MAP = {
            numerical   : 'menu-viz-num',
            categorical : 'menu-viz-cat',
            bivariate   : 'menu-viz-biv',
            catnum      : 'menu-viz-catnum',
            compare     : 'menu-viz-compare',
        };
        var el = document.getElementById(MAP[category]);
        if (el) el.classList.add('active');

        var accBody = document.getElementById('acc-viz');
        var accBtn  = document.getElementById('acc-viz-btn');
        if (accBody && !accBody.classList.contains('open')) {
            accBody.classList.add('open');
            if (accBtn) accBtn.classList.add('open');
        }
    }

    function openCategory(category) {
        if (state.loading && _activeController) try { _activeController.abort(); } catch (e) {}
        state.category   = category || 'numerical';
        var types        = CHART_TYPES[state.category] || [];
        state.chartType  = types[0] || null;
        state.chartIndex = 0;
        state.colX       = defaultX(state.category);
        state.colY       = defaultY(state.category);
        state.colZ       = defaultZ();
        populateDropdowns();
        updateLabel(null);
        highlightSidebar(state.category);
        fetchAndRender();
    }

    function bindEvents() {
        var selX = $$('viz-col-x');
        var selY = $$('viz-col-y');
        var selZ = $$('viz-col-z');
        if (selX) selX.addEventListener('change', function () { state.colX = selX.value; fetchAndRender(); });
        if (selY) selY.addEventListener('change', function () { state.colY = selY.value; fetchAndRender(); });
        if (selZ) selZ.addEventListener('change', function () { state.colZ = selZ.value; fetchAndRender(); });

        var btnNext = $$('viz-btn-next');
        var btnPrev = $$('viz-btn-prev');
        if (btnNext) btnNext.addEventListener('click', function (e) { e.stopPropagation(); nextChart(); });
        if (btnPrev) btnPrev.addEventListener('click', function (e) { e.stopPropagation(); prevChart(); });

        document.addEventListener('keydown', function (e) {
            var vizTab = document.getElementById('tab-visualizations');
            if (!vizTab || vizTab.style.display === 'none') return;
            if (e.key === 'ArrowRight') nextChart();
            if (e.key === 'ArrowLeft')  prevChart();
        });

        var _rsz;
        window.addEventListener('resize', function () {
            clearTimeout(_rsz);
            _rsz = setTimeout(function () {
                var el = $$('viz-master-plot');
                if (el && el._fullLayout && typeof Plotly !== 'undefined') Plotly.Plots.resize(el);
            }, 200);
        });
    }

    function init(vizMeta) {
        meta = vizMeta || {};
        bindEvents();
    }

    function onTabShow() {
        if (!meta.filename) return;
        var plotEl = $$('viz-master-plot');
        var hasPlotly = plotEl && plotEl._fullLayout && plotEl.data && plotEl.data.length > 0;
        if (!hasPlotly) {
            openCategory(state.category || 'numerical');
        } else if (plotEl && typeof Plotly !== 'undefined') {
            Plotly.Plots.resize(plotEl);
        }
    }

    function retry() { fetchAndRender(false); }

    return {
        init        : init,
        openCategory: openCategory,
        onTabShow   : onTabShow,
        nextChart   : nextChart,
        prevChart   : prevChart,
        retry       : retry,
    };
})();

function openVizCategory(cat) {
    if (typeof switchTab === 'function') switchTab('visualizations');
    setTimeout(function () { VizMaster.openCategory(cat); }, 80);
}