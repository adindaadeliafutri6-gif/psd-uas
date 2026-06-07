"""
backend/visualizations.py
Week 15 — Auto-Visualization Engine
Menghasilkan 6 grafik interaktif Plotly: Histogram, Bar, Boxplot, Heatmap, Scatter Matrix, Pie
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json

COLOR_SEQ = ['#4318ff', '#05cd99', '#ffce20', '#ee5d50', '#868cff', '#ff6b6b', '#4ecdc4']

def _safe_json(fig):
    return json.loads(fig.to_json())

def generate_plots(df, num_cols, cat_cols):
    """Menghasilkan grafik Plotly dalam format JSON untuk dikirim ke template."""
    plots = {}
    layout_base = dict(margin=dict(l=20, r=20, t=45, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # ── 1. HISTOGRAM NUMERIK ──────────────────────────────────────────────────
    if num_cols:
        col = num_cols[0]
        fig = px.histogram(df, x=col, nbins=30, title=f"📊 Distribusi: {col}",
                           template="plotly_white", color_discrete_sequence=['#4318ff'])
        fig.update_traces(marker_line_width=0.5, marker_line_color='white')
        fig.update_layout(**layout_base)
        plots['hist_num'] = _safe_json(fig)

    # ── 2. BAR CHART KATEGORIK ────────────────────────────────────────────────
    if cat_cols:
        col = cat_cols[0]
        vc = df[col].value_counts().reset_index()
        vc.columns = [col, 'Count']
        fig = px.bar(vc.head(10), x=col, y='Count', title=f"📋 Top 10 Kategori: {col}",
                     template="plotly_white", color='Count', color_continuous_scale='Blues')
        fig.update_layout(**layout_base, coloraxis_showscale=False)
        plots['bar_cat'] = _safe_json(fig)

    # ── 3. BOXPLOT (Cat vs Num) ───────────────────────────────────────────────
    if num_cols and cat_cols:
        num_col, cat_col = num_cols[0], cat_cols[0]
        # Batasi jumlah kategori agar tidak penuh
        top_cats = df[cat_col].value_counts().head(8).index
        df_filt = df[df[cat_col].isin(top_cats)]
        fig = px.box(df_filt, x=cat_col, y=num_col,
                     title=f"🔀 {num_col} per {cat_col}",
                     template="plotly_white", color=cat_col,
                     color_discrete_sequence=COLOR_SEQ)
        fig.update_layout(**layout_base, showlegend=False)
        plots['box_cat_num'] = _safe_json(fig)

    # ── 4. HEATMAP KORELASI ───────────────────────────────────────────────────
    if len(num_cols) > 1:
        corr = df[num_cols].corr().round(2)
        fig = px.imshow(corr, text_auto=True, aspect="auto",
                        title="🔥 Correlation Heatmap",
                        color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        fig.update_layout(**layout_base)
        plots['heatmap'] = _safe_json(fig)

    # ── 5. SCATTER MATRIX (jika ≥ 2 num cols) ─────────────────────────────────
    if len(num_cols) >= 2:
        cols_for_scatter = num_cols[:4]  # Max 4 kolom
        color_col = cat_cols[0] if cat_cols else None
        try:
            df_scatter = df[cols_for_scatter + ([color_col] if color_col else [])].dropna()
            if color_col and df_scatter[color_col].nunique() > 15:
                color_col = None
                df_scatter = df[cols_for_scatter].dropna()
            fig = px.scatter_matrix(df_scatter, dimensions=cols_for_scatter,
                                    color=color_col,
                                    title="🔵 Scatter Matrix (Multivariate)",
                                    color_discrete_sequence=COLOR_SEQ,
                                    template="plotly_white")
            fig.update_traces(diagonal_visible=False, marker=dict(size=3, opacity=0.6))
            fig.update_layout(**layout_base)
            plots['scatter_matrix'] = _safe_json(fig)
        except Exception:
            pass

    # ── 6. PIE CHART (Kategorik pertama) ─────────────────────────────────────
    if cat_cols:
        col = cat_cols[0]
        vc = df[col].value_counts().head(8)
        fig = px.pie(values=vc.values, names=vc.index.astype(str),
                     title=f"🥧 Proporsi: {col}",
                     color_discrete_sequence=COLOR_SEQ)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(**layout_base)
        plots['pie_cat'] = _safe_json(fig)

    return plots
