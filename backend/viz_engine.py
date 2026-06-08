"""
backend/viz_engine.py
Master Visualization Engine — 1 chart per view, dark pastel theme, dynamic columns.
"""

import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats as scipy_stats

# ─── High Visual Dark Palette ────────────────────────────────────────────────
PALETTE = ['#4ECDC4', '#7EA9FF', '#A8E6CF', '#C9B8FF', '#88D4E8', '#F4A9C8']
BG_CONTAINER = '#111A40'
PLOT_BG = '#172254'
GRID = 'rgba(255,255,255,0.06)'
AXIS_LINE = 'rgba(255,255,255,0.12)'
FONT_COLOR = '#C8D8F0'

CATEGORY_CHARTS = {
    'numerical': ['histogram', 'boxplot', 'density', 'qq', 'violin'],
    'categorical': ['bar', 'pie', 'count', 'pareto'],
    'bivariate': ['scatter', 'heatmap', 'regression', 'bubble', 'pair'],
    'catnum': ['box_by_cat', 'violin_by_cat', 'grouped_bar', 'strip'],
    'compare': ['violin_compare', 'grouped_bar_compare', 'parallel'],
}

CHART_LABELS = {
    'histogram': 'Histogram + KDE',
    'boxplot': 'Box Plot',
    'density': 'Density Plot (KDE)',
    'qq': 'QQ Plot — Normality',
    'violin': 'Violin Plot',
    'bar': 'Bar Chart',
    'pie': 'Donut / Pie Chart',
    'count': 'Count Plot',
    'pareto': 'Pareto Chart',
    'scatter': 'Scatter Plot',
    'heatmap': 'Correlation Heatmap',
    'regression': 'Regression + 95% CI',
    'bubble': 'Bubble Chart',
    'pair': 'Pair Plot Matrix',
    'box_by_cat': 'Boxplot by Category',
    'violin_by_cat': 'Violin by Category',
    'grouped_bar': 'Grouped Bar Chart',
    'strip': 'Strip Plot',
    'violin_compare': 'Violin Comparison',
    'grouped_bar_compare': 'Mean Comparison',
    'parallel': 'Parallel Coordinates',
}

PLACEHOLDERS = {
    'numerical': 'Gunakan dataset dengan minimal 1 kolom numerik untuk mengaktifkan halaman ini.',
    'categorical': 'Gunakan dataset dengan kolom kategorik untuk mengaktifkan halaman ini.',
    'bivariate': 'Gunakan dataset dengan minimal 2 kolom numerik untuk mengaktifkan halaman ini.',
    'catnum': 'Gunakan dataset dengan kolom numerik dan kategorik untuk mengaktifkan halaman ini.',
    'compare': 'Gunakan dataset dengan minimal 2 kolom numerik untuk perbandingan.',
}


def category_available(category, num_cols, cat_cols):
    """Validasi apakah kategori bisa ditampilkan."""
    n, c = len(num_cols), len(cat_cols)
    checks = {
        'numerical': n >= 1,
        'categorical': c >= 1,
        'bivariate': n >= 2,
        'catnum': n >= 1 and c >= 1,
        'compare': n >= 2,
    }
    return checks.get(category, False)


def _layout(**extra):
    base = dict(
        paper_bgcolor=BG_CONTAINER,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR, family='Inter, sans-serif', size=12),
        margin=dict(l=52, r=28, t=56, b=56),
        hoverlabel=dict(
            bgcolor='rgba(17,26,64,0.95)',
            bordercolor='rgba(126,169,255,0.4)',
            font=dict(color='#E8F0FF', size=12),
        ),
        legend=dict(
            bgcolor='rgba(17,26,64,0.6)',
            bordercolor='rgba(255,255,255,0.08)',
            font=dict(color=FONT_COLOR, size=11),
        ),
    )
    base.update(extra)
    return base


def _axes(fig):
    fig.update_xaxes(
        gridcolor=GRID, zerolinecolor=GRID,
        linecolor=AXIS_LINE, tickfont=dict(color=FONT_COLOR, size=10),
        title_font=dict(color=FONT_COLOR, size=11),
    )
    fig.update_yaxes(
        gridcolor=GRID, zerolinecolor=GRID,
        linecolor=AXIS_LINE, tickfont=dict(color=FONT_COLOR, size=10),
        title_font=dict(color=FONT_COLOR, size=11),
    )
    return fig


