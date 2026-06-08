/* ============================================================
   DS Generator — Kelompok 2 ITSB
   script.js — Main Application Script
   ============================================================ */

'use strict';

/* ─── TAB SWITCHING ──────────────────────────────────────────────────────── */
/**
 * switchTab(tabName)
 * Menyembunyikan semua tab, lalu menampilkan tab yang dipilih.
 * Juga memperbarui status aktif di nav sidebar.
 */
function switchTab(tabName) {
    // Sembunyikan semua tab
    document.querySelectorAll('.tab-content').forEach(el => {
        el.style.display = 'none';
        el.classList.remove('active-tab');
    });

    // Tampilkan tab yang dipilih
    const target = document.getElementById('tab-' + tabName);
    if (target) {
        target.style.display = 'block';
        target.classList.add('active-tab');
    }

    // Update nav sidebar — hapus semua active, set yang sesuai
    document.querySelectorAll('.nav-item').forEach(li => li.classList.remove('active'));
    const activeMenu = document.getElementById('menu-' + tabName);
    if (activeMenu) activeMenu.classList.add('active');

    // Scroll content-container ke atas
    const cc = document.querySelector('.content-container');
    if (cc) cc.scrollTop = 0;

    // Jika pindah ke tab visualizations, trigger render chart
    if (tabName === 'visualizations') {
        setTimeout(function () {
            if (typeof renderVisibleCharts === 'function') renderVisibleCharts();
            if (typeof renderVizSubTab === 'function')    renderVizSubTab('numerical');
        }, 100);
    }

    // Jika kembali ke overview, render chart overview
    if (tabName === 'overview') {
        setTimeout(function () {
            if (typeof renderVisibleCharts === 'function') renderVisibleCharts();
        }, 100);
    }
}

/* ─── DARK MODE TOGGLE ───────────────────────────────────────────────────── */
function initThemeToggle() {
    const btn  = document.getElementById('theme-toggle');
    const icon = document.getElementById('theme-icon');
    if (!btn) return;

    // Baca preferensi tersimpan
    const saved = localStorage.getItem('ds-theme');
    if (saved === 'dark') applyDark(true, icon);

    btn.addEventListener('click', function () {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
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
    // Relayout semua Plotly chart agar warna menyesuaikan
    setTimeout(function () {
        if (typeof Plotly === 'undefined') return;
        document.querySelectorAll('[id^="plot-"], [id^="ov-"]').forEach(function (el) {
            if (el._fullData) {
                Plotly.relayout(el, {
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor:  'rgba(0,0,0,0)',
                    'font.color':  dark ? '#c8d8f0' : '#2b3674',
                });
            }
        });
    }, 80);
}

/* ─── TEAM MODAL ─────────────────────────────────────────────────────────── */
function initTeamModal() {
    const openBtn  = document.getElementById('team-profile-btn');
    const modal    = document.getElementById('team-modal');
    const closeBtn = document.getElementById('close-modal');

    if (!openBtn || !modal) return;

    openBtn.addEventListener('click', function () {
        modal.style.display = 'flex';
        setTimeout(function () { modal.style.opacity = '1'; }, 10);
    });

    function closeModal() {
        modal.style.display = 'none';
    }

    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    // Klik di luar modal content → tutup
    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });

    // ESC untuk tutup
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') closeModal();
    });
}

/* ─── LANGUAGE SELECTOR ──────────────────────────────────────────────────── */
const TRANSLATIONS = {
    en: {
        title: 'Descriptive Statistics Generator',
        desc: 'Upload, analyze, visualize and get insights automatically',
        subtitle: 'Descriptive Statistics',
        nav_home: 'Dashboard',
        nav_upload: 'Upload Data',
        nav_analytics: 'ANALYTICS',
        nav_preview: 'Data Preview',
        nav_stats: 'Descriptive Stats',
        nav_advanced: 'ADVANCED ANALYTICS',
        admin_role: 'Data Science Team',
    },
    id: {
        title: 'Generator Statistik Deskriptif',
        desc: 'Unggah, analisis, visualisasi, dan dapatkan wawasan secara otomatis',
        subtitle: 'Statistik Deskriptif',
        nav_home: 'Beranda',
        nav_upload: 'Unggah Data',
        nav_analytics: 'ANALITIK',
        nav_preview: 'Pratinjau Data',
        nav_stats: 'Statistik Deskriptif',
        nav_advanced: 'ANALITIK LANJUTAN',
        admin_role: 'Tim Ilmu Data',
    },
    pt: {
        title: 'Gerador de Estatísticas Descritivas',
        desc: 'Envie, analise, visualize e obtenha insights automaticamente',
        subtitle: 'Estatísticas Descritivas',
        nav_home: 'Painel',
        nav_upload: 'Enviar Dados',
        nav_analytics: 'ANÁLISE',
        nav_preview: 'Visualizar Dados',
        nav_stats: 'Estatísticas Descritivas',
        nav_advanced: 'ANÁLISE AVANÇADA',
        admin_role: 'Equipe de Ciência de Dados',
    },
};

