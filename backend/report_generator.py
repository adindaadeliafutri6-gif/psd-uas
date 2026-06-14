"""
backend/report_generator.py
<<<<<<< HEAD
─────────────────────────────────────────────────────────────────────────────
Comprehensive PDF Report Generator — Auto-EDA Dashboard (Kelompok 2 ITSB)

Sections (ordered):
  1. Deskripsi Web   — Penjelasan fungsionalitas dashboard
  2. Member          — Daftar anggota Kelompok 2 ITSB
  3. Deskripsi Data  — Ringkasan statistik (dimensi, tipe, status cleaning)
  4. Visual          — Histogram & Heatmap dari viz_engine / matplotlib
  5. Insight         — Analisis singkat (tren, korelasi, distribusi)
  6. Rekomendasi     — Saran strategis berbasis insight

Fixes:
  - TypeError 'list indices must be integers or slices, not str'
    → uses quality_full (dict from get_quality_report) instead of
      quality_report (list from analyze_quality)
  - Every section wrapped in try-except → graceful N/A fallback
  - Watermark 'CONFIDENTIAL - Kelompok 2 ITSB' on every page

Dependencies: reportlab, matplotlib (optional fallback for images)
─────────────────────────────────────────────────────────────────────────────
=======
Comprehensive PDF Report Generator — DS Generator | Kelompok 2 ITSB

Supports:
  - Full descriptive stats table (numerical + categorical)
  - Data quality summary with KPI boxes
  - Embedded static visualizations (Histogram + Correlation Heatmap)
  - Auto-generated insights and strategic recommendations
  - Diagonal CONFIDENTIAL watermark on every page
  - Two-pass NumberedCanvas for "Page X of Y" footer
  - Robust try-except: every section degrades gracefully, PDF never crashes
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
"""

import os
import io
import datetime
<<<<<<< HEAD
import traceback
=======
import tempfile
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854

import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
<<<<<<< HEAD
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether,
=======
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image,
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


<<<<<<< HEAD
# ─────────────────────────────────────────────────────────────────────────────
# NumberedCanvas — two-pass pattern for 'Page X of Y' + header/footer
# ─────────────────────────────────────────────────────────────────────────────

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that counts total pages and draws header/footer/watermark.
    Watermark: 'CONFIDENTIAL - Kelompok 2 ITSB' — transparent, diagonal.
=======
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
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
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
<<<<<<< HEAD
            self._draw_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_decorations(self, page_count):
=======
            self._draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_page_decorations(self, page_count):
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
        self.saveState()

        # ── Watermark (every page, behind content) ──────────────────────────
        self.setFont('Helvetica-Bold', 52)
        self.setFillColor(colors.Color(0.75, 0.75, 0.80, alpha=0.10))
        self.translate(306, 396)
        self.rotate(38)
        self.drawCentredString(0, 0, "CONFIDENTIAL")
        self.setFont('Helvetica', 14)
        self.setFillColor(colors.Color(0.75, 0.75, 0.80, alpha=0.12))
        self.drawCentredString(0, -42, "Kelompok 2 ITSB")
        self.rotate(-38)
        self.translate(-306, -396)

        # ── Header (pages 2+) ────────────────────────────────────────────────
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#a3aed0"))
<<<<<<< HEAD
        if self._pageNumber > 1:
            self.drawString(54, 750, "Auto-EDA Dashboard Report  —  Kelompok 2 ITSB")