def _json(fig):
    return json.loads(fig.to_json())


def _kpis_numeric(series, col_name):
    s = series.dropna()
    if s.empty:
        return []
    return [
        {'label': 'Mean', 'value': f'{s.mean():,.2f}', 'icon': 'fa-calculator'},
        {'label': 'Median', 'value': f'{s.median():,.2f}', 'icon': 'fa-chart-line'},
        {'label': 'Std Dev', 'value': f'{s.std():,.2f}', 'icon': 'fa-ruler'},
        {'label': 'Min', 'value': f'{s.min():,.2f}', 'icon': 'fa-arrow-down'},
        {'label': 'Max', 'value': f'{s.max():,.2f}', 'icon': 'fa-arrow-up'},
    ]


def _kpis_categorical(series, col_name):
    s = series.dropna()
    if s.empty:
        return []
    vc = s.value_counts()
    mode = str(vc.index[0]) if not vc.empty else 'N/A'
    return [
        {'label': 'Unique', 'value': str(s.nunique()), 'icon': 'fa-tags'},
        {'label': 'Mode', 'value': mode[:18], 'icon': 'fa-star'},
        {'label': 'Top Freq', 'value': str(int(vc.iloc[0])) if not vc.empty else '0', 'icon': 'fa-hashtag'},
        {'label': 'Missing', 'value': str(int(series.isna().sum())), 'icon': 'fa-exclamation'},
        {'label': 'Rows', 'value': f'{len(series):,}', 'icon': 'fa-list'},
    ]


def _kpis_bivariate(df, col_x, col_y):
    clean = df[[col_x, col_y]].dropna()
    if len(clean) < 2:
        return _kpis_numeric(df[col_x], col_x)[:5]
    r = clean[col_x].corr(clean[col_y])
    return [
        {'label': 'Correlation', 'value': f'{r:.3f}', 'icon': 'fa-link'},
        {'label': 'Pairs', 'value': f'{len(clean):,}', 'icon': 'fa-circle-dot'},
        {'label': f'Mean {col_x[:12]}', 'value': f'{clean[col_x].mean():,.2f}', 'icon': 'fa-calculator'},
        {'label': f'Mean {col_y[:12]}', 'value': f'{clean[col_y].mean():,.2f}', 'icon': 'fa-chart-bar'},
        {'label': 'R²', 'value': f'{r**2:.3f}', 'icon': 'fa-square-root-alt'},
    ]


def build_kpis(category, df, col_x=None, col_y=None, num_cols=None):
    if category == 'numerical' and col_x:
        return _kpis_numeric(df[col_x], col_x)
    if category == 'categorical' and col_x:
        return _kpis_categorical(df[col_x], col_x)
    if category in ('bivariate', 'catnum') and col_x and col_y:
        if category == 'catnum':
            return [
                {'label': 'Groups', 'value': str(df[col_x].nunique()), 'icon': 'fa-layer-group'},
                {'label': f'Mean {col_y[:12]}', 'value': f'{df[col_y].mean():,.2f}', 'icon': 'fa-calculator'},
                {'label': 'Std', 'value': f'{df[col_y].std():,.2f}', 'icon': 'fa-ruler'},
                {'label': 'Rows', 'value': f'{len(df):,}', 'icon': 'fa-list'},
                {'label': 'Missing', 'value': str(int(df[[col_x, col_y]].isna().any(axis=1).sum())), 'icon': 'fa-exclamation'},
            ]
        return _kpis_bivariate(df, col_x, col_y)
    if category == 'compare' and num_cols:
        return [
            {'label': 'Variables', 'value': str(len(num_cols)), 'icon': 'fa-hashtag'},
            {'label': 'Rows', 'value': f'{len(df):,}', 'icon': 'fa-list'},
            {'label': 'Cols', 'value': str(len(df.columns)), 'icon': 'fa-columns'},
            {'label': 'Numeric', 'value': str(len(num_cols)), 'icon': 'fa-chart-bar'},
            {'label': 'Complete', 'value': f'{df[num_cols].dropna().shape[0]:,}', 'icon': 'fa-check'},
        ]
    return []


