/**
 * dashboardOverview.js
 * Render & interaksi tab Dashboard Overview (grid KPI + 6 chart slots).
 */
'use strict';

var OverviewDashboard = (function () {
    var data = null;
    var rendered = new Set();

    var PLOTLY_CFG = {
        responsive: true,
        displayModeBar: false,
        displaylogo: false,
        scrollZoom: false,
    };

    function getLayoutPatch() {
        var dark = document.body.getAttribute('data-theme') === 'dark';
        return {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: dark ? '#c8d8f0' : '#2b3674', family: 'Inter, sans-serif', size: 11 },
            margin: { l: 40, r: 16, t: 36, b: 36 },
            hoverlabel: {
                bgcolor: 'rgba(10,18,48,0.93)',
                bordercolor: 'rgba(100,160,235,0.45)',
                font: { color: '#e8f4fc', size: 12 },
            },
        };
    }

    function drawSlot(slotId, chartJson, force) {
        if (!chartJson || typeof Plotly === 'undefined') return;
        var el = document.getElementById(slotId);
        if (!el) return;
        if (!force && rendered.has(slotId)) {
            Plotly.Plots.resize(el);
            return;
        }
        var layout = Object.assign({}, chartJson.layout || {}, getLayoutPatch());
        Plotly.react(el, chartJson.data || [], layout, PLOTLY_CFG).then(function () {
            rendered.add(slotId);
        }).catch(function (err) {
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

    function bindToggles() {
        if (!data || !data.toggle_data) return;

        Object.keys(data.toggle_data).forEach(function (slotId) {
            var toggle = data.toggle_data[slotId];
            var select = document.getElementById('toggle-' + slotId);
            if (!select || !toggle.charts) return;

            select.addEventListener('change', function () {
                var col = select.value;
                var chart = toggle.charts[col];
                if (chart) {
                    rendered.delete(slotId);
                    drawSlot(slotId, chart, true);
                }
            });
        });
    }

    function bindVizNavigation() {
        document.querySelectorAll('.ov-chart-slot[data-viz-tab]').forEach(function (el) {
            el.addEventListener('click', function (e) {
                if (e.target.closest('.ov-toggle-wrap')) return;
                goToVisualizations(el.getAttribute('data-viz-tab'), el.getAttribute('data-viz-sub'));
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

    function init(overviewPayload) {
        data = overviewPayload || null;
        if (!data) return;

        bindToggles();
        bindVizNavigation();

        var overviewTab = document.getElementById('tab-overview');
        if (overviewTab && overviewTab.classList.contains('active-tab')) {
            setTimeout(renderAll, 200);
        }
    }

    function onTabShow() {
        setTimeout(renderAll, 120);
    }

    function onResize() {
        rendered.forEach(function (slotId) {
            var el = document.getElementById(slotId);
            if (el && el._fullLayout) Plotly.Plots.resize(el);
        });
    }

    return {
        init: init,
        onTabShow: onTabShow,
        onResize: onResize,
        goToVisualizations: goToVisualizations,
        renderAll: renderAll,
    };
})();

/* Global hook untuk onclick di template */
function goToVisualizations(tab, subTab) {
    OverviewDashboard.goToVisualizations(tab, subTab);
}
