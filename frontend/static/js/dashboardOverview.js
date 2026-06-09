/**
 * dashboardOverview.js
 * Render & interaksi tab Dashboard Overview.
 *
 * SLOT MATRIX:
 *   ov_hbar        → Pareto Chart       (toggle cat_cols)
 *   ov_center      → Pie/Donut          (toggle cat_cols)
 *   ov_top_right   → TS (fixed) atau Scatter (toggle X & Y terpisah)
 *   ov_vbar_left   → Histogram          (toggle num_cols)
 *   ov_area_bottom → Box Plot           (toggle num_cols)
 *   ov_vbar_right  → Bar Chart          (toggle cat_cols)
 */
'use strict';

var OverviewDashboard = (function () {
    var data     = null;
    var rendered = new Set();

    var PLOTLY_CFG = {
        responsive     : true,
        displayModeBar : false,
        displaylogo    : false,
        scrollZoom     : false,
    };

    var SLOT_TITLE_PREFIX = {
        'ov_hbar'        : 'Pareto — ',
        'ov_center'      : 'Composition — ',
        'ov_vbar_left'   : 'Distribution — ',
        'ov_area_bottom' : 'Spread — ',
        'ov_vbar_right'  : 'Frequency — ',
    };

    // ── Layout patch ──────────────────────────────────────────────────────────
    function getLayoutPatch() {
        var dark = document.body.getAttribute('data-theme') === 'dark';
        return {
            paper_bgcolor : 'rgba(0,0,0,0)',
            plot_bgcolor  : 'rgba(0,0,0,0)',
            font          : {
                color  : dark ? '#c8d8f0' : '#2b3674',
                family : 'Inter, sans-serif',
                size   : 11,
            },
            margin    : { l: 44, r: 16, t: 38, b: 38 },
            hoverlabel: {
                bgcolor    : 'rgba(10,18,48,0.93)',
                bordercolor: 'rgba(100,160,235,0.45)',
                font       : { color: '#e8f4fc', size: 12 },
            },
        };
    }

    // ── Binary decode ─────────────────────────────────────────────────────────
    function _decodeBinaryField(field) {
        if (!field || typeof field !== 'object' || !field.bdata) return field;
        var dtype  = field.dtype || 'f8';
        var binary = atob(field.bdata);
        var len    = binary.length;
        var buf    = new ArrayBuffer(len);
        var view   = new Uint8Array(buf);
        for (var i = 0; i < len; i++) view[i] = binary.charCodeAt(i);
        var arr;
        if      (dtype === 'f8') arr = new Float64Array(buf);
        else if (dtype === 'f4') arr = new Float32Array(buf);
        else if (dtype === 'i4') arr = new Int32Array(buf);
        else if (dtype === 'i2') arr = new Int16Array(buf);
        else if (dtype === 'u4') arr = new Uint32Array(buf);
        else if (dtype === 'u1') arr = new Uint8Array(buf);
        else                     arr = new Float64Array(buf);
        return Array.from(arr);
    }

    function _decodeTrace(trace) {
        if (!trace || typeof trace !== 'object') return trace;
        var decoded = Object.assign({}, trace);
        ['x', 'y', 'z', 'values', 'labels', 'ids'].forEach(function (f) {
            if (decoded[f] && typeof decoded[f] === 'object' && decoded[f].bdata) {
                decoded[f] = _decodeBinaryField(decoded[f]);
            }
        });
        if (decoded.marker && decoded.marker.size &&
            typeof decoded.marker.size === 'object' && decoded.marker.size.bdata) {
            decoded.marker      = Object.assign({}, decoded.marker);
            decoded.marker.size = _decodeBinaryField(decoded.marker.size);
        }
        return decoded;
    }

    function _decodeChartData(chartObj) {
        if (!chartObj || !Array.isArray(chartObj.data)) return chartObj;
        return Object.assign({}, chartObj, {
            data: chartObj.data.map(_decodeTrace),
        });
    }
    // ── End binary decode ─────────────────────────────────────────────────────

    function drawSlot(slotId, chartJson, force) {
        if (!chartJson || typeof Plotly === 'undefined') return;
        var el = document.getElementById(slotId);
        if (!el) return;

        if (!force && rendered.has(slotId)) {
            Plotly.Plots.resize(el);
            return;
        }

        var decoded = _decodeChartData(chartJson);
        var layout  = Object.assign({}, decoded.layout || {}, getLayoutPatch());

        try { Plotly.purge(el); } catch (e) {}
        el.innerHTML = '';

        Plotly.react(el, decoded.data || [], layout, PLOTLY_CFG)
            .then(function () { rendered.add(slotId); })
            .catch(function (err) {
                console.warn('[Overview] Chart render failed:', slotId, err);
            });
    }

    function renderAll() {
        if (!data || !data.slots) return;
        Object.keys(data.slots).forEach(function (key) {
            var slot = data.slots[key];
            if (slot && slot.visible && slot.chart) {
                drawSlot(key, slot.chart, false);
            }
        });
    }

    // ── Title updater ─────────────────────────────────────────────────────────
    function _updateSlotTitle(slotId, text) {
        var el = document.getElementById(slotId + '-title');
        if (el) el.textContent = text;
    }

    // ── Toggle: regular (single dropdown per slot) ────────────────────────────
    function _bindRegularToggle(slotId, toggle) {
        var select = document.getElementById('toggle-' + slotId);
        if (!select || !toggle.charts) return;

        select.addEventListener('change', function () {
            var col   = select.value;
            var chart = toggle.charts[col];
            if (chart) {
                rendered.delete(slotId);
                drawSlot(slotId, chart, true);
                var prefix = SLOT_TITLE_PREFIX[slotId] || '';
                _updateSlotTitle(slotId, prefix + col);
            }
        });
    }

    // ── Toggle: scatter (dua dropdown X dan Y) ────────────────────────────────
    function _bindScatterToggle(toggle) {
        var selX = document.getElementById('scatter-col-x');
        var selY = document.getElementById('scatter-col-y');
        if (!selX || !selY) return;

        function _redraw() {
            var cx     = selX.value;
            var cy     = selY.value;
            var charts = toggle.charts || {};
            var chart  = (charts[cx] || {})[cy];
            if (chart) {
                rendered.delete('ov_top_right');
                drawSlot('ov_top_right', chart, true);
                _updateSlotTitle('ov_top_right', 'Scatter — ' + cx + ' × ' + cy);
            }
        }

        selX.addEventListener('change', function () {
            // Saat X berubah, cek apakah Y saat ini masih valid; jika Y == X, pindah ke pilihan lain
            var cx = selX.value;
            var cy = selY.value;
            if (cx === cy) {
                // Pilih Y pertama yang bukan cx
                var opts = Array.from(selY.options).map(function (o) { return o.value; });
                var alt  = opts.find(function (v) { return v !== cx; });
                if (alt) selY.value = alt;
            }
            _redraw();
        });

        selY.addEventListener('change', function () {
            var cy = selY.value;
            var cx = selX.value;
            if (cx === cy) {
                var opts = Array.from(selX.options).map(function (o) { return o.value; });
                var alt  = opts.find(function (v) { return v !== cy; });
                if (alt) selX.value = alt;
            }
            _redraw();
        });
    }

    function bindToggles() {
        if (!data || !data.toggle_data) return;

        Object.keys(data.toggle_data).forEach(function (slotId) {
            var toggle = data.toggle_data[slotId];
            if (!toggle) return;

            if (slotId === 'ov_top_right' && toggle.type === 'scatter') {
                _bindScatterToggle(toggle);
            } else {
                _bindRegularToggle(slotId, toggle);
            }
        });
    }

    // ── Stats Preview Tables ──────────────────────────────────────────────────
    function renderStatsPreview() {
        if (!data || !data.stats_preview) return;
        var sp = data.stats_preview;

        var numWrap = document.getElementById('ov-stats-num-wrap');
        if (numWrap && sp.num && sp.num.length > 0) {
            var numHtml =
                '<table class="ov-stats-table"><thead><tr>' +
                '<th>Column</th><th>Mean</th><th>Median</th>' +
                '<th>Std</th><th>Min</th><th>Max</th>' +
                '<th>Outliers</th><th>Missing</th>' +
                '</tr></thead><tbody>';
            sp.num.forEach(function (r) {
                var outCls = r.outliers > 0 ? 'ov-td-warn' : '';
                var misCls = r.missing  > 0 ? 'ov-td-warn' : '';
                numHtml +=
                    '<tr><td class="ov-td-col">' + r.col + '</td>' +
                    '<td>' + r.mean   + '</td><td>' + r.median + '</td>' +
                    '<td>' + r.std    + '</td><td>' + r.min    + '</td>' +
                    '<td>' + r.max    + '</td>' +
                    '<td class="' + outCls + '">' + r.outliers + '</td>' +
                    '<td class="' + misCls + '">' + r.missing  + '</td></tr>';
            });
            numHtml += '</tbody></table>';
            numWrap.innerHTML    = numHtml;
            numWrap.style.display = 'block';
            var nc = document.getElementById('ov-stats-num-card');
            if (nc) nc.style.display = 'block';
        }

        var catWrap = document.getElementById('ov-stats-cat-wrap');
        if (catWrap && sp.cat && sp.cat.length > 0) {
            var catHtml =
                '<table class="ov-stats-table"><thead><tr>' +
                '<th>Column</th><th>Unique</th><th>Mode</th>' +
                '<th>Mode %</th><th>Missing</th>' +
                '</tr></thead><tbody>';
            sp.cat.forEach(function (r) {
                var misCls = r.missing  > 0  ? 'ov-td-warn'   : '';
                var pctCls = r.mode_pct > 70 ? 'ov-td-danger' :
                             r.mode_pct > 50 ? 'ov-td-warn'   : '';
                catHtml +=
                    '<tr><td class="ov-td-col">' + r.col + '</td>' +
                    '<td>' + r.unique + '</td>' +
                    '<td class="ov-td-mode">' + r.mode + '</td>' +
                    '<td class="' + pctCls + '">' + r.mode_pct + '%</td>' +
                    '<td class="' + misCls + '">' + r.missing  + '</td></tr>';
            });
            catHtml += '</tbody></table>';
            catWrap.innerHTML    = catHtml;
            catWrap.style.display = 'block';
            var cc = document.getElementById('ov-stats-cat-card');
            if (cc) cc.style.display = 'block';
        }
    }

    // ── Click-through to Visualizations ──────────────────────────────────────
    function bindVizNavigation() {
        document.querySelectorAll('.ov-chart-slot[data-viz-tab]').forEach(function (el) {
            el.addEventListener('click', function (e) {
                if (e.target.closest('.ov-toggle-wrap')) return;
                goToVisualizations(
                    el.getAttribute('data-viz-tab'),
                    el.getAttribute('data-viz-sub')
                );
            });
        });
    }

    function goToVisualizations(tab, subTab) {
        if (tab === 'timeseries') {
            if (typeof switchTab === 'function') switchTab('timeseries');
            setTimeout(function () {
                if (typeof switchTsTab === 'function') switchTsTab('line');
            }, 90);
            return;
        }
        if (typeof openVizCategory === 'function') {
            openVizCategory(subTab || 'numerical');
        } else if (typeof switchTab === 'function') {
            switchTab('visualizations');
        }
    }

    // ── Public API ────────────────────────────────────────────────────────────
    function init(overviewPayload) {
        data = overviewPayload || null;
        if (!data) return;
        bindToggles();
        bindVizNavigation();
        var overviewTab = document.getElementById('tab-overview');
        if (overviewTab && overviewTab.classList.contains('active-tab')) {
            setTimeout(function () {
                renderAll();
                renderStatsPreview();
            }, 200);
        }
    }

    function onTabShow() {
        setTimeout(function () {
            renderAll();
            renderStatsPreview();
        }, 120);
    }

    function onResize() {
        rendered.forEach(function (slotId) {
            var el = document.getElementById(slotId);
            if (el && el._fullLayout && typeof Plotly !== 'undefined') {
                Plotly.Plots.resize(el);
            }
        });
    }

    return {
        init              : init,
        onTabShow         : onTabShow,
        onResize          : onResize,
        goToVisualizations: goToVisualizations,
        renderAll         : renderAll,
        renderStatsPreview: renderStatsPreview,
    };
})();

function goToVisualizations(tab, subTab) {
    OverviewDashboard.goToVisualizations(tab, subTab);
}