=======

        # Header (skip cover page)
        if self._pageNumber > 1:
            self.drawString(54, 750, "DS Generator Report — Kelompok 2 ITSB")
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
            self.setStrokeColor(colors.HexColor("#e0e5f2"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

<<<<<<< HEAD
        # ── Footer ───────────────────────────────────────────────────────────
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(
            54, 40,
            f"Auto-EDA Report | Generated: {datetime.datetime.now().strftime('%d %b %Y %H:%M')}"
        )
=======
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        date_str = datetime.datetime.now().strftime('%d %b %Y')
        self.drawString(54, 40, f"Descriptive Statistics & Quality Report | Generated: {date_str}")
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
        self.setStrokeColor(colors.HexColor("#e0e5f2"))
        self.setLineWidth(0.5)
        self.line(54, 52, 558, 52)

        self.restoreState()


<<<<<<< HEAD
# ─────────────────────────────────────────────────────────────────────────────
# Defensive access helpers — never crash on missing/wrong-type keys
# ─────────────────────────────────────────────────────────────────────────────

def _safe_get(obj, key, default=None):
    """Safely get a key from a dict-like object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _safe_summary(quality_full):
    """Return the 'summary' sub-dict from quality_full, or empty dict."""
    return _safe_get(quality_full, 'summary', {})


def _safe_columns(quality_full):
    """Return the 'columns' list from quality_full, or empty list."""
    cols = _safe_get(quality_full, 'columns', [])
    return cols if isinstance(cols, list) else []


def _safe_warnings(quality_full):
    """Return the 'warnings' list from quality_full, or empty list."""
    warns = _safe_get(quality_full, 'warnings', [])
    return warns if isinstance(warns, list) else []


# ─────────────────────────────────────────────────────────────────────────────
# Image helpers — load from path or generate with matplotlib fallback
# ─────────────────────────────────────────────────────────────────────────────

def _try_load_image(image_path, max_width=500, max_height=300):
    """
    Load an image file and return a ReportLab Image flowable,
    scaled proportionally to fit within max_width x max_height.
    Returns None on failure.
    """
    if not image_path or not os.path.isfile(image_path):
        return None
    try:
        from PIL import Image as PILImage
        pil_img = PILImage.open(image_path)
        w, h = pil_img.size
        if w == 0 or h == 0:
            return None
        scale = min(max_width / w, max_height / h, 1.0)
        return RLImage(image_path, width=w * scale, height=h * scale)
    except Exception:
        return None


def _generate_histogram_image(df, num_cols):
    """Generate a histogram PNG in memory using matplotlib; return BytesIO or None."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        col = num_cols[0] if num_cols else None
        if not col or col not in df.columns:
            return None

        series = pd.to_numeric(df[col], errors='coerce').dropna()
        if series.empty:
            return None

        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=100)
        ax.hist(series, bins=25, color='#4ECDC4', edgecolor='white', alpha=0.85)
        ax.set_title(f'Histogram: {col}', fontsize=10, color='#1b254b')
        ax.set_xlabel(col, fontsize=8)
        ax.set_ylabel('Frequency', fontsize=8)
        ax.tick_params(labelsize=7)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        return None


def _generate_heatmap_image(df, num_cols):
    """Generate a correlation heatmap PNG in memory; return BytesIO or None."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        valid = [c for c in num_cols[:10] if c in df.columns]
        if len(valid) < 2:
            return None

        df_num = df[valid].apply(pd.to_numeric, errors='coerce').dropna()
        if df_num.empty or df_num.shape[1] < 2:
            return None

        corr = df_num.corr()
        fig, ax = plt.subplots(figsize=(6, 4.5), dpi=100)
        im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha='right', fontsize=7)
        ax.set_yticklabels(corr.columns, fontsize=7)
        ax.set_title('Correlation Heatmap', fontsize=10, color='#1b254b')
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────

def _build_styles():
    """Build and return all ParagraphStyle objects used in the report."""
    base = getSampleStyleSheet()

    def _make(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)

    return {
        'title': _make(
            'CoverTitle',
            fontName='Helvetica-Bold', fontSize=20, leading=24,
            textColor=colors.HexColor('#1b254b'), spaceAfter=6,
        ),
        'subtitle': _make(
            'CoverSubtitle',
            fontName='Helvetica', fontSize=11, leading=15,
            textColor=colors.HexColor('#4318ff'), spaceAfter=15,
        ),
        'h1': _make(
            'H1',
            fontName='Helvetica-Bold', fontSize=12, leading=15,
            textColor=colors.HexColor('#1b254b'), spaceBefore=14,
            spaceAfter=8, keepWithNext=True,
        ),
        'h2': _make(
            'H2',
            fontName='Helvetica-Bold', fontSize=10, leading=13,
            textColor=colors.HexColor('#4318ff'), spaceBefore=10,
            spaceAfter=5, keepWithNext=True,
        ),
        'body': _make(
            'Body',
            fontName='Helvetica', fontSize=8.5, leading=12,
            textColor=colors.HexColor('#4a5568'), spaceAfter=6,
        ),
        'th': _make(
            'TH',
            fontName='Helvetica-Bold', fontSize=8, leading=10,
            textColor=colors.white,
        ),
        'td': _make(
            'TD',
            fontName='Helvetica', fontSize=7.5, leading=9,
            textColor=colors.HexColor('#1b254b'),
        ),
        'warn': _make(
            'Warn',
            fontName='Helvetica', fontSize=8, leading=10,
            textColor=colors.HexColor('#856404'),
        ),
        'na': _make(
            'NA',
            fontName='Helvetica-Oblique', fontSize=8.5, leading=11,
            textColor=colors.HexColor('#a0aec0'), spaceAfter=4,
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Table style presets
# ─────────────────────────────────────────────────────────────────────────────

HEADER_BG  = colors.HexColor('#111c44')
ALT_ROW    = [colors.white, colors.HexColor('#f8f9fa')]
GRID_COLOR = colors.HexColor('#e2e8f0')


def _header_table_style():
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), HEADER_BG),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), ALT_ROW),
        ('GRID',          (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf_report(
    dest_path,
    filename,
    df,
    quality_full,
    metrics,
    num_stats,
    cat_stats,
    auto_insights,
    cleaning_history,
    cleaning_summary,
    image_paths=None,
):
    """
    Generates a comprehensive PDF report with the following sections:
      1. Deskripsi Web    2. Member    3. Deskripsi Data
      4. Visual           5. Insight   6. Rekomendasi

    Parameters
    ----------
    dest_path      : str   — absolute output PDF path
    filename       : str   — dataset filename (for display)
    df             : pd.DataFrame — current (cleaned or raw) DataFrame
    quality_full   : dict  — from get_quality_report(); keys: summary, columns, warnings
    metrics        : dict  — from get_summary_metrics()
    num_stats      : list  — descriptive stats for numeric columns
    cat_stats      : list  — descriptive stats for categorical columns
    auto_insights  : list  — from generate_auto_insights()
    cleaning_history : list — cleaning pipeline labels
    cleaning_summary : dict — before/after cleaning metrics
    image_paths    : dict  — optional {'histogram': path, 'heatmap': path}
    """

    # ── Document setup ───────────────────────────────────────────────────────
=======
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
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
    doc = SimpleDocTemplate(
        dest_path,
        pagesize=letter,
        leftMargin=54, rightMargin=54,
<<<<<<< HEAD
        topMargin=72,  bottomMargin=72,
=======
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
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
    )

    S = _build_styles()
    story = []

<<<<<<< HEAD
    # ── Cover banner ─────────────────────────────────────────────────────────
    try:
        banner_data = [[Paragraph(
            "AUTO-EDA DASHBOARD  ·  DATA SCIENCE GENERATOR SYSTEM",
            ParagraphStyle('Banner', fontName='Helvetica-Bold',
                           fontSize=10, textColor=colors.white, leading=12),
        )]]
        banner = Table(banner_data, colWidths=[504])
        banner.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#4318ff')),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(banner)
        story.append(Spacer(1, 15))
    except Exception:
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1 · DESKRIPSI WEB
    # ─────────────────────────────────────────────────────────────────────────
    try:
        story.append(Paragraph("1. TENTANG AUTO-EDA DASHBOARD", S['h1']))
        desc_web = (
            "<b>Auto-EDA Dashboard (DS Generator)</b> adalah platform analisis data otomatis "
            "berbasis web yang dikembangkan oleh <b>Kelompok 2 Data Science ITSB</b>. "
            "Aplikasi ini dirancang untuk membantu analis data, manajer, dan pengambil keputusan "
            "bisnis dalam melakukan: (1) unggah dan validasi dataset, (2) audit kesehatan data "
            "(quality audit), (3) pembersihan data interaktif (data cleaning), (4) perhitungan "
            "statistik deskriptif dan lanjutan, (5) visualisasi pola data secara interaktif, "
            "serta (6) perumusan insight dan rekomendasi strategis berbasis data secara otomatis "
            "dan real-time."
        )
        story.append(Paragraph(desc_web, S['body']))
        story.append(Spacer(1, 8))
    except Exception:
        story.append(Paragraph("<i>[Bagian Deskripsi Web tidak dapat dimuat]</i>", S['na']))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2 · MEMBER
    # ─────────────────────────────────────────────────────────────────────────
    try:
        story.append(Paragraph("2. ANGGOTA TIM PENGEMBANG (KELOMPOK 2 ITSB)", S['h1']))
        members = [
            [Paragraph("<b>Nama Lengkap</b>",            S['th']),
             Paragraph("<b>NIM</b>",                      S['th']),
             Paragraph("<b>Peran / Fokus Analisis</b>",   S['th'])],
            [Paragraph("Carol Dupino Pereira",           S['td']),
             Paragraph("52250051",                        S['td']),
             Paragraph("Descriptive & Advanced Statistics Engine", S['td'])],
            [Paragraph("Refantanur Husnul Haqib",        S['td']),
             Paragraph("52250052",                        S['td']),
             Paragraph("Visualizations & Dynamic Plotly Dashboard", S['td'])],
            [Paragraph("Cahaya Medina Semidang",         S['td']),
             Paragraph("52250053",                        S['td']),
             Paragraph("Data Preprocessing & Sanitizer Module", S['td'])],
            [Paragraph("Raihania Syah Putri",            S['td']),
             Paragraph("52250054",                        S['td']),
             Paragraph("Time Series Forecasting & Trends Panel", S['td'])],
            [Paragraph("Cloise Shafira",                 S['td']),
             Paragraph("52250044",                        S['td']),
             Paragraph("Smart Insights Generation Algorithm", S['td'])],
            [Paragraph("Adinda Adelia Futri",            S['td']),
             Paragraph("52250055",                        S['td']),
             Paragraph("Reporting System PDF/Excel & Security Sanitization", S['td'])],
        ]
        mt = Table(members, colWidths=[180, 100, 224])
        mt.setStyle(_header_table_style())
        story.append(mt)
        story.append(PageBreak())
    except Exception:
        story.append(Paragraph("<i>[Bagian Member tidak dapat dimuat]</i>", S['na']))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3 · DESKRIPSI DATA
    # ─────────────────────────────────────────────────────────────────────────
    try:
        story.append(Paragraph("3. DESKRIPSI DATA & RINGKASAN EKSEKUTIF", S['h1']))

        summary  = _safe_summary(quality_full)
        needs_cleaning = summary.get('needs_cleaning', True)
        status_label = "RAW DATA (Perlu Pembersihan)" if needs_cleaning else "CLEAN DATA (Bersih)"
        status_color = "#e53e3e" if needs_cleaning else "#38a169"

        total_rows    = summary.get('total_rows',    _safe_get(metrics, 'total_rows',    len(df)))
        total_cols    = summary.get('total_cols',
                        summary.get('total_columns', _safe_get(metrics, 'total_columns', len(df.columns))))
        missing_cells = summary.get('missing_cells', 0)
        missing_pct   = summary.get('missing_pct',   0.0)
        duplicate_rows= summary.get('duplicate_rows',0)
        total_outliers= summary.get('total_outliers',0)

        meta_info = [
            [Paragraph("<b>Nama File Dataset:</b>",        S['body']),
             Paragraph(filename,                            S['body'])],
            [Paragraph("<b>Waktu Analisis:</b>",           S['body']),
             Paragraph(datetime.datetime.now().strftime('%d %B %Y, %H:%M:%S'), S['body'])],
            [Paragraph("<b>Status Kebersihan:</b>",        S['body']),
             Paragraph(f"<font color='{status_color}'><b>{status_label}</b></font>", S['body'])],
            [Paragraph("<b>Total Baris (Observasi):</b>",  S['body']),
             Paragraph(str(total_rows),                     S['body'])],
            [Paragraph("<b>Total Kolom (Variabel):</b>",   S['body']),
             Paragraph(str(total_cols),                     S['body'])],
            [Paragraph("<b>Variabel Numerik:</b>",         S['body']),
             Paragraph(str(_safe_get(metrics, 'num_count', 0)), S['body'])],
            [Paragraph("<b>Variabel Kategorikal:</b>",     S['body']),
             Paragraph(str(_safe_get(metrics, 'cat_count', 0)), S['body'])],
        ]
        meta_table = Table(meta_info, colWidths=[150, 354])
        meta_table.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('LINEBELOW',     (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # KPI Box
        kpis = [
            [Paragraph("<b>Missing Cells</b>",   S['th']),
             Paragraph("<b>Duplicate Rows</b>",  S['th']),
             Paragraph("<b>IQR Outliers</b>",    S['th'])],
            [Paragraph(
                f"<font size=11 color='#2d3748'><b>{missing_cells}</b></font>"
                f"<br/><font size=7 color='#718096'>({missing_pct}%)</font>", S['body']),
             Paragraph(f"<font size=11 color='#2d3748'><b>{duplicate_rows}</b></font>", S['body']),
             Paragraph(f"<font size=11 color='#2d3748'><b>{total_outliers}</b></font>", S['body'])],
        ]
        kpi_table = Table(kpis, colWidths=[168, 168, 168])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX',           (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('INNERGRID',     (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
=======
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
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 10))

<<<<<<< HEAD
        # Warnings
        warnings = _safe_warnings(quality_full)
        if warnings:
            story.append(Paragraph("Identifikasi Masalah Kualitas Data:", S['h2']))
            warn_rows = [[Paragraph("•", S['warn']), Paragraph(w, S['warn'])] for w in warnings]
            wt = Table(warn_rows, colWidths=[15, 489])
            wt.setStyle(TableStyle([
                ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
                ('BOX',           (0, 0), (-1, -1), 0.5, colors.HexColor('#ffeeba')),
                ('TOPPADDING',    (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(wt)
            story.append(Spacer(1, 8))

        # Column health table
        columns_info = _safe_columns(quality_full)
        if columns_info:
            story.append(Paragraph("Detail Kesehatan Per Kolom:", S['h2']))
            col_rows = [[
                Paragraph("Kolom",       S['th']),
                Paragraph("Tipe",        S['th']),
                Paragraph("Missing (%)", S['th']),
                Paragraph("Unique",      S['th']),
                Paragraph("Outliers",    S['th']),
                Paragraph("Status",      S['th']),
            ]]
            for c in columns_info:
                if not isinstance(c, dict):
                    continue
                issues    = c.get('issues', 'OK')
                status_p  = (
                    Paragraph("<font color='#38a169'><b>OK</b></font>", S['td'])
                    if issues == 'OK' else
                    Paragraph(f"<font color='#e53e3e'><b>{issues}</b></font>", S['td'])
                )
                col_rows.append([
                    Paragraph(str(c.get('column', '')),                       S['td']),
                    Paragraph(str(c.get('dtype', '')),                        S['td']),
                    Paragraph(f"{c.get('missing', 0)} ({c.get('missing_pct', 0)}%)", S['td']),
                    Paragraph(str(c.get('unique', 0)),                        S['td']),
                    Paragraph(str(c.get('outliers', 0)),                      S['td']),
                    status_p,
                ])
            ct = Table(col_rows, colWidths=[110, 65, 85, 50, 55, 139])
            ct.setStyle(_header_table_style())
            story.append(ct)

        story.append(PageBreak())
    except Exception:
        story.append(Paragraph("<i>[Bagian Deskripsi Data tidak dapat dimuat — N/A]</i>", S['na']))
        story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3b · DATA CLEANING PIPELINE & BEFORE/AFTER (kept from original)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        story.append(Paragraph("3a. ALUR PROSES DATA CLEANING (PIPELINE)", S['h1']))
        flow_desc = (
            "Dataset diproses melalui 5 tahapan alur data cleaning di backend engine:<br/><br/>"
            "<b>1. Audit Kesehatan (Data Profiling):</b> Mendeteksi sel kosong (NaN), "
            "baris duplikat, inkonsistensi teks, dan outlier numerik (IQR).<br/>"
            "<b>2. Standarisasi Teks:</b> Menghilangkan spasi berlebih dan menyeragamkan "
            "bentuk huruf (Title/Lower/Upper Case).<br/>"
            "<b>3. Imputasi Data Hilang:</b> Mengisi sel kosong dengan mean/median/modus "
            "atau menghapus baris jika kerusakan ekstrem.<br/>"
            "<b>4. Pembersihan Outlier (IQR Capping):</b> Menetralkan nilai ekstrim "
            "menggunakan batas IQR.<br/>"
            "<b>5. Drop Kolom Tidak Relevan:</b> Menghapus kolom variansi nol atau "
            "rasio keunikan terlalu tinggi (ID/teks acak)."
        )
        story.append(Paragraph(flow_desc, S['body']))
        story.append(Spacer(1, 10))

        # Before / After table
        if isinstance(cleaning_summary, dict):
            sb     = cleaning_summary
            rows_b = sb.get('rows_before',  len(df))
            rows_a = sb.get('rows_after',   len(df))
            cols_b = sb.get('cols_before',  len(df.columns))
            cols_a = sb.get('cols_after',   len(df.columns))
            miss_b = sb.get('missing_before', 0)
            miss_a = sb.get('missing_after',  0)
            mp_b   = sb.get('missing_pct_before', 0.0)
            mp_a   = sb.get('missing_pct_after',  0.0)
            dups   = sb.get('duplicates_removed', 0)

            diff_data = [
                [Paragraph("<b>Metrik</b>",             S['th']),
                 Paragraph("<b>Sebelum (Raw)</b>",      S['th']),
                 Paragraph("<b>Sesudah (Cleaned)</b>",  S['th']),
                 Paragraph("<b>Perubahan</b>",          S['th'])],
                [Paragraph("Baris Data",        S['td']),
                 Paragraph(str(rows_b),         S['td']),
                 Paragraph(str(rows_a),         S['td']),
                 Paragraph(f"Dihapus: {rows_b - rows_a} baris", S['td'])],
                [Paragraph("Kolom Data",        S['td']),
                 Paragraph(str(cols_b),         S['td']),
                 Paragraph(str(cols_a),         S['td']),
                 Paragraph(f"Dihapus: {cols_b - cols_a} kolom", S['td'])],
                [Paragraph("Sel Kosong",        S['td']),
                 Paragraph(f"{miss_b} ({mp_b}%)", S['td']),
                 Paragraph(f"{miss_a} ({mp_a}%)", S['td']),
                 Paragraph(f"Dibersihkan: {miss_b - miss_a} sel", S['td'])],
            ]
            dt = Table(diff_data, colWidths=[130, 120, 120, 134])
            dt.setStyle(_header_table_style())
            story.append(dt)
            story.append(Spacer(1, 8))

            # Cleaning log
            cleaning_logs = sb.get('log', [])
            if cleaning_logs:
                story.append(Paragraph("Log Tindakan Cleaning:", S['h2']))
                log_rows = [[Paragraph(f"• {l}", S['td'])] for l in cleaning_logs]
                lt = Table(log_rows, colWidths=[504])
                lt.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                    ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
                ]))
                story.append(lt)
    except Exception:
        story.append(Paragraph("<i>[Bagian Cleaning Pipeline tidak dapat dimuat — N/A]</i>", S['na']))

    # ── Descriptive stats: Numeric ────────────────────────────────────────────
    try:
        story.append(Spacer(1, 10))
        story.append(Paragraph("3b. Statistik Deskriptif — Variabel Numerik", S['h2']))
        if num_stats:
            nh = [Paragraph(h, S['th']) for h in
                  ["Kolom", "Mean", "Median", "Min", "Max", "Std Dev", "Skewness", "Normality"]]
            n_rows = [nh]
            for ns in num_stats:
                if not isinstance(ns, dict):
                    continue
                n_rows.append([
                    Paragraph(str(ns.get('Column', '')),    S['td']),
                    Paragraph(str(ns.get('Mean', 'N/A')),   S['td']),
                    Paragraph(str(ns.get('Median', 'N/A')), S['td']),
                    Paragraph(str(ns.get('Min', 'N/A')),    S['td']),
                    Paragraph(str(ns.get('Max', 'N/A')),    S['td']),
                    Paragraph(str(ns.get('Std Dev', 'N/A')),S['td']),
                    Paragraph(str(ns.get('Skewness', 'N/A')), S['td']),
                    Paragraph(str(ns.get('Normality', 'N/A')),S['td']),
                ])
            nt = Table(n_rows, colWidths=[90, 55, 55, 48, 48, 55, 55, 98])
            nt.setStyle(_header_table_style())
            story.append(nt)
        else:
            story.append(Paragraph("<i>Tidak ada kolom numerik.</i>", S['na']))
    except Exception:
        story.append(Paragraph("<i>[Statistik numerik tidak tersedia — N/A]</i>", S['na']))

    # ── Descriptive stats: Categorical ────────────────────────────────────────
    try:
        story.append(Spacer(1, 10))
        story.append(Paragraph("3c. Statistik Deskriptif — Variabel Kategorikal", S['h2']))
        if cat_stats:
            ch = [Paragraph(h, S['th']) for h in
                  ["Kolom", "Unique", "Mode", "Mode Freq", "Mode %", "Missing", "Missing %"]]
            c_rows = [ch]
            for cs in cat_stats:
                if not isinstance(cs, dict):
                    continue
                c_rows.append([
                    Paragraph(str(cs.get('Column', '')),        S['td']),
                    Paragraph(str(cs.get('Unique', 'N/A')),     S['td']),
                    Paragraph(str(cs.get('Mode', 'N/A')),       S['td']),
                    Paragraph(str(cs.get('Mode Freq', 'N/A')),  S['td']),
                    Paragraph(str(cs.get('Mode %', 'N/A')),     S['td']),
                    Paragraph(str(cs.get('Missing Count', 'N/A')), S['td']),
                    Paragraph(str(cs.get('Missing %', 'N/A')),  S['td']),
                ])
            ct2 = Table(c_rows, colWidths=[100, 50, 124, 60, 55, 55, 60])
            ct2.setStyle(_header_table_style())
            story.append(ct2)
        else:
            story.append(Paragraph("<i>Tidak ada kolom kategorikal.</i>", S['na']))
        story.append(PageBreak())
    except Exception:
        story.append(Paragraph("<i>[Statistik kategorikal tidak tersedia — N/A]</i>", S['na']))
        story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4 · VISUAL (Histogram & Heatmap)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        story.append(Paragraph("4. VISUALISASI KUNCI (HISTOGRAM & HEATMAP)", S['h1']))

        image_paths = image_paths or {}
        hist_path   = image_paths.get('histogram')
        heat_path   = image_paths.get('heatmap')

        # Detect numeric columns for fallback generation
        num_cols_list = [
            c for c in df.select_dtypes(include='number').columns
            if c in df.columns
        ]

        # Histogram
        story.append(Paragraph("4a. Histogram (Distribusi Variabel Numerik)", S['h2']))
        hist_img = _try_load_image(hist_path) if hist_path else None
        if hist_img is None:
            hist_buf = _generate_histogram_image(df, num_cols_list)
            if hist_buf is not None:
                hist_img = RLImage(hist_buf, width=450, height=262)
        if hist_img is not None:
            story.append(hist_img)
        else:
            story.append(Paragraph("<i>[Histogram tidak dapat dihasilkan — data numerik tidak tersedia]</i>", S['na']))
        story.append(Spacer(1, 10))

        # Heatmap
        story.append(Paragraph("4b. Heatmap Korelasi (Hubungan Antar Variabel)", S['h2']))
        heat_img = _try_load_image(heat_path) if heat_path else None
        if heat_img is None:
            heat_buf = _generate_heatmap_image(df, num_cols_list)
            if heat_buf is not None:
                heat_img = RLImage(heat_buf, width=450, height=337)
        if heat_img is not None:
            story.append(heat_img)
        else:
            story.append(Paragraph(
                "<i>[Heatmap tidak dapat dihasilkan — minimal 2 kolom numerik diperlukan]</i>", S['na']))

        story.append(PageBreak())
    except Exception:
        story.append(Paragraph("<i>[Bagian Visual tidak dapat dimuat — N/A]</i>", S['na']))
        story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5 · INSIGHT
    # ─────────────────────────────────────────────────────────────────────────
    try:
        story.append(Paragraph("5. TEMUAN KUNCI & INSIGHT OTOMATIS", S['h1']))
        if auto_insights:
            for ins in auto_insights:
                if not isinstance(ins, dict):
                    continue
                ins_title = ins.get('title', 'Temuan Data')
                ins_desc  = ins.get('desc', '') or ins.get('description', '')
                ins_type  = ins.get('type', 'info')

                t_color = {
                    'success': '#2f855a', 'warning': '#c05621',
                    'danger':  '#c53030',
                }.get(ins_type, '#2b6cb0')

                story.append(Paragraph(
                    f"<b><font color='{t_color}'>{ins_title}</font></b>", S['h2']))
                story.append(Paragraph(ins_desc, S['body']))
                story.append(Spacer(1, 3))
        else:
            story.append(Paragraph(
                "<i>Belum ada insight otomatis yang dirumuskan untuk dataset ini.</i>", S['na']))
        story.append(Spacer(1, 10))
    except Exception:
        story.append(Paragraph("<i>[Bagian Insight tidak dapat dimuat — N/A]</i>", S['na']))

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 6 · REKOMENDASI
    # ─────────────────────────────────────────────────────────────────────────
    try:
        story.append(Paragraph("6. REKOMENDASI STRATEGIS PENGAMBILAN KEPUTUSAN", S['h1']))
        recoms = []

        summary      = _safe_summary(quality_full)
        total_missing  = summary.get('missing_cells',  0)
        total_outliers = summary.get('total_outliers', 0)
        total_dups     = summary.get('duplicate_rows', 0)

        if total_missing > 0:
            recoms.append(
                "<b>Penguatan Validasi Input Data:</b> Mengingat ditemukannya sel kosong "
                "(missing cells) pada dataset, manajemen harus mengintegrasikan pengecekan "
                "validitas (field validation) pada formulir pengisian data untuk memastikan "
                "tidak ada field kritis yang dikirim dalam keadaan kosong."
            )
        if total_outliers > 0:
            recoms.append(
                "<b>Investigasi Nilai Anomali (Outliers):</b> Ditemukan data pencilan ekstrem. "
                "Disarankan tim operasional memvalidasi apakah angka tersebut valid (fluktuasi "
                "bisnis riil) atau human error. Lakukan capping/truncation sebelum pemodelan "
                "prediktif lanjutan."
            )
        if total_dups > 0:
            recoms.append(
                "<b>Pencegahan Duplikasi Data:</b> Terdapat baris ganda. Tim IT disarankan "
                "memvalidasi primary key atau unique constraint pada basis data transaksional "
                "agar duplikasi tidak terulang."
            )

        # High skewness recommendation
        high_skew_cols = []
        for ns in (num_stats or []):
            if not isinstance(ns, dict):
                continue
            try:
                val = ns.get('Skewness', 'N/A')
                if val != 'N/A' and abs(float(val)) > 1.0:
                    high_skew_cols.append(ns.get('Column', ''))
            except Exception:
                continue

        if high_skew_cols:
            cols_str = ", ".join(filter(None, high_skew_cols))
            recoms.append(
                f"<b>Transformasi Skewness Data:</b> Kolom ({cols_str}) memiliki kemiringan "
                "distribusi tinggi (skewed). Sebelum menerapkan algoritma berbasis distribusi "
                "normal, lakukan transformasi logaritma atau Box-Cox untuk meminimalkan bias."
            )

        recoms.append(
            "<b>Pembersihan Berkala (Data Governance):</b> Jadwalkan proses pembersihan data "
            "secara rutin menggunakan Auto-EDA Dashboard sebelum laporan akhir bulan diekspor "
            "ke departemen eksekutif, guna menjamin keputusan dibuat berdasarkan data higienis."
        )

        recoms_html = "".join(
            f"<b>R{i+1}.</b> {rec}<br/><br/>" for i, rec in enumerate(recoms)
        )
        story.append(Paragraph(recoms_html, S['body']))
    except Exception:
        story.append(Paragraph("<i>[Bagian Rekomendasi tidak dapat dimuat — N/A]</i>", S['na']))
=======
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
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(
        story,
        canvasmaker=NumberedCanvas,
<<<<<<< HEAD
=======
        onFirstPage=draw_watermark,
        onLaterPages=draw_watermark,
>>>>>>> a76182c716ad8f83f17f93003ea34f1d0331f854
    )