# ─── Chart builders ──────────────────────────────────────────────────────────

def _chart_histogram(df, col):
    clean = df[col].dropna()
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=clean, nbinsx=30, marker_color=PALETTE[0], opacity=0.85, name=col))
    if len(clean) >= 3:
        kde_x = np.linspace(clean.min(), clean.max(), 200)
        kde = scipy_stats.gaussian_kde(clean)
        scale = len(clean) * (clean.max() - clean.min()) / 30
        fig.add_trace(go.Scatter(x=kde_x, y=kde(kde_x) * scale, mode='lines',
                                 line=dict(color=PALETTE[1], width=2), name='KDE'))
    fig.update_layout(_layout(title=CHART_LABELS['histogram']))
    return _json(_axes(fig))


def _chart_boxplot(df, col):
    fig = go.Figure(go.Box(y=df[col].dropna(), name=col, marker_color=PALETTE[0],
                           boxmean='sd', line_color=PALETTE[1]))
    fig.update_layout(_layout(title=CHART_LABELS['boxplot']))
    return _json(_axes(fig))


def _chart_density(df, col):
    clean = df[col].dropna()
    kde_x = np.linspace(clean.min(), clean.max(), 300)
    kde = scipy_stats.gaussian_kde(clean)
    fig = go.Figure(go.Scatter(
        x=kde_x, y=kde(kde_x), fill='tozeroy', mode='lines',
        line=dict(color=PALETTE[0], width=2),
        fillcolor='rgba(78,205,196,0.18)', name=col,
    ))
    fig.update_layout(_layout(title=CHART_LABELS['density']))
    return _json(_axes(fig))


def _chart_qq(df, col):
    clean = df[col].dropna().values
    (osm, osr), (slope, intercept, _) = scipy_stats.probplot(clean, dist='norm')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=osm, y=osr, mode='markers', marker=dict(color=PALETTE[1], size=5, opacity=0.7)))
    x_line = np.array([osm.min(), osm.max()])
    fig.add_trace(go.Scatter(x=x_line, y=slope * x_line + intercept, mode='lines',
                             line=dict(color=PALETTE[2], dash='dash', width=2)))
    fig.update_layout(_layout(title=CHART_LABELS['qq']))
    return _json(_axes(fig))


def _chart_violin_uni(df, col):
    fig = go.Figure(go.Violin(y=df[col].dropna(), name=col, fillcolor=PALETTE[0],
                              line_color=PALETTE[1], box_visible=True, meanline_visible=True, opacity=0.8))
    fig.update_layout(_layout(title=CHART_LABELS['violin']))
    return _json(_axes(fig))


def _chart_bar_cat(df, col):
    vc = df[col].value_counts().head(12)
    fig = go.Figure(go.Bar(x=vc.index.astype(str), y=vc.values, marker_color=PALETTE[0]))
    fig.update_layout(_layout(title=CHART_LABELS['bar']))
    return _json(_axes(fig))


def _chart_pie_cat(df, col):
    vc = df[col].value_counts().head(10)
    fig = go.Figure(go.Pie(labels=vc.index.astype(str), values=vc.values, hole=0.45,
                           marker_colors=PALETTE, textfont=dict(color=FONT_COLOR)))
    fig.update_layout(_layout(title=CHART_LABELS['pie']))
    return _json(fig)


def _chart_count_cat(df, col):
    vc = df[col].value_counts().head(15).sort_values()
    fig = go.Figure(go.Bar(x=vc.values, y=vc.index.astype(str), orientation='h', marker_color=PALETTE[2]))
    fig.update_layout(_layout(title=CHART_LABELS['count']))
    return _json(_axes(fig))


def _chart_pareto_cat(df, col):
    vc = df[col].value_counts().head(12)
    cum = vc.cumsum() / vc.sum() * 100
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Bar(x=vc.index.astype(str), y=vc.values, marker_color=PALETTE[0]), secondary_y=False)
    fig.add_trace(go.Scatter(x=vc.index.astype(str), y=cum, mode='lines+markers',
                             line=dict(color=PALETTE[3], width=2)), secondary_y=True)
    fig.update_layout(_layout(title=CHART_LABELS['pareto']))
    return _json(_axes(fig))


