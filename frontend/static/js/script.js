/* ============================================================
   DS Generator — Kelompok 2 ITSB
   script.js — Week 15 Full Upgrade
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    /* ── 1. FILE INPUT & ENABLE ANALYZE BUTTON ─────────────── */
    const fileInput = document.getElementById('file-input');
    const fileDisplay = document.getElementById('file-name-display');
    const btnSubmit = document.getElementById('btn-submit');

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                fileDisplay.textContent = "📄 Selected: " + fileInput.files[0].name;
                btnSubmit.disabled = false;
            }
        });

        // Drag & drop support
        const dropzone = document.querySelector('.modern-dropzone');
        if (dropzone) {
            dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
            dropzone.addEventListener('drop', e => {
                e.preventDefault();
                dropzone.classList.remove('drag-over');
                const dt = e.dataTransfer;
                if (dt.files.length) {
                    fileInput.files = dt.files;
                    fileDisplay.textContent = "📄 Selected: " + dt.files[0].name;
                    btnSubmit.disabled = false;
                }
            });
        }
    }

    /* ── 2. UPLOAD FORM — DUPLICATE CHECK + LOADING ─────────── */
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(uploadForm);
            const selectedFile = fileInput ? fileInput.files[0] : null;
            if (!selectedFile) return;

            // Send AJAX with X-Requested-With header so Flask can return JSON
            const xhr = new XMLHttpRequest();
            xhr.open('POST', uploadForm.action, true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

            xhr.onload = function () {
                try {
                    const resp = JSON.parse(xhr.responseText);
                    if (resp.duplicate) {
                        Swal.fire({
                            icon: 'info',
                            title: '📂 Dataset Already Exists!',
                            html: `File <strong>${resp.filename}</strong> sudah pernah dianalisis.<br>Menampilkan hasil analisis sebelumnya...`,
                            confirmButtonColor: '#4318ff',
                            confirmButtonText: 'Lihat Dashboard',
                            timer: 5000,
                            timerProgressBar: true
                        }).then(() => { window.location.href = resp.redirect; });
                    } else {
                        Swal.fire({
                            icon: 'success',
                            title: '✅ Upload Berhasil!',
                            text: `Dataset "${resp.filename}" sedang diproses...`,
                            showConfirmButton: false,
                            timer: 1500,
                            didClose: () => { window.location.href = resp.redirect; }
                        });
                    }
                } catch (_) {
                    // Fallback: show loading then submit normally
                    Swal.fire({
                        title: 'Processing...', text: 'Analyzing Data & Generating Statistics.',
                        icon: 'info', allowOutsideClick: false, showConfirmButton: false,
                        didOpen: () => { Swal.showLoading(); HTMLFormElement.prototype.submit.call(uploadForm); }
                    });
                }
            };
            xhr.onerror = function () {
                Swal.fire({ icon: 'error', title: 'Oops!', text: 'Terjadi kesalahan jaringan.', confirmButtonColor: '#4318ff' });
            };

            // Show loading during upload
            Swal.fire({
                title: '⏳ Uploading...', text: 'Mengunggah dan menganalisis dataset Anda.',
                allowOutsideClick: false, showConfirmButton: false,
                didOpen: () => { Swal.showLoading(); xhr.send(formData); }
            });
        });
    }

    /* ── 3. DARK / LIGHT MODE ────────────────────────────────── */
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const body = document.body;

    const savedTheme = localStorage.getItem('theme') || 'light';
    body.setAttribute('data-theme', savedTheme);
    if (savedTheme === 'dark') themeIcon.classList.replace('fa-moon', 'fa-sun');

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDark = body.getAttribute('data-theme') === 'dark';
            body.setAttribute('data-theme', isDark ? 'light' : 'dark');
            themeIcon.classList.replace(isDark ? 'fa-sun' : 'fa-moon', isDark ? 'fa-moon' : 'fa-sun');
            localStorage.setItem('theme', isDark ? 'light' : 'dark');
            // Re-render charts with correct colors
            if (window.chartsRendered && window.renderCharts) {
                window.chartsRendered = false;
                window.renderCharts();
            }
        });
    }

    /* ── 4. MULTI-LANGUAGE SYSTEM ────────────────────────────── */
    const translations = {
        en: {
            subtitle: "Descriptive Statistics", nav_home: "Dashboard", nav_upload: "Upload Data",
            nav_preview: "Data Preview", nav_stats: "Descriptive Stats", nav_analytics: "ANALYTICS",
            nav_advanced: "ADVANCED ANALYTICS", title: "Descriptive Statistics Generator",
            desc: "Upload, analyze, visualize and get insights automatically", admin_role: "Data Science Team",
            upload_title: "Upload Your Dataset", dropzone_title: "Drag & drop your file here"
        },
        id: {
            subtitle: "Statistik Deskriptif", nav_home: "Dasbor", nav_upload: "Unggah Data",
            nav_preview: "Pratinjau Data", nav_stats: "Statistik Deskriptif", nav_analytics: "ANALITIK",
            nav_advanced: "ANALITIK LANJUTAN", title: "Generator Statistik Deskriptif",
            desc: "Unggah, analisis, visualisasi, dan dapatkan wawasan otomatis", admin_role: "Tim Data Science",
            upload_title: "Unggah Dataset Anda", dropzone_title: "Tarik & lepas file di sini"
        },
        pt: {
            subtitle: "Estatística Descritiva", nav_home: "Painel", nav_upload: "Carregar Dados",
            nav_preview: "Visualizar Dados", nav_stats: "Estatísticas", nav_analytics: "ANÁLISES",
            nav_advanced: "ANÁLISE AVANÇADA", title: "Gerador de Estatísticas Descritivas",
            desc: "Carregue, analise, visualize e obtenha insights automaticamente", admin_role: "Equipe de Ciência",
            upload_title: "Carregue seu conjunto de dados", dropzone_title: "Arraste e solte aqui"
        }
    };

    const langSelector = document.getElementById('lang-selector');
    function changeLanguage(lang) {
        document.querySelectorAll('[data-translate]').forEach(el => {
            const key = el.getAttribute('data-translate');
            if (translations[lang]?.[key]) el.textContent = translations[lang][key];
        });
        localStorage.setItem('lang', lang);
    }
    const savedLang = localStorage.getItem('lang') || 'en';
    if (langSelector) langSelector.value = savedLang;
    changeLanguage(savedLang);
    if (langSelector) langSelector.addEventListener('change', e => changeLanguage(e.target.value));

    /* ── 5. TEAM MODAL ───────────────────────────────────────── */
    const teamBtn = document.getElementById('team-profile-btn');
    const teamModal = document.getElementById('team-modal');
    const closeModal = document.getElementById('close-modal');

    if (teamBtn && teamModal) {
        teamBtn.addEventListener('click', () => { teamModal.style.display = 'flex'; });
        closeModal?.addEventListener('click', () => { teamModal.style.display = 'none'; });
        window.addEventListener('click', e => { if (e.target === teamModal) teamModal.style.display = 'none'; });
    }

    /* ── 6. DATATABLES ───────────────────────────────────────── */
    if ($.fn.DataTable) {
        $('.data-table').DataTable({
            dom: '<"top"Bf>rt<"bottom"ilp><"clear">',
            buttons: ['copy', 'csv', 'excel', 'pdf'],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
            scrollX: true,
            autoWidth: false,
            language: { search: "🔍 Search:" }
        });
    }

    /* ── 7. TAB SWITCHER ─────────────────────────────────────── */
    window.switchTab = function (tabId) {
        document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
        const active = document.getElementById('tab-' + tabId);
        if (active) active.style.display = 'block';

        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        const menu = document.getElementById('menu-' + tabId);
        if (menu) menu.classList.add('active');

        if ($.fn.DataTable) {
            $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
        }

        // Auto-render charts when switching to visualizations or overview
        if ((tabId === 'visualizations' || tabId === 'overview') && window.renderCharts) {
            setTimeout(window.renderCharts, 150);
        }
    };

    /* ── 8. DATA NETWORK CANVAS ANIMATION (Welcome page) ────── */
    const canvas = document.getElementById('data-network-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let width, height, particles;

        function initCanvas() {
            width = canvas.width = canvas.parentElement.clientWidth;
            height = canvas.height = canvas.parentElement.clientHeight;
            particles = [];
            const count = window.innerWidth < 768 ? 50 : 100;
            for (let i = 0; i < count; i++) particles.push(new Particle());
        }

        class Particle {
            constructor() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.vx = (Math.random() - 0.5) * 1.2;
                this.vy = (Math.random() - 0.5) * 1.2;
                this.r = Math.random() * 2.5 + 1;
            }
            update() {
                this.x += this.vx; this.y += this.vy;
                if (this.x < 0 || this.x > width) this.vx *= -1;
                if (this.y < 0 || this.y > height) this.vy *= -1;
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(134,140,255,0.6)';
                ctx.fill();
            }
        }

        function animate() {
            ctx.clearRect(0, 0, width, height);
            particles.forEach(p => { p.update(); p.draw(); });
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 100) {
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(134,140,255,${1 - dist / 100})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
            requestAnimationFrame(animate);
        }

        initCanvas();
        animate();
        window.addEventListener('resize', initCanvas);
    }

    /* ── 9. WELCOME PAGE: LOGIN & ONBOARDING ─────────────────── */
    window.processLogin = function () {
        const name = document.getElementById('user-name')?.value.trim();
        const email = document.getElementById('user-email')?.value.trim();
        if (!name || !email) {
            Swal.fire({ icon: 'warning', title: 'Incomplete!', text: 'Please fill in both fields.', confirmButtonColor: '#4318ff' });
            return;
        }
        localStorage.setItem('ds_user_name', name);
        localStorage.setItem('ds_user_email', email);
        const login = document.getElementById('login-screen');
        const onboarding = document.getElementById('onboarding-screen');
        if (login) login.style.display = 'none';
        if (onboarding) { onboarding.style.display = 'flex'; showSlide(1); }
    };

    window.nextSlide = function (num) { showSlide(num); };

    function showSlide(num) {
        document.querySelectorAll('.onboarding-slide').forEach(s => s.classList.remove('active'));
        const slide = document.getElementById('slide-' + num);
        if (slide) slide.classList.add('active');
        if (num === 3) {
            const name = localStorage.getItem('ds_user_name') || 'User';
            const greetEl = document.getElementById('welcome-greeting');
            const nameEl = document.getElementById('welcome-name');
            const hour = new Date().getHours();
            const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';
            if (greetEl) greetEl.textContent = greeting;
            if (nameEl) nameEl.textContent = name;
        }
    }

    window.enterDashboard = function () {
        const overlay = document.getElementById('app-overlay');
        if (overlay) {
            overlay.style.transition = 'opacity 0.5s ease';
            overlay.style.opacity = '0';
            setTimeout(() => { overlay.style.display = 'none'; }, 500);
        }
    };

    // Auto-skip login if already logged in
    const savedUser = localStorage.getItem('ds_user_name');
    const overlay = document.getElementById('app-overlay');
    if (savedUser && overlay) {
        // Show onboarding directly
        const loginScreen = document.getElementById('login-screen');
        const onboardingScreen = document.getElementById('onboarding-screen');
        if (loginScreen) loginScreen.style.display = 'none';
        if (onboardingScreen) { onboardingScreen.style.display = 'flex'; showSlide(1); }
    }
});
