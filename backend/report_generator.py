"""
backend/report_generator.py
Comprehensive PDF Report Generator — DS Generator | Kelompok 2 ITSB

Supports:
  - Full descriptive stats table (numerical + categorical)
  - Data quality summary with KPI boxes
  - Embedded static visualizations (Histogram + Correlation Heatmap)
  - Auto-generated insights and strategic recommendations
  - Diagonal CONFIDENTIAL watermark on every page
  - Two-pass NumberedCanvas for "Page X of Y" footer
  - Robust try-except: every section degrades gracefully, PDF never crashes
"""

import os
import io
import datetime
import tempfile

import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


# ─── Watermark helper ────────────────────────────────────────────────────────

def draw_watermark(canvas_obj, doc):
    """
    Draws a transparent diagonal watermark 'CONFIDENTIAL - Kelompok 2 ITSB'
    behind the content on every page.  Called as onFirstPage / onLaterPages.
    """
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica-Bold', 50)
    canvas_obj.setFillColor(colors.HexColor('#e0e5f2'), alpha=0.12)
    canvas_obj.translate(306, 396)
    canvas_obj.rotate(42)
    canvas_obj.drawCentredString(0, 0, "CONFIDENTIAL")
    canvas_obj.setFont('Helvetica', 14)
    canvas_obj.drawCentredString(0, -44, "Kelompok 2 ITSB — DS Generator")
    canvas_obj.restoreState()