def _chart_scatter(df, col_x, col_y):
    fig = px.scatter(df, x=col_x, y=col_y, opacity=0.65, color_discrete_sequence=[PALETTE[0]])
    fig.update_layout(_layout(title=CHART_LABELS['scatter']))
    return _json(_axes(fig))


def _chart_heatmap(df, num_cols):
    corr = df[num_cols[:12]].corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale=[[0, PLOT_BG], [0.5, PALETTE[1]], [1, PALETTE[0]]],
        zmid=0,
    ))
    fig.update_layout(_layout(title=CHART_LABELS['heatmap']))
    return _json(fig)


def _chart_regression(df, col_x, col_y):
    clean = df[[col_x, col_y]].dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=clean[col_x], y=clean[col_y], mode='markers',
                             marker=dict(color=PALETTE[0], size=6, opacity=0.6)))
    slope, intercept, r, _, _ = scipy_stats.linregress(clean[col_x], clean[col_y])
    x_range = np.linspace(clean[col_x].min(), clean[col_x].max(), 100)
    fig.add_trace(go.Scatter(x=x_range, y=slope * x_range + intercept, mode='lines',
                             line=dict(color=PALETTE[3], width=2.5), name=f'R²={r**2:.3f}'))
    fig.update_layout(_layout(title=CHART_LABELS['regression']))
    return _json(_axes(fig))


def _chart_bubble(df, col_x, col_y, col_z):
    fig = px.scatter(df, x=col_x, y=col_y, size=col_z, opacity=0.65, color_discrete_sequence=[PALETTE[4]])
    fig.update_layout(_layout(title=CHART_LABELS['bubble']))
    return _json(_axes(fig))


def _chart_pair(df, num_cols):
    cols = num_cols[:4]
    fig = px.scatter_matrix(df[cols].dropna().head(400), dimensions=cols,
                            color_discrete_sequence=PALETTE)
    fig.update_layout(_layout(title=CHART_LABELS['pair'], height=520))
    fig.update_traces(diagonal_visible=False, marker=dict(size=4, opacity=0.5))
    return _json(fig)


def _chart_box_catnum(df, cat_col, num_col):
    top = df[cat_col].value_counts().head(8).index
    sub = df[df[cat_col].isin(top)]
    fig = px.box(sub, x=cat_col, y=num_col, color_discrete_sequence=PALETTE)
    fig.update_layout(_layout(title=CHART_LABELS['box_by_cat']))
    return _json(_axes(fig))


def _chart_violin_catnum(df, cat_col, num_col):
    top = df[cat_col].value_counts().head(8).index
    sub = df[df[cat_col].isin(top)]
    fig = px.violin(sub, x=cat_col, y=num_col, color_discrete_sequence=PALETTE, box=True)
    fig.update_layout(_layout(title=CHART_LABELS['violin_by_cat']))
    return _json(_axes(fig))


def _chart_grouped_bar(df, cat_col, num_col):
    grp = df.groupby(cat_col)[num_col].mean().head(12)
    fig = go.Figure(go.Bar(x=grp.index.astype(str), y=grp.values, marker_color=PALETTE[1]))
    fig.update_layout(_layout(title=CHART_LABELS['grouped_bar']))
    return _json(_axes(fig))


def _chart_strip(df, cat_col, num_col):
    top = df[cat_col].value_counts().head(10).index
    sub = df[df[cat_col].isin(top)]
    fig = px.strip(sub, x=cat_col, y=num_col, color_discrete_sequence=[PALETTE[0]])
    fig.update_layout(_layout(title=CHART_LABELS['strip']))
    return _json(_axes(fig))


def _chart_violin_compare(df, num_cols):
    fig = go.Figure()
    for i, col in enumerate(num_cols[:8]):
        fig.add_trace(go.Violin(y=df[col].dropna(), name=col, line_color=PALETTE[i % len(PALETTE)],
                                fillcolor=PALETTE[i % len(PALETTE)], opacity=0.75))
    fig.update_layout(_layout(title=CHART_LABELS['violin_compare']))
    return _json(_axes(fig))


def _chart_grouped_compare(df, num_cols):
    means = [df[c].mean() for c in num_cols[:10]]
    stds = [df[c].std() for c in num_cols[:10]]
    fig = go.Figure(go.Bar(
        x=num_cols[:10], y=means, error_y=dict(type='data', array=stds, visible=True),
        marker_color=PALETTE[0],
    ))
    fig.update_layout(_layout(title=CHART_LABELS['grouped_bar_compare']))
    return _json(_axes(fig))