function applyLanguage(lang) {
    const t = TRANSLATIONS[lang];
    if (!t) return;
    document.querySelectorAll('[data-translate]').forEach(function (el) {
        const key = el.getAttribute('data-translate');
        if (t[key]) el.textContent = t[key];
    });
    localStorage.setItem('ds-lang', lang);
}

function initLanguageSelector() {
    const sel = document.getElementById('lang-selector');
    if (!sel) return;

    const saved = localStorage.getItem('ds-lang') || 'en';
    sel.value = saved;
    applyLanguage(saved);

    sel.addEventListener('change', function () {
        applyLanguage(sel.value);
    });
}

/* ─── DATATABLES INIT ────────────────────────────────────────────────────── */
function initDataTables() {
    if (typeof $ === 'undefined' || typeof $.fn.DataTable === 'undefined') return;

    $('table.data-table').each(function () {
        if (!$.fn.DataTable.isDataTable(this)) {
            $(this).DataTable({
                pageLength: 25,
                responsive: false,
                scrollX: true,
                dom: '<"dt-top"Bf>rt<"dt-bot"ip>',
                buttons: [
                    { extend: 'csvHtml5',   text: '<i class="fas fa-file-csv"></i> CSV',   className: 'dt-btn' },
                    { extend: 'excelHtml5', text: '<i class="fas fa-file-excel"></i> Excel', className: 'dt-btn' },
                    { extend: 'pdfHtml5',   text: '<i class="fas fa-file-pdf"></i> PDF',    className: 'dt-btn',
                      orientation: 'landscape', pageSize: 'A4' },
                ],
                language: {
                    search: '<i class="fas fa-search"></i>',
                    searchPlaceholder: 'Filter data...',
                    lengthMenu: 'Show _MENU_ rows',
                    info: 'Showing _START_–_END_ of _TOTAL_ entries',
                    paginate: { previous: '‹', next: '›' },
                },
            });
        }
    });
}

/* ─── AI CHAT (DataBot) ──────────────────────────────────────────────────── */
function sendAIMessage() {
    const input = document.getElementById('ai-input');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;

    appendChatMsg(msg, 'user');
    input.value = '';

    const typingEl = appendChatMsg('Sedang mengetik...', 'bot', true);

    const ctx = window.datasetContext || '';

    fetch('/api/ai-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, context: ctx }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        typingEl.querySelector('.chat-bubble').innerHTML =
            data.reply || 'Tidak ada respons dari server.';
        typingEl.querySelector('.chat-bubble').classList.remove('typing');
    })
    .catch(function () {
        typingEl.querySelector('.chat-bubble').innerHTML =
            '⚠️ Gagal terhubung ke AI. Pastikan ANTHROPIC_API_KEY sudah diset.';
        typingEl.querySelector('.chat-bubble').classList.remove('typing');
    });
}

function appendChatMsg(text, role, typing) {
    typing = typing || false;
    const container = document.getElementById('chat-messages');
    if (!container) return null;

    const div = document.createElement('div');
    div.className = 'chat-msg ' + role;
    div.innerHTML =
        '<div class="chat-avatar"><i class="fas fa-' + (role === 'bot' ? 'robot' : 'user') + '"></i></div>' +
        '<div class="chat-bubble' + (typing ? ' typing' : '') + '">' + text + '</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function initAIChat() {
    const input = document.getElementById('ai-input');
    if (!input) return;
    input.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendAIMessage();
    });
}

/* ─── VIZ SUB-TAB SWITCHER ───────────────────────────────────────────────── */
function switchVizTab(tab) {
    document.querySelectorAll('.viz-subtab-content').forEach(function (el) {
        el.style.display = 'none';
        el.classList.remove('active-viztab');
    });
    document.querySelectorAll('.viz-subtab-btn').forEach(function (btn) {
        btn.classList.remove('active');
        const oc = btn.getAttribute('onclick') || '';
        if (oc.includes("'" + tab + "'") || oc.includes('"' + tab + '"')) {
            btn.classList.add('active');
        }
    });
    const target = document.getElementById('viz-' + tab);
    if (target) {
        target.style.display = 'block';
        target.classList.add('active-viztab');
    }
    // Plotly: render charts di sub-tab ini
    setTimeout(function () {
        if (typeof renderVizSubTab === 'function') renderVizSubTab(tab);
    }, 60);
}

