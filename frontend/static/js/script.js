/* ============================================================
   DS Generator — script.js  (Fixed)
   ============================================================ */
'use strict';

/* ─── TAB SWITCHING ─────────────────────────────────────────── */
function switchTab(tabName) {
    /* Hide all */
    document.querySelectorAll('.tab-content').forEach(function (el) {
        el.style.display = 'none';
        el.classList.remove('active-tab');
    });

    /* Show target */
    var target = document.getElementById('tab-' + tabName);
    if (target) {
        target.style.display = 'block';
        target.classList.add('active-tab');
    }

    /* Update nav active state */
    document.querySelectorAll('.nav-item, .nav-sub-item').forEach(function (li) {
        li.classList.remove('active');
    });

    /* Mark correct sidebar item active */
    var menuMap = {
        overview    : 'menu-overview',
        upload      : 'menu-upload',
        preview     : 'menu-preview',
        cleaning    : 'menu-cleaning',
        numerical   : 'menu-numerical',
        categorical  : 'menu-categorical',
        advanced    : 'menu-advanced',
        visualizations: 'menu-visualizations',
        timeseries  : 'menu-timeseries',
        insights    : 'menu-insights',
        ai          : 'menu-ai',
    };
    var menuId = menuMap[tabName];
    if (menuId) {
        var menuEl = document.getElementById(menuId);
        if (menuEl) menuEl.classList.add('active');
    }

    /* Auto-open relevant accordion */
    var accMap = {
        numerical   : 'acc-stats',
        categorical  : 'acc-stats',
        advanced    : 'acc-stats',
    };
    if (accMap[tabName]) {
        var accBody = document.getElementById(accMap[tabName]);
        if (accBody && !accBody.classList.contains('open')) {
            accBody.classList.add('open');
            var trigger = accBody.previousElementSibling;
            if (trigger) trigger.classList.add('open');
        }
    }

    /* Scroll content to top */
    var cc = document.querySelector('.content-container');
    if (cc) cc.scrollTop = 0;

    /* Trigger tab-specific hooks */
    if (tabName === 'visualizations') {
        setTimeout(function () {
            if (typeof VizMaster !== 'undefined') VizMaster.onTabShow();
        }, 80);
    }
    if (tabName === 'overview') {
        setTimeout(function () {
            if (typeof OverviewDashboard !== 'undefined') OverviewDashboard.onTabShow();
        }, 80);
    }
}

/* ─── DARK MODE ─────────────────────────────────────────────── */
function initThemeToggle() {
    var btn  = document.getElementById('theme-toggle');
    var icon = document.getElementById('theme-icon');
    if (!btn) return;

    var saved = localStorage.getItem('ds-theme');
    if (saved === 'dark') applyDark(true, icon);

    btn.addEventListener('click', function () {
        var isDark = document.body.getAttribute('data-theme') === 'dark';
        applyDark(!isDark, icon);
        localStorage.setItem('ds-theme', !isDark ? 'dark' : 'light');
    });
}

function applyDark(dark, icon) {
    document.body.setAttribute('data-theme', dark ? 'dark' : 'light');
    if (!icon) icon = document.getElementById('theme-icon');
    if (icon) {
        icon.classList.toggle('fa-moon', !dark);
        icon.classList.toggle('fa-sun',   dark);
    }
    setTimeout(function () {
        if (typeof Plotly === 'undefined') return;
        document.querySelectorAll('[id^="plot-"],[id^="ov-"]').forEach(function (el) {
            if (el._fullData) {
                Plotly.relayout(el, {
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor : 'rgba(0,0,0,0)',
                    'font.color' : dark ? '#c8d8f0' : '#2b3674',
                });
            }
        });
    }, 80);
}

/* ─── TEAM MODAL ─────────────────────────────────────────────── */
function initTeamModal() {
    var openBtn  = document.getElementById('team-profile-btn');
    var modal    = document.getElementById('team-modal');
    var closeBtn = document.getElementById('close-modal');
    if (!openBtn || !modal) return;

    openBtn.addEventListener('click', function () {
        modal.style.display = 'flex';
    });

    function closeModal() { modal.style.display = 'none'; }
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') closeModal();
    });
}

/* ─── LANGUAGE SELECTOR ────────────────────────────────────────── */
var TRANSLATIONS = {
    en: {
        title      : 'Descriptive Statistics Generator',
        desc       : 'Upload, analyze, visualize and get insights automatically',
        subtitle   : 'Descriptive Statistics',
        admin_role : 'Data Science Team',
    },
    id: {
        title      : 'Generator Statistik Deskriptif',
        desc       : 'Unggah, analisis, visualisasi, dan dapatkan wawasan secara otomatis',
        subtitle   : 'Statistik Deskriptif',
        admin_role : 'Tim Ilmu Data',
    },
    pt: {
        title      : 'Gerador de Estatísticas Descritivas',
        desc       : 'Envie, analise, visualize e obtenha insights automaticamente',
        subtitle   : 'Estatísticas Descritivas',
        admin_role : 'Equipe de Ciência de Dados',
    },
};

function applyLanguage(lang) {
    var t = TRANSLATIONS[lang];
    if (!t) return;
    document.querySelectorAll('[data-translate]').forEach(function (el) {
        var key = el.getAttribute('data-translate');
        if (t[key]) el.textContent = t[key];
    });
    localStorage.setItem('ds-lang', lang);
}

function initLanguageSelector() {
    var sel = document.getElementById('lang-selector');
    if (!sel) return;
    var saved = localStorage.getItem('ds-lang') || 'en';
    sel.value = saved;
    applyLanguage(saved);
    sel.addEventListener('change', function () { applyLanguage(sel.value); });
}