# ─── Two-pass canvas (Page X of Y) ───────────────────────────────────────────

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that computes total page count dynamically.
    Renders header/footer and 'Page X of Y' on every page.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#a3aed0"))

        # Header (skip cover page)
        if self._pageNumber > 1:
            self.drawString(54, 750, "DS Generator Report — Kelompok 2 ITSB")
            self.setStrokeColor(colors.HexColor("#e0e5f2"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        date_str = datetime.datetime.now().strftime('%d %b %Y')
        self.drawString(54, 40, f"Descriptive Statistics & Quality Report | Generated: {date_str}")
        self.setStrokeColor(colors.HexColor("#e0e5f2"))
        self.setLineWidth(0.5)
        self.line(54, 52, 558, 52)

        self.restoreState()


# ─── Quality report normaliser ───────────────────────────────────────────────

def _normalise_quality_report(quality_report, df):
    """
    Accepts either:
      a) A list[dict]  — raw output of analyze_quality()
      b) A dict        — rich output of get_quality_report() with keys
                         'summary', 'columns', 'warnings'

    Always returns a dict with those three keys so the rest of the
    generator can use quality_report['summary']['missing_cells'] etc.
    without hitting  TypeError: list indices must be integers or slices.
    """
    # ── Case A: already the right dict ───────────────────────────────────────
    if isinstance(quality_report, dict) and 'summary' in quality_report:
        return quality_report

    # ── Case B: list of per-column dicts (analyze_quality output) ────────────
    if isinstance(quality_report, list):
        col_list = quality_report
    else:
        col_list = []

    # Re-build global summary from the column list + df
    total_rows   = len(df)
    total_cols   = len(df.columns)
    total_cells  = max(total_rows * total_cols, 1)
    missing_cells   = int(df.isna().sum().sum())
    duplicate_rows  = int(df.duplicated().sum())
    missing_pct  = round(missing_cells / total_cells * 100, 2)

    # IQR outlier count from df directly
    total_outliers = 0
    for c in df.select_dtypes(include='number').columns:
        s = df[c].dropna()
        if len(s) >= 4:
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            total_outliers += int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())

    warnings = []
    if missing_pct > 0:
        warnings.append(f'{missing_cells} sel kosong (missing) — {missing_pct}% dari total data')
    if duplicate_rows > 0:
        warnings.append(f'{duplicate_rows} baris duplikat ditemukan')
    if total_outliers > 0:
        warnings.append(f'{total_outliers} outlier terdeteksi (IQR method)')

    needs_cleaning = bool(warnings)

    # Ensure each column entry has the 'outliers' key (analyze_quality omits it)
    for row in col_list:
        if 'outliers' not in row:
            row['outliers'] = 0

    return {
        'summary': {
            'total_rows'    : total_rows,
            'total_cols'    : total_cols,
            'missing_cells' : missing_cells,
            'missing_pct'   : missing_pct,
            'duplicate_rows': duplicate_rows,
            'total_outliers': total_outliers,
            'needs_cleaning': needs_cleaning,
        },
        'columns' : col_list,
        'warnings': warnings,
    }


# ─── Static chart generation ─────────────────────────────────────────────────

def _try_generate_charts(df, num_cols, cat_cols, max_charts=3):
    """
    Generates up to max_charts static PNG images using Plotly + Kaleido.
    Returns a list of (title, filepath) tuples for existing temp files.
    Falls back gracefully if kaleido is not installed.
    """
    chart_paths = []
    try:
        import plotly.graph_objects as go
        import plotly.express as px
    except ImportError:
        return chart_paths

    tmp_dir = tempfile.gettempdir()

    # Chart 1 — Histogram of first numeric column
    if num_cols and len(chart_paths) < max_charts:
        try:
            col = num_cols[0]
            data = df[col].dropna()
            fig = go.Figure(go.Histogram(
                x=data.tolist(), nbinsx=30,
                marker_color='#4ECDC4', opacity=0.85,
            ))
            fig.update_layout(
                title=f'Histogram: {col}',
                paper_bgcolor='white', plot_bgcolor='#f8f9fa',
                font=dict(color='#1b254b'),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            path = os.path.join(tmp_dir, f'_rpt_hist_{col[:20]}.png')
            fig.write_image(path, width=520, height=300)
            if os.path.exists(path):
                chart_paths.append((f'Histogram — {col}', path))
        except Exception as e:
            print(f"[report_generator] histogram chart error: {e}")

    # Chart 2 — Correlation Heatmap (needs >= 2 numeric cols)
    if len(num_cols) >= 2 and len(chart_paths) < max_charts:
        try:
            cols = num_cols[:10]
            corr = df[cols].apply(pd.to_numeric, errors='coerce').corr()
            fig = go.Figure(go.Heatmap(
                z=corr.values.tolist(),
                x=corr.columns.tolist(),
                y=corr.columns.tolist(),
                colorscale='RdBu',
                zmid=0,
                text=[[f'{v:.2f}' for v in row] for row in corr.values.tolist()],
                texttemplate='%{text}',
            ))
            fig.update_layout(
                title='Correlation Heatmap',
                paper_bgcolor='white',
                font=dict(color='#1b254b'),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            path = os.path.join(tmp_dir, '_rpt_heatmap.png')
            fig.write_image(path, width=520, height=360)
            if os.path.exists(path):
                chart_paths.append(('Correlation Heatmap', path))
        except Exception as e:
            print(f"[report_generator] heatmap chart error: {e}")

    # Chart 3 — Bar chart of first categorical column
    if cat_cols and len(chart_paths) < max_charts:
        try:
            col = cat_cols[0]
            vc = df[col].value_counts().head(12)
            fig = go.Figure(go.Bar(
                x=vc.index.astype(str).tolist(),
                y=vc.values.tolist(),
                marker_color='#7EA9FF', opacity=0.9,
            ))
            fig.update_layout(
                title=f'Bar Chart — {col}',
                paper_bgcolor='white', plot_bgcolor='#f8f9fa',
                font=dict(color='#1b254b'),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            path = os.path.join(tmp_dir, f'_rpt_bar_{col[:20]}.png')
            fig.write_image(path, width=520, height=300)
            if os.path.exists(path):
                chart_paths.append((f'Bar Chart — {col}', path))
        except Exception as e:
            print(f"[report_generator] bar chart error: {e}")

    return chart_paths


# ─── Main entry point ────────────────────────────────────────────────────────

def generate_pdf_report(
    dest_path, filename, df,
    quality_report, metrics, num_stats, cat_stats,
    auto_insights, cleaning_history, cleaning_summary
):
    """
    Generates a comprehensive PDF report with:
      1. Web/app description + team members
      2. Data description & quality KPIs
      3. Embedded chart visuals (Histogram + Heatmap + Bar)
      4. Auto insights
      5. Strategic recommendations
      6. Descriptive statistics tables
      7. Cleaning pipeline explanation & log
    """

    # ── Normalise quality_report ──────────────────────────────────────────────
    quality_report = _normalise_quality_report(quality_report, df)

    # ── Detect column types ───────────────────────────────────────────────────
    try:
        num_cols = [ns['Column'] for ns in (num_stats or [])]
        cat_cols = [cs['Column'] for cs in (cat_stats or [])]
    except Exception:
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    # ── Generate static chart images ─────────────────────────────────────────
    chart_images = []
    try:
        chart_images = _try_generate_charts(df, num_cols, cat_cols, max_charts=3)
    except Exception as e:
        print(f"[report_generator] chart generation error: {e}")

    # ── Setup Document ────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        dest_path,
        pagesize=letter,
        leftMargin=54, rightMargin=54,
        topMargin=72, bottomMargin=72,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CoverTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=20, leading=24,
        textColor=colors.HexColor('#1b254b'), spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, leading=15,
        textColor=colors.HexColor('#4318ff'), spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        'Header1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=15,
        textColor=colors.HexColor('#1b254b'),
        spaceBefore=14, spaceAfter=8, keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'Header2', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13,
        textColor=colors.HexColor('#4318ff'),
        spaceBefore=10, spaceAfter=5, keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=colors.HexColor('#4a5568'), spaceAfter=6,
    )
    th_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.white,
    )
    td_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9,
        textColor=colors.HexColor('#1b254b'),
    )
    warning_style = ParagraphStyle(
        'WarningText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10,
        textColor=colors.HexColor('#856404'),
    )

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════════
    try:
        banner_data = [[Paragraph(
            "DATA SCIENCE GENERATOR SYSTEM",
            ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=10,
                           textColor=colors.white, leading=12)
        )]]
        banner_table = Table(banner_data, colWidths=[504])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#4318ff')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 15))
        story.append(Paragraph("Dataset Quality & Descriptive Statistics Report", title_style))
        story.append(Paragraph(f"Analysis and decision-support report for: {filename}", subtitle_style))
        story.append(Spacer(1, 8))
    except Exception as e:
        print(f"[report_generator] cover page error: {e}")
        story.append(Paragraph(f"Report: {filename}", title_style))
        story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Deskripsi Web
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("1. TENTANG DS GENERATOR", h1_style))
        desc_web = (
            "<b>DS Generator (Descriptive Statistics Generator)</b> adalah sebuah platform analisis data "
            "otomatis berbasis web yang dirancang khusus oleh <b>Kelompok 2 Data Science ITSB</b>. "
            "Aplikasi ini membantu HR, analis data, dan pengambil keputusan bisnis dalam mengunggah dataset, "
            "menganalisis kesehatan data (quality audit), membersihkan data yang kotor (data cleaning), "
            "menghitung statistik deskriptif tingkat lanjut, memvisualisasikan temuan secara interaktif, "
            "serta merumuskan rekomendasi keputusan strategis berbasis data secara real-time."
        )
        story.append(Paragraph(desc_web, body_style))
        story.append(Spacer(1, 8))
    except Exception as e:
        print(f"[report_generator] section 1 error: {e}")
        story.append(Paragraph("1. TENTANG DS GENERATOR — N/A", body_style))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Member
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("2. ANGGOTA TIM PENGEMBANG (KELOMPOK 2 ITSB)", h1_style))
        member_data = [
            [Paragraph("<b>Nama Lengkap</b>", th_style),
             Paragraph("<b>NIM</b>", th_style),
             Paragraph("<b>Peran / Fokus Analisis</b>", th_style)],
            [Paragraph("Carol Dupino Pereira", td_style),       Paragraph("52250051", td_style), Paragraph("Descriptive & Advanced Statistics Engine", td_style)],
            [Paragraph("Refantanur Husnul Haqib", td_style),    Paragraph("52250052", td_style), Paragraph("Visualizations & Dynamic Plotly Dashboard", td_style)],
            [Paragraph("Cahaya Medina Semidang", td_style),     Paragraph("52250053", td_style), Paragraph("Data Preprocessing & Sanitizer Module", td_style)],
            [Paragraph("Raihania Syah Putri", td_style),        Paragraph("52250054", td_style), Paragraph("Time Series Forecasting & Trends Panel", td_style)],
            [Paragraph("Cloise Shafira", td_style),             Paragraph("52250044", td_style), Paragraph("Smart Insights Generation Algorithm", td_style)],
            [Paragraph("Adinda Adelia Futri", td_style),        Paragraph("52250055", td_style), Paragraph("Reporting System PDF/Excel & Security Sanitization", td_style)],
        ]
        member_table = Table(member_data, colWidths=[180, 100, 224])
        member_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111c44')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(member_table)
        story.append(PageBreak())
    except Exception as e:
        print(f"[report_generator] section 2 error: {e}")
        story.append(Paragraph("2. ANGGOTA TIM — N/A", body_style))
        story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Deskripsi Data & KPI
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("3. DESKRIPSI DATA & RINGKASAN EKSEKUTIF", h1_style))

        summary = quality_report.get('summary', {})
        needs_cleaning = summary.get('needs_cleaning', False)
        status_label = "RAW DATA (Perlu Pembersihan)" if needs_cleaning else "CLEAN DATA (Bersih)"
        status_color = "#e53e3e" if needs_cleaning else "#38a169"

        # Metadata table
        meta_info = [
            [Paragraph("<b>Nama File Dataset:</b>", body_style),      Paragraph(str(filename), body_style)],
            [Paragraph("<b>Waktu Analisis:</b>", body_style),          Paragraph(datetime.datetime.now().strftime('%d %B %Y, %H:%M:%S'), body_style)],
            [Paragraph("<b>Status Kebersihan:</b>", body_style),       Paragraph(f"<font color='{status_color}'><b>{status_label}</b></font>", body_style)],
            [Paragraph("<b>Total Baris (Observasi):</b>", body_style), Paragraph(str(metrics.get('total_rows', len(df))), body_style)],
            [Paragraph("<b>Total Kolom (Variabel):</b>", body_style),  Paragraph(str(metrics.get('total_columns', len(df.columns))), body_style)],
            [Paragraph("<b>Variabel Numerik:</b>", body_style),        Paragraph(str(metrics.get('num_count', 0)), body_style)],
            [Paragraph("<b>Variabel Kategorikal:</b>", body_style),    Paragraph(str(metrics.get('cat_count', 0)), body_style)],
        ]
        meta_table = Table(meta_info, colWidths=[150, 354])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # KPI box
        kpis = [
            [
                Paragraph("<b>Missing Cells</b>", ParagraphStyle('Hk', parent=body_style, fontName='Helvetica-Bold')),
                Paragraph("<b>Duplicate Rows</b>", ParagraphStyle('Hk', parent=body_style, fontName='Helvetica-Bold')),
                Paragraph("<b>IQR Outliers</b>", ParagraphStyle('Hk', parent=body_style, fontName='Helvetica-Bold')),
            ],
            [
                Paragraph(f"<font size=11 color='#2d3748'><b>{summary.get('missing_cells', 'N/A')}</b></font>"
                          f"<br/><font size=7 color='#718096'>({summary.get('missing_pct', 0)}%)</font>", body_style),
                Paragraph(f"<font size=11 color='#2d3748'><b>{summary.get('duplicate_rows', 'N/A')}</b></font>", body_style),
                Paragraph(f"<font size=11 color='#2d3748'><b>{summary.get('total_outliers', 'N/A')}</b></font>", body_style),
            ],
        ]
        kpi_table = Table(kpis, colWidths=[168, 168, 168])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 10))

        # Quality warnings
        warnings = quality_report.get('warnings', [])
        if warnings:
            story.append(Paragraph("Identifikasi Masalah Kualitas Data:", ParagraphStyle(
                'Sub', parent=h1_style, fontSize=9, leading=11)))
            warnings_box = [[Paragraph("•", warning_style), Paragraph(w, warning_style)] for w in warnings]
            warn_table = Table(warnings_box, colWidths=[15, 489])
            warn_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#ffeeba')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(warn_table)

        story.append(PageBreak())
    except Exception as e:
        print(f"[report_generator] section 3 error: {e}")
        story.append(Paragraph("3. DESKRIPSI DATA — N/A (error saat memuat)", body_style))
        story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Visualisasi (embedded charts)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("4. VISUALISASI DATA KUNCI", h1_style))
        if chart_images:
            for chart_title, chart_path in chart_images:
                try:
                    story.append(Paragraph(chart_title, h2_style))
                    img = Image(chart_path, width=450, height=260)
                    img.hAlign = 'CENTER'
                    story.append(img)
                    story.append(Spacer(1, 10))
                except Exception as img_err:
                    print(f"[report_generator] embedding image '{chart_title}' failed: {img_err}")
                    story.append(Paragraph(f"<i>[Visualisasi '{chart_title}' tidak dapat ditampilkan — N/A]</i>", body_style))
        else:
            visual_text = (
                "Visualisasi grafis yang disajikan pada dashboard interaktif DS Generator mencakup:<br/>"
                "• <b>Histogram &amp; Density Plot (Variabel Numerik):</b> Penyebaran frekuensi nilai dan deteksi distribusi.<br/>"
                "• <b>Bar Chart &amp; Pie Chart (Variabel Kategorikal):</b> Frekuensi dan proporsi kategori.<br/>"
                "• <b>Correlation Heatmap (Bivariate):</b> Matriks korelasi antar variabel numerik.<br/>"
                "• <b>Time Series Plot (Auto-Detected):</b> Tren historis dan pola musiman data.<br/><br/>"
                "<i>Catatan: Ekspor grafis statis membutuhkan library <b>kaleido</b>. "
                "Install dengan: <b>pip install kaleido</b></i>"
            )
            story.append(Paragraph(visual_text, body_style))

        story.append(Spacer(1, 10))
    except Exception as e:
        print(f"[report_generator] section 4 error: {e}")
        story.append(Paragraph("4. VISUALISASI — N/A", body_style))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — Insight
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("5. TEMUAN KUNCI & INSIGHT OTOMATIS", h1_style))
        if auto_insights:
            for ins in auto_insights:
                try:
                    ins_title = ins.get('title', 'Temuan Data')
                    ins_desc  = ins.get('desc', '')
                    ins_type  = ins.get('type', 'info')

                    t_color = "#2b6cb0"
                    if ins_type == 'success': t_color = "#2f855a"
                    elif ins_type == 'warning': t_color = "#c05621"
                    elif ins_type == 'danger': t_color = "#c53030"

                    story.append(Paragraph(f"<b><font color='{t_color}'>{ins_title}</font></b>", h2_style))
                    story.append(Paragraph(str(ins_desc), body_style))
                    story.append(Spacer(1, 3))
                except Exception as ins_err:
                    print(f"[report_generator] insight item error: {ins_err}")
        else:
            story.append(Paragraph("<i>Belum ada insight otomatis yang dirumuskan untuk dataset ini.</i>", body_style))

        story.append(Spacer(1, 10))
    except Exception as e:
        print(f"[report_generator] section 5 error: {e}")
        story.append(Paragraph("5. INSIGHT — N/A", body_style))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — Rekomendasi
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("6. REKOMENDASI STRATEGIS PENGAMBILAN KEPUTUSAN", h1_style))
        recoms = []

        summary = quality_report.get('summary', {})
        total_missing  = summary.get('missing_cells', 0)
        total_outliers = summary.get('total_outliers', 0)
        total_dups     = summary.get('duplicate_rows', 0)

        if total_missing and int(total_missing) > 0:
            recoms.append(
                "<b>Penguatan Validasi Input Data:</b> Ditemukannya sel kosong (missing cells) menandakan "
                "perlunya integrasi pengecekan validitas (field validation) pada formulir pengisian data "
                "untuk memastikan tidak ada field kritis yang dikirimkan dalam keadaan kosong."
            )
        if total_outliers and int(total_outliers) > 0:
            recoms.append(
                "<b>Investigasi Nilai Anomali (Outliers):</b> Ditemukan beberapa data pencilan ekstrem. "
                "Disarankan tim operasional memvalidasi apakah angka tersebut valid karena fluktuasi riil bisnis "
                "atau human error, sebelum melakukan pemodelan prediktif lanjutan."
            )
        if total_dups and int(total_dups) > 0:
            recoms.append(
                "<b>Pencegahan Duplikasi Data:</b> Terdapat entri baris ganda. Tim IT disarankan memvalidasi "
                "primary key atau constraint keunikan pada basis data transaksional agar duplikasi tidak berulang."
            )

        # Skewness-based recommendation
        try:
            high_skew_cols = []
            for ns in (num_stats or []):
                val = ns.get('Skewness', 'N/A')
                if val != 'N/A':
                    if abs(float(val)) > 1.0:
                        high_skew_cols.append(ns['Column'])
            if high_skew_cols:
                cols_str = ", ".join(high_skew_cols)
                recoms.append(
                    f"<b>Transformasi Skewness Data:</b> Kolom ({cols_str}) memiliki kemiringan distribusi tinggi (skewed). "
                    "Sebelum menerapkan algoritma berbasis asumsi distribusi normal, lakukan transformasi logaritma atau Box-Cox "
                    "agar hasil prediksi memiliki bias minimal."
                )
        except Exception:
            pass

        recoms.append(
            "<b>Pembersihan Berkala (Data Governance):</b> Jadwalkan proses pembersihan data secara rutin "
            "menggunakan DS Generator sebelum laporan akhir bulan diekspor ke departemen eksekutif, "
            "guna menjamin keputusan dibuat berdasarkan data yang higienis dan terpercaya."
        )

        recoms_html = ""
        for idx, rec in enumerate(recoms):
            recoms_html += f"<b>R{idx + 1}.</b> {rec}<br/><br/>"

        story.append(Paragraph(recoms_html, body_style))
        story.append(PageBreak())
    except Exception as e:
        print(f"[report_generator] section 6 error: {e}")
        story.append(Paragraph("6. REKOMENDASI — N/A", body_style))
        story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7 — Data Health per-column table
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("7. DATA HEALTH & COLUMN DETAILS", h1_style))
        columns_detail = quality_report.get('columns', [])
        if columns_detail:
            col_headers = [
                Paragraph("Column Name", th_style),
                Paragraph("Type", th_style),
                Paragraph("Missing (%)", th_style),
                Paragraph("Unique", th_style),
                Paragraph("Outliers", th_style),
                Paragraph("Status / Issues", th_style),
            ]
            col_rows = [col_headers]
            for c in columns_detail:
                try:
                    status_text = c.get('issues', 'OK')
                    if status_text == 'OK':
                        status_p = Paragraph("<font color='#38a169'><b>OK</b></font>", td_style)
                    else:
                        status_p = Paragraph(f"<font color='#e53e3e'><b>{status_text}</b></font>", td_style)

                    col_rows.append([
                        Paragraph(str(c.get('column', '')), td_style),
                        Paragraph(str(c.get('dtype', '')), td_style),
                        Paragraph(f"{c.get('missing', 0)} ({c.get('missing_pct', 0)}%)", td_style),
                        Paragraph(str(c.get('unique', '')), td_style),
                        Paragraph(str(c.get('outliers', 0)), td_style),
                        status_p,
                    ])
                except Exception as row_err:
                    print(f"[report_generator] col detail row error: {row_err}")
                    col_rows.append([Paragraph("N/A", td_style)] * 6)

            col_table = Table(col_rows, colWidths=[120, 65, 80, 50, 55, 134])
            col_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111c44')),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
            ]))
            story.append(col_table)
        else:
            story.append(Paragraph("<i>Data kolom tidak tersedia.</i>", body_style))

        story.append(PageBreak())
    except Exception as e:
        print(f"[report_generator] section 7 error: {e}")
        story.append(Paragraph("7. DATA HEALTH — N/A", body_style))
        story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 8 — Numerical Descriptive Stats
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("8. STATISTIK DESKRIPTIF — VARIABEL NUMERIK", h1_style))
        if num_stats:
            num_headers = [
                Paragraph("Column", th_style),
                Paragraph("Mean", th_style),
                Paragraph("Median", th_style),
                Paragraph("Min", th_style),
                Paragraph("Max", th_style),
                Paragraph("Std Dev", th_style),
                Paragraph("Mode", th_style),
                Paragraph("Skewness", th_style),
                Paragraph("Normality", th_style),
            ]
            num_rows = [num_headers]
            for ns in num_stats:
                try:
                    num_rows.append([
                        Paragraph(str(ns.get('Column', '')),   td_style),
                        Paragraph(str(ns.get('Mean', 'N/A')),   td_style),
                        Paragraph(str(ns.get('Median', 'N/A')), td_style),
                        Paragraph(str(ns.get('Min', 'N/A')),    td_style),
                        Paragraph(str(ns.get('Max', 'N/A')),    td_style),
                        Paragraph(str(ns.get('Std Dev', 'N/A')),td_style),
                        Paragraph(str(ns.get('Mode', 'N/A')),   td_style),
                        Paragraph(str(ns.get('Skewness', 'N/A')),td_style),
                        Paragraph(str(ns.get('Normality', 'N/A')),td_style),
                    ])
                except Exception:
                    num_rows.append([Paragraph("N/A", td_style)] * 9)

            num_table = Table(num_rows, colWidths=[90, 52, 52, 46, 46, 52, 46, 56, 64])
            num_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111c44')),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
            ]))
            story.append(num_table)
        else:
            story.append(Paragraph("<i>Tidak ada kolom numerik di dataset ini.</i>", body_style))

        story.append(Spacer(1, 10))
    except Exception as e:
        print(f"[report_generator] section 8 error: {e}")
        story.append(Paragraph("8. STATISTIK NUMERIK — N/A", body_style))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 9 — Categorical Descriptive Stats
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("9. STATISTIK DESKRIPTIF — VARIABEL KATEGORIKAL", h1_style))
        if cat_stats:
            cat_headers = [
                Paragraph("Column", th_style),
                Paragraph("Unique", th_style),
                Paragraph("Mode (Most Freq)", th_style),
                Paragraph("Mode Freq", th_style),
                Paragraph("Mode %", th_style),
                Paragraph("Missing", th_style),
                Paragraph("Missing %", th_style),
            ]
            cat_rows = [cat_headers]
            for cs in cat_stats:
                try:
                    cat_rows.append([
                        Paragraph(str(cs.get('Column', '')),       td_style),
                        Paragraph(str(cs.get('Unique', '')),        td_style),
                        Paragraph(str(cs.get('Mode', 'N/A')),       td_style),
                        Paragraph(str(cs.get('Mode Freq', '')),     td_style),
                        Paragraph(str(cs.get('Mode %', '')),        td_style),
                        Paragraph(str(cs.get('Missing Count', '')), td_style),
                        Paragraph(str(cs.get('Missing %', '')),     td_style),
                    ])
                except Exception:
                    cat_rows.append([Paragraph("N/A", td_style)] * 7)

            cat_table = Table(cat_rows, colWidths=[110, 48, 134, 58, 50, 52, 52])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111c44')),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
            ]))
            story.append(cat_table)
        else:
            story.append(Paragraph("<i>Tidak ada kolom kategorikal di dataset ini.</i>", body_style))

        story.append(PageBreak())
    except Exception as e:
        print(f"[report_generator] section 9 error: {e}")
        story.append(Paragraph("9. STATISTIK KATEGORIKAL — N/A", body_style))
        story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 10 — Before vs After Cleaning
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("10. PERBANDINGAN METRIK SEBELUM & SESUDAH CLEANING", h1_style))
        sb = cleaning_summary or {}
        rows_b   = sb.get('rows_before', len(df))
        rows_a   = sb.get('rows_after', len(df))
        cols_b   = sb.get('cols_before', len(df.columns))
        cols_a   = sb.get('cols_after', len(df.columns))
        miss_b   = sb.get('missing_before', 0)
        miss_a   = sb.get('missing_after', 0)
        miss_p_b = sb.get('missing_pct_before', 0.0)
        miss_p_a = sb.get('missing_pct_after', 0.0)
        dups_rem = sb.get('duplicates_removed', 0)

        diff_data = [
            [Paragraph("<b>Metrik</b>", th_style), Paragraph("<b>Sebelum (Raw)</b>", th_style),
             Paragraph("<b>Sesudah (Cleaned)</b>", th_style), Paragraph("<b>Perubahan</b>", th_style)],
            [Paragraph("Jumlah Baris", td_style), Paragraph(str(rows_b), td_style), Paragraph(str(rows_a), td_style), Paragraph(f"Dihapus: {rows_b - rows_a} baris", td_style)],
            [Paragraph("Jumlah Kolom", td_style), Paragraph(str(cols_b), td_style), Paragraph(str(cols_a), td_style), Paragraph(f"Dihapus: {cols_b - cols_a} kolom", td_style)],
            [Paragraph("Sel Kosong", td_style),   Paragraph(f"{miss_b} ({miss_p_b}%)", td_style), Paragraph(f"{miss_a} ({miss_p_a}%)", td_style), Paragraph(f"Diisi/hapus: {miss_b - miss_a} sel", td_style)],
            [Paragraph("Baris Duplikat", td_style), Paragraph(str(dups_rem), td_style), Paragraph("0", td_style), Paragraph("Duplikasi 100% dihilangkan", td_style)],
        ]
        diff_table = Table(diff_data, colWidths=[174, 100, 100, 130])
        diff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111c44')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(diff_table)
        story.append(Spacer(1, 10))
    except Exception as e:
        print(f"[report_generator] section 10 error: {e}")
        story.append(Paragraph("10. PERBANDINGAN CLEANING — N/A", body_style))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 11 — Cleaning Log
    # ══════════════════════════════════════════════════════════════════════════
    try:
        story.append(Paragraph("11. LOG TINDAKAN PEMBERSIHAN DETIL PER KOLOM", h1_style))
        cleaning_logs = (cleaning_summary or {}).get('log', [])
        if cleaning_logs:
            log_rows = [[Paragraph("<b>Keterangan Modifikasi</b>", th_style)]]
            for log_item in cleaning_logs:
                log_rows.append([Paragraph(f"• {log_item}", td_style)])
            log_table = Table(log_rows, colWidths=[504])
            log_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(log_table)
        else:
            story.append(Paragraph(
                "<i>Belum ada tindakan cleaning spesifik. Data masih dalam kondisi awal.</i>",
                body_style,
            ))
    except Exception as e:
        print(f"[report_generator] section 11 error: {e}")
        story.append(Paragraph("11. LOG CLEANING — N/A", body_style))

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(
        story,
        canvasmaker=NumberedCanvas,
        onFirstPage=draw_watermark,
        onLaterPages=draw_watermark,
    )