/* ─── EXTRA CSS FOR DATATABLES (injected once) ───────────────────────────── */
function injectDTStyles() {
    if (document.getElementById('dt-custom-styles')) return;
    const style = document.createElement('style');
    style.id = 'dt-custom-styles';
    style.textContent = `
        .dt-top { display:flex; align-items:center; gap:10px; padding:12px 16px; flex-wrap:wrap; }
        .dt-bot { display:flex; align-items:center; justify-content:space-between; padding:10px 16px; flex-wrap:wrap; gap:8px; }
        .dt-btn {
            background: var(--blue-light) !important; color: var(--blue) !important;
            border: 1px solid var(--blue) !important; border-radius: 8px !important;
            padding: 6px 12px !important; font-size: 0.78rem !important; font-weight: 600 !important;
            cursor: pointer !important; transition: .2s !important;
        }
        .dt-btn:hover { background: var(--blue) !important; color: #fff !important; }
        .dataTables_filter input {
            border: 1px solid var(--border); border-radius: 8px; padding: 6px 10px;
            background: var(--bg); color: var(--text); font-size: 0.85rem; outline: none;
            margin-left: 4px;
        }
        .dataTables_filter input:focus { border-color: var(--blue); }
        .dataTables_paginate .paginate_button {
            padding: 4px 10px !important; border-radius: 6px !important; font-size:0.8rem !important;
            color: var(--text) !important; cursor: pointer;
        }
        .dataTables_paginate .paginate_button.current {
            background: var(--blue) !important; color: #fff !important; border: none !important;
        }
        .dataTables_paginate .paginate_button:hover:not(.current) {
            background: var(--blue-light) !important; color: var(--blue) !important; border: none !important;
        }
        .dataTables_info { font-size: 0.78rem; color: var(--muted); }
        .viz-subtab-nav { display:flex; gap:8px; flex-wrap:wrap; }
        .viz-subtab-btn {
            padding: 8px 16px; border-radius: 20px; border: 1.5px solid var(--border);
            background: var(--bg); color: var(--muted); font-size: 0.82rem; font-weight: 600;
            cursor: pointer; transition: .2s; font-family: inherit;
        }
        .viz-subtab-btn.active,
        .viz-subtab-btn:hover {
            background: var(--blue); color: #fff; border-color: var(--blue);
        }
        .chart-badge {
            font-size: 0.65rem; font-weight: 700;
            background: var(--blue-light); color: var(--blue);
            padding: 2px 9px; border-radius: 20px;
        }
        .chart-grid-1 { display: grid; grid-template-columns: 1fr; gap: 18px; }
    `;
    document.head.appendChild(style);
}

/* ─── RESPONSIVE SIDEBAR TOGGLE (mobile) ─────────────────────────────────── */
function initMobileSidebar() {
    // Jika layar kecil, klik nav-item akan menutup sidebar
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    if (window.innerWidth > 900) return;

    document.querySelectorAll('.nav-item a').forEach(function (link) {
        link.addEventListener('click', function () {
            sidebar.style.transform = 'translateX(-100%)';
            setTimeout(function () { sidebar.style.transform = ''; }, 400);
        });
    });
}

/* ─── MAIN INIT ──────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    injectDTStyles();
    initThemeToggle();
    initLanguageSelector();
    initTeamModal();
    initAIChat();
    initMobileSidebar();

    // Inisialisasi DataTables setelah jQuery siap
    if (typeof $ !== 'undefined') {
        $(document).ready(function () { initDataTables(); });
    } else {
        // Fallback: tunggu sedikit untuk jQuery dari CDN
        setTimeout(initDataTables, 800);
    }

    // Pastikan tab overview aktif saat pertama load
    const firstActive = document.querySelector('.tab-content.active-tab');
    if (!firstActive) {
        const overview = document.getElementById('tab-overview');
        if (overview) {
            overview.style.display = 'block';
            overview.classList.add('active-tab');
        }
    }

    // Render overview charts setelah DOM siap
    setTimeout(function () {
        if (typeof renderVisibleCharts === 'function') renderVisibleCharts();
    }, 400);
});