/* ─── DATATABLES ─────────────────────────────────────────────── */
function initDataTables() {
    if (typeof $ === 'undefined' || typeof $.fn.DataTable === 'undefined') return;
    $('table.data-table').each(function () {
        if (!$.fn.DataTable.isDataTable(this)) {
            $(this).DataTable({
                pageLength : 25,
                responsive : false,
                scrollX    : true,
                dom        : '<"dt-top"Bf>rt<"dt-bot"ip>',
                buttons    : [
                    { extend:'csvHtml5',   text:'<i class="fas fa-file-csv"></i> CSV',   className:'dt-btn' },
                    { extend:'excelHtml5', text:'<i class="fas fa-file-excel"></i> Excel', className:'dt-btn' },
                    { extend:'pdfHtml5',   text:'<i class="fas fa-file-pdf"></i> PDF',   className:'dt-btn',
                      orientation:'landscape', pageSize:'A4' },
                ],
                language: {
                    search: '<i class="fas fa-search"></i>',
                    searchPlaceholder: 'Filter data...',
                    lengthMenu: 'Show _MENU_ rows',
                    info: 'Showing _START_–_END_ of _TOTAL_ entries',
                    paginate: { previous:'‹', next:'›' },
                },
            });
        }
    });
}

/* ─── AI CHAT ────────────────────────────────────────────────── */
function sendAIMessage() {
    var input = document.getElementById('ai-input');
    if (!input) return;
    var msg = input.value.trim();
    if (!msg) return;

    appendChatMsg(msg, 'user');
    input.value = '';

    var typingEl = appendChatMsg('Sedang mengetik...', 'bot', true);
    var ctx = window.datasetContext || '';

    fetch('/api/ai-chat', {
        method  : 'POST',
        headers : { 'Content-Type': 'application/json' },
        body    : JSON.stringify({ message: msg, context: ctx }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        var bubble = typingEl.querySelector('.chat-bubble');
        bubble.innerHTML = data.reply || 'Tidak ada respons dari server.';
        bubble.classList.remove('typing');
    })
    .catch(function () {
        var bubble = typingEl.querySelector('.chat-bubble');
        bubble.innerHTML = '⚠️ Gagal terhubung ke AI. Pastikan ANTHROPIC_API_KEY sudah diset.';
        bubble.classList.remove('typing');
    });
}

function appendChatMsg(text, role, typing) {
    typing = typing || false;
    var container = document.getElementById('chat-messages');
    if (!container) return null;

    var div = document.createElement('div');
    div.className = 'chat-msg ' + role;
    div.innerHTML =
        '<div class="chat-avatar"><i class="fas fa-' + (role === 'bot' ? 'robot' : 'user') + '"></i></div>' +
        '<div class="chat-bubble' + (typing ? ' typing' : '') + '">' + text + '</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function initAIChat() {
    var input = document.getElementById('ai-input');
    if (!input) return;
    input.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendAIMessage();
    });
}

/* ─── INJECT DT STYLES ───────────────────────────────────────── */
function injectDTStyles() {
    if (document.getElementById('dt-custom-styles')) return;
    var style = document.createElement('style');
    style.id  = 'dt-custom-styles';
    style.textContent = [
        '.dt-top{display:flex;align-items:center;gap:10px;padding:12px 16px;flex-wrap:wrap;}',
        '.dt-bot{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;flex-wrap:wrap;gap:8px;}',
        '.dt-btn{background:var(--blue-light)!important;color:var(--blue)!important;',
        'border:1px solid var(--blue)!important;border-radius:8px!important;',
        'padding:6px 12px!important;font-size:.78rem!important;font-weight:600!important;',
        'cursor:pointer!important;transition:.2s!important;}',
        '.dt-btn:hover{background:var(--blue)!important;color:#fff!important;}',
        '.dataTables_filter input{border:1px solid var(--border);border-radius:8px;',
        'padding:6px 10px;background:var(--bg);color:var(--text);font-size:.85rem;',
        'outline:none;margin-left:4px;}',
        '.dataTables_filter input:focus{border-color:var(--blue);}',
        '.dataTables_paginate .paginate_button{padding:4px 10px!important;',
        'border-radius:6px!important;font-size:.8rem!important;color:var(--text)!important;cursor:pointer;}',
        '.dataTables_paginate .paginate_button.current{background:var(--blue)!important;',
        'color:#fff!important;border:none!important;}',
        '.dataTables_paginate .paginate_button:hover:not(.current){background:var(--blue-light)!important;',
        'color:var(--blue)!important;border:none!important;}',
        '.dataTables_info{font-size:.78rem;color:var(--muted);}',
    ].join('');
    document.head.appendChild(style);
}

/* ─── MOBILE SIDEBAR ────────────────────────────────────────── */
function initMobileSidebar() {
    if (window.innerWidth > 900) return;
    var sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    document.querySelectorAll('.nav-item > a, .nav-sub-item > a').forEach(function (link) {
        link.addEventListener('click', function () {
            sidebar.classList.remove('mobile-open');
        });
    });
}

/* ─── MAIN INIT ──────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    injectDTStyles();
    initThemeToggle();
    initLanguageSelector();
    initTeamModal();
    initAIChat();
    initMobileSidebar();

    if (typeof $ !== 'undefined') {
        $(document).ready(function () { initDataTables(); });
    } else {
        setTimeout(initDataTables, 800);
    }

    /* Ensure overview tab is active on first load */
    var firstActive = document.querySelector('.tab-content.active-tab');
    if (!firstActive) {
        var overview = document.getElementById('tab-overview');
        if (overview) {
            overview.style.display = 'block';
            overview.classList.add('active-tab');
        }
    }

    /* Trigger visible chart renders after DOM settles */
    setTimeout(function () {
        if (typeof renderVisibleCharts === 'function') renderVisibleCharts();
    }, 400);
});