def _chart_parallel(df, num_cols, cat_cols):
    cols = num_cols[:6]
    sub = df[cols].dropna().sample(min(400, len(df)), random_state=42)
    fig = go.Figure(go.Parcoords(
        line=dict(color=np.arange(len(sub)), colorscale=[[0, PALETTE[0]], [1, PALETTE[3]]], showscale=False),
        dimensions=[dict(label=c, values=sub[c]) for c in cols],
    ))
    fig.update_layout(_layout(title=CHART_LABELS['parallel']))
    return _json(fig)


def generate_master_chart(df, num_cols, cat_cols, category, chart_type,
                          col_x=None, col_y=None, col_z=None):
    """
    Generate single chart + metadata for master visualization view.

    Returns dict: ok, chart, kpis, chart_label, placeholder
    """
    if not category_available(category, num_cols, cat_cols):
        return {
            'ok': False,
            'placeholder': PLACEHOLDERS.get(category, 'Dataset tidak kompatibel.'),
            'kpis': [],
        }

    types = CATEGORY_CHARTS.get(category, [])
    if chart_type not in types:
        chart_type = types[0] if types else None

    if not chart_type:
        return {'ok': False, 'placeholder': 'Tidak ada tipe grafik.', 'kpis': []}

    # Default columns
    if category in ('numerical', 'categorical') and not col_x:
        col_x = (num_cols[0] if category == 'numerical' else cat_cols[0])
    if category == 'bivariate':
        col_x = col_x or (num_cols[0] if num_cols else None)
        col_y = col_y or (num_cols[1] if len(num_cols) > 1 else num_cols[0])
        col_z = col_z or (num_cols[2] if len(num_cols) > 2 else num_cols[0])
    if category == 'catnum':
        col_x = col_x or cat_cols[0]
        col_y = col_y or num_cols[0]

    try:
        builders = {
            'histogram': lambda: _chart_histogram(df, col_x),
            'boxplot': lambda: _chart_boxplot(df, col_x),
            'density': lambda: _chart_density(df, col_x),
            'qq': lambda: _chart_qq(df, col_x),
            'violin': lambda: _chart_violin_uni(df, col_x),
            'bar': lambda: _chart_bar_cat(df, col_x),
            'pie': lambda: _chart_pie_cat(df, col_x),
            'count': lambda: _chart_count_cat(df, col_x),
            'pareto': lambda: _chart_pareto_cat(df, col_x),
            'scatter': lambda: _chart_scatter(df, col_x, col_y),
            'heatmap': lambda: _chart_heatmap(df, num_cols),
            'regression': lambda: _chart_regression(df, col_x, col_y),
            'bubble': lambda: _chart_bubble(df, col_x, col_y, col_z),
            'pair': lambda: _chart_pair(df, num_cols),
            'box_by_cat': lambda: _chart_box_catnum(df, col_x, col_y),
            'violin_by_cat': lambda: _chart_violin_catnum(df, col_x, col_y),
            'grouped_bar': lambda: _chart_grouped_bar(df, col_x, col_y),
            'strip': lambda: _chart_strip(df, col_x, col_y),
            'violin_compare': lambda: _chart_violin_compare(df, num_cols),
            'grouped_bar_compare': lambda: _chart_grouped_compare(df, num_cols),
            'parallel': lambda: _chart_parallel(df, num_cols, cat_cols),
        }
        chart = builders[chart_type]()
        kpis = build_kpis(category, df, col_x, col_y, num_cols)
        idx = types.index(chart_type)

        return {
            'ok': True,
            'chart': chart,
            'kpis': kpis,
            'chart_type': chart_type,
            'chart_label': CHART_LABELS.get(chart_type, chart_type),
            'chart_index': idx,
            'chart_total': len(types),
            'col_x': col_x,
            'col_y': col_y,
            'col_z': col_z,
        }
    except Exception as e:
        return {
            'ok': False,
            'placeholder': f'Gagal membuat grafik: {str(e)}',
            'kpis': build_kpis(category, df, col_x, col_y, num_cols),
        }
