"""
backend/dashboard_overview.py
Dashboard utama — KPI cards + grid visualisasi dengan validasi kondisional.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from backend.visualizations import COLORS, _layout, _safe_json, _apply_axes, _top_cats


def _fmt_num(val, decimals=2):
    try:
        f = float(val)
        if abs(f) >= 1000:
            return f"{f:,.{decimals}f}"
        return round(f, decimals)
    except (TypeError, ValueError):
        return "N/A"


def build_overview_kpis(df, num_cols, cat_cols, metrics):
    """Maksimal 5 KPI cards — prioritas metrik yang tersedia di dataset."""
    kpis = [
        {'id': 'rows', 'label': 'Total Rows', 'value': metrics['total_rows'],
         'icon': 'fa-list-ol', 'color': 'blue'},
        {'id': 'cols', 'label': 'Total Columns', 'value': metrics['total_columns'],
         'icon': 'fa-columns', 'color': 'green'},
    ]

    missing_pct = metrics.get('missing_pct', '0%')
    kpis.append({
        'id': 'missing', 'label': 'Missing Ratio', 'value': missing_pct,
        'icon': 'fa-exclamation-circle', 'color': 'red',
    })

    if num_cols:
        col = num_cols[0]
        mean_val = df[col].mean()
        kpis.append({
            'id': 'mean', 'label': f'Avg — {col}', 'value': _fmt_num(mean_val),
            'icon': 'fa-chart-line', 'color': 'orange',
        })
        if len(num_cols) > 1:
            col2 = num_cols[1]
            std_val = df[col2].std()
            kpis.append({
                'id': 'std', 'label': f'Std — {col2}', 'value': _fmt_num(std_val),
                'icon': 'fa-ruler-horizontal', 'color': 'purple',
            })
    elif cat_cols:
        col = cat_cols[0]
        kpis.append({
            'id': 'unique', 'label': f'Unique — {col}', 'value': df[col].nunique(),
            'icon': 'fa-tags', 'color': 'orange',
        })

    if len(kpis) < 5 and cat_cols and num_cols:
        kpis.append({
            'id': 'cat_count', 'label': 'Categorical Cols', 'value': len(cat_cols),
            'icon': 'fa-font', 'color': 'purple',
        })

    return kpis[:5]


def _hbar_cat(df, cat_col, top_n=10):
    """Horizontal bar — perbandingan kategori."""
    vc = df[cat_col].value_counts().head(top_n).sort_values()
    fig = go.Figure(go.Bar(
        x=vc.values, y=vc.index.astype(str), orientation='h',
        marker_color=COLORS[0],
        hovertemplate='%{y}<br>Count: %{x}<extra></extra>',
    ))
    fig.update_layout(_layout(
        title=f'Category Comparison — {cat_col}',
        margin=dict(l=100, r=20, t=48, b=40),
    ))
    _apply_axes(fig)
    return _safe_json(fig)


def _treemap_cat(df, cat_col, top_n=10):
    """Treemap — komposisi kategori."""
    vc = df[cat_col].value_counts().head(top_n).reset_index()
    vc.columns = ['category', 'count']
    fig = px.treemap(
        vc, path=['category'], values='count',
        color='count', color_continuous_scale='Blues',
    )
    fig.update_layout(_layout(title=f'Composition — {cat_col}'))
    fig.update_traces(hovertemplate='%{label}<br>Count: %{value}<extra></extra>')
    return _safe_json(fig)


def _pie_cat(df, cat_col, top_n=8):
    """Fallback pie jika treemap tidak cocok."""
    vc = df[cat_col].value_counts().head(top_n)
    fig = go.Figure(go.Pie(
        labels=vc.index.astype(str), values=vc.values,
        hole=0.4, marker_colors=COLORS,
        hovertemplate='%{label}<br>%{percent}<extra></extra>',
    ))
    fig.update_layout(_layout(title=f'Composition — {cat_col}'))
    return _safe_json(fig)


def _area_ranking(df, num_col, top_n=20):
    """Area/line — ranking nilai numerik terbesar → terkecil."""
    s = df[num_col].dropna().nlargest(min(top_n, len(df))).sort_values(ascending=False)
    if s.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(s) + 1)), y=s.values,
        mode='lines', fill='tozeroy',
        line=dict(color=COLORS[1], width=2),
        fillcolor='rgba(5,205,153,0.15)',
        name=num_col,
        hovertemplate='Rank %{x}<br>Value: %{y:,.2f}<extra></extra>',
    ))
    fig.update_layout(_layout(
        title=f'Value Ranking — {num_col}',
        xaxis_title='Rank', yaxis_title=num_col,
    ))
    _apply_axes(fig)
    return _safe_json(fig)


def _line_timeseries(df, dt_col, num_col, max_pts=100):
    """Line chart — tren temporal."""
    temp = df[[dt_col, num_col]].copy()
    temp[dt_col] = pd.to_datetime(temp[dt_col], errors='coerce')
    temp = temp.dropna().sort_values(dt_col)
    if len(temp) < 2:
        return None
    if len(temp) > max_pts:
        temp = temp.iloc[:: max(1, len(temp) // max_pts)]
    fig = go.Figure(go.Scatter(
        x=temp[dt_col], y=temp[num_col],
        mode='lines', line=dict(color=COLORS[0], width=2),
        hovertemplate='%{x|%Y-%m-%d}<br>%{y:,.2f}<extra></extra>',
    ))
    fig.update_layout(_layout(
        title=f'Trend — {num_col}',
        xaxis=dict(type='date'),
    ))
    _apply_axes(fig)
    return _safe_json(fig)


def _vbar_numeric(df, num_col, bins=20):
    """Vertical bar — distribusi numerik (histogram sebagai bar)."""
    clean = df[num_col].dropna()
    if len(clean) < 2:
        return None
    counts, edges = np.histogram(clean, bins=min(bins, max(5, clean.nunique())))
    labels = [f'{edges[i]:.1f}' for i in range(len(counts))]
    fig = go.Figure(go.Bar(
        x=labels, y=counts,
        marker_color=COLORS[2],
        hovertemplate='Range %{x}<br>Count: %{y}<extra></extra>',
    ))
    fig.update_layout(_layout(title=f'Distribution — {num_col}'))
    _apply_axes(fig)
    return _safe_json(fig)


def _vbar_cat(df, cat_col, top_n=10):
    """Vertical bar — frekuensi kategori."""
    vc = df[cat_col].value_counts().head(top_n)
    fig = go.Figure(go.Bar(
        x=vc.index.astype(str), y=vc.values,
        marker_color=COLORS[3],
        hovertemplate='%{x}<br>Count: %{y}<extra></extra>',
    ))
    fig.update_layout(_layout(title=f'Category Count — {cat_col}'))
    _apply_axes(fig)
    return _safe_json(fig)


def _area_cumulative(df, num_col):
    """Area chart — kumulatif / urutan nilai."""
    s = df[num_col].dropna().sort_values(ascending=False).reset_index(drop=True)
    if len(s) < 2:
        return None
    cum = s.cumsum() / s.sum() * 100 if s.sum() != 0 else s.cumsum()
    fig = go.Figure(go.Scatter(
        x=list(range(1, len(cum) + 1)), y=cum,
        mode='lines', fill='tozeroy',
        line=dict(color=COLORS[4], width=2),
        fillcolor='rgba(134,140,255,0.15)',
        hovertemplate='Index %{x}<br>Cumulative %: %{y:.1f}<extra></extra>',
    ))
    fig.update_layout(_layout(
        title=f'Cumulative Share — {num_col}',
        xaxis_title='Sorted Index', yaxis_title='Cumulative %',
    ))
    _apply_axes(fig)
    return _safe_json(fig)


def generate_overview_dashboard(df, num_cols, cat_cols, dt_cols=None, metrics=None):
    """
    Bangun payload lengkap untuk tab Dashboard Overview.

    Returns
    -------
    dict dengan keys: kpis, slots, toggle_data, viz_links
    """
    dt_cols = dt_cols or []
    metrics = metrics or {}

    result = {
        'kpis': build_overview_kpis(df, num_cols, cat_cols, metrics),
        'slots': {},
        'toggle_data': {},
        'viz_links': {},
    }

    def _slot(key, chart_json, visible, title, viz_tab, viz_sub=None):
        result['slots'][key] = {
            'visible': visible and chart_json is not None,
            'title': title,
            'chart': chart_json,
        }
        result['viz_links'][key] = {'tab': 'visualizations', 'sub': viz_sub or 'numerical'}

    # ── Baris tengah ──────────────────────────────────────────────────────────
    if cat_cols:
        c0 = cat_cols[0]
        try:
            hbar = _hbar_cat(df, c0)
            _slot('ov_hbar', hbar, True, 'Category Comparison', 'categorical', 'categorical')
        except Exception:
            _slot('ov_hbar', None, False, 'Category Comparison', 'categorical')

        try:
            center = _treemap_cat(df, c0)
            _slot('ov_center', center, True, 'Category Composition', 'categorical', 'categorical')
        except Exception:
            try:
                center = _pie_cat(df, c0)
                _slot('ov_center', center, True, 'Category Composition', 'categorical', 'categorical')
            except Exception:
                _slot('ov_center', None, False, 'Category Composition', 'categorical')
    else:
        _slot('ov_hbar', None, False, 'Category Comparison', 'categorical')
        _slot('ov_center', None, False, 'Category Composition', 'categorical')

    # Kanan atas: time series jika ada datetime + numeric, else ranking
    top_right = None
    top_right_visible = False
    top_right_viz = 'numerical'
    if dt_cols and num_cols:
        try:
            top_right = _line_timeseries(df, dt_cols[0], num_cols[0])
            top_right_visible = top_right is not None
            top_right_viz = 'numerical'
        except Exception:
            pass
    if not top_right_visible and num_cols:
        try:
            top_right = _area_ranking(df, num_cols[0])
            top_right_visible = top_right is not None
        except Exception:
            pass
    _slot('ov_top_right', top_right, top_right_visible,
          'Trend / Ranking', 'numerical' if not dt_cols else 'timeseries',
          'numerical' if not dt_cols else None)

    # ── Baris bawah ───────────────────────────────────────────────────────────
    vbar_left_opts = {}
    if num_cols:
        for col in num_cols[:4]:
            try:
                vbar_left_opts[col] = _vbar_numeric(df, col)
            except Exception:
                pass
        default_left = num_cols[0]
        result['toggle_data']['ov_vbar_left'] = {
            'options': list(vbar_left_opts.keys()),
            'default': default_left,
            'charts': vbar_left_opts,
        }
        _slot('ov_vbar_left', vbar_left_opts.get(default_left), bool(vbar_left_opts),
              'Numeric Distribution', 'numerical', 'numerical')
    else:
        _slot('ov_vbar_left', None, False, 'Numeric Distribution', 'numerical')

    area_bottom = None
    if len(num_cols) >= 2:
        try:
            area_bottom = _area_cumulative(df, num_cols[1])
        except Exception:
            pass
    elif num_cols:
        try:
            area_bottom = _area_ranking(df, num_cols[0])
        except Exception:
            pass
    _slot('ov_area_bottom', area_bottom, area_bottom is not None,
          'Cumulative / Trend', 'numerical', 'numerical')

    vbar_right_opts = {}
    if cat_cols:
        for col in cat_cols[:4]:
            try:
                vbar_right_opts[col] = _vbar_cat(df, col)
            except Exception:
                pass
        default_right = cat_cols[0] if len(cat_cols) == 1 else (cat_cols[1] if len(cat_cols) > 1 else cat_cols[0])
        if default_right not in vbar_right_opts and vbar_right_opts:
            default_right = list(vbar_right_opts.keys())[0]
        result['toggle_data']['ov_vbar_right'] = {
            'options': list(vbar_right_opts.keys()),
            'default': default_right,
            'charts': vbar_right_opts,
        }
        _slot('ov_vbar_right', vbar_right_opts.get(default_right), bool(vbar_right_opts),
              'Category Frequency', 'categorical', 'categorical')
    else:
        _slot('ov_vbar_right', None, False, 'Category Frequency', 'categorical')

    return result
