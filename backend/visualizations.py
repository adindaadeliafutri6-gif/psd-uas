"""
backend/visualizations.py
Week 15 — Auto-Visualization Engine (Complete)

Charts yang dihasilkan:
  a) Numerical   : histogram, density, boxplot, qq, violin
  b) Categorical : bar, pie, count, pareto
  c) Bivariate   : scatter, heatmap, scatter_matrix (pair plot), regression, bubble
  d) Cat vs Num  : box_cat_num, violin_cat_num, grouped_bar, strip
  e) Komparasi   : violin_compare, grouped_bar_compare, parallel_coords
"""

import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats as scipy_stats

# ─── Palette ────────────────────────────────────────────────────────────────
COLORS   = ['#4318ff', '#05cd99', '#ffce20', '#ee5d50', '#868cff',
            '#17a2b8', '#fd7e14', '#6f42c1', '#20c997', '#dc3545']
LAYOUT   = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor ='rgba(0,0,0,0)',
    font         =dict(family='Inter, sans-serif', size=12),
    margin       =dict(l=40, r=20, t=48, b=40),
    hoverlabel   =dict(bgcolor='rgba(10,18,48,0.93)',
                       bordercolor='rgba(100,160,235,0.45)',
                       font=dict(color='#e8f4fc', size=13)),
)
AXIS_STYLE = dict(
    showgrid    =True,
    gridcolor   ='rgba(180,190,220,0.15)',
    zeroline    =False,
    linecolor   ='rgba(180,190,220,0.3)',
    tickfont    =dict(size=11),
)

def _layout(**extra):
    d = dict(**LAYOUT)
    d.update(extra)
    return d

def _safe_json(fig):
    return json.loads(fig.to_json())

def _hex_to_rgba(hex_color, alpha=0.12):
    """Convert #RRGGBB hex to rgba() string for Plotly fillcolor."""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'

def _apply_axes(fig):
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

def _top_cats(df, col, n=8):
    """Kembalikan df yang hanya berisi n kategori teratas."""
    top = df[col].value_counts().head(n).index
    return df[df[col].isin(top)]


# ════════════════════════════════════════════════════════════════════════════
# a) NUMERICAL VISUALIZATIONS
# ════════════════════════════════════════════════════════════════════════════

def _hist_num(df, num_cols):
    """Histogram + KDE overlay untuk kolom numerik pertama."""
    col = num_cols[0]
    clean = df[col].dropna()

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=clean, nbinsx=30,
        name='Count',
        marker_color=COLORS[0],
        opacity=0.75,
        hovertemplate='%{x}<br>Count: %{y}<extra></extra>',
    ))

    # KDE overlay
    kde_x = np.linspace(clean.min(), clean.max(), 300)
    kde   = scipy_stats.gaussian_kde(clean)
    scale = len(clean) * (clean.max() - clean.min()) / 30
    fig.add_trace(go.Scatter(
        x=kde_x, y=kde(kde_x) * scale,
        mode='lines', name='KDE',
        line=dict(color=COLORS[4], width=2.5),
        hovertemplate='%{x:.2f}<br>Density: %{y:.4f}<extra></extra>',
    ))

    fig.update_layout(_layout(title=f'📊 Histogram + KDE: {col}'), showlegend=True)
    _apply_axes(fig)
    return _safe_json(fig)


def _density_num(df, num_cols):
    """Density (KDE) plot untuk semua kolom numerik (max 6)."""
    fig = go.Figure()
    for i, col in enumerate(num_cols[:6]):
        clean = df[col].dropna()
        if len(clean) < 3:
            continue
        kde_x = np.linspace(clean.min(), clean.max(), 300)
        kde   = scipy_stats.gaussian_kde(clean)
        fig.add_trace(go.Scatter(
            x=kde_x, y=kde(kde_x),
            mode='lines', name=col,
            line=dict(color=COLORS[i % len(COLORS)], width=2),
            fill='tozeroy',
            fillcolor=_hex_to_rgba(COLORS[i % len(COLORS)], 0.12),
            hovertemplate=f'{col}: %{{x:.2f}}<br>Density: %{{y:.4f}}<extra></extra>',
        ))
    fig.update_layout(_layout(title='🌊 Density Plot (KDE) — All Numeric Columns'))
    _apply_axes(fig)
    return _safe_json(fig)


def _boxplot_num(df, num_cols):
    """Boxplot multi-variabel untuk semua kolom numerik."""
    fig = go.Figure()
    for i, col in enumerate(num_cols):
        clean = df[col].dropna()
        fig.add_trace(go.Box(
            y=clean, name=col,
            marker_color=COLORS[i % len(COLORS)],
            boxmean='sd',
            hovertemplate=f'{col}<br>Value: %{{y:.2f}}<extra></extra>',
        ))
    fig.update_layout(_layout(title='📦 Boxplot — All Numeric Variables'))
    _apply_axes(fig)
    return _safe_json(fig)


def _qq_num(df, num_cols):
    """QQ Plot untuk kolom numerik pertama."""
    col   = num_cols[0]
    clean = df[col].dropna().values
    (osm, osr), (slope, intercept, _) = scipy_stats.probplot(clean, dist='norm')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=osm, y=osr,
        mode='markers',
        name='Data Points',
        marker=dict(color=COLORS[0], size=5, opacity=0.7),
        hovertemplate='Theoretical: %{x:.3f}<br>Sample: %{y:.3f}<extra></extra>',
    ))
    # Reference line
    x_line = np.array([osm.min(), osm.max()])
    fig.add_trace(go.Scatter(
        x=x_line, y=slope * x_line + intercept,
        mode='lines', name='Normal Reference',
        line=dict(color=COLORS[3], width=2, dash='dash'),
    ))
    fig.update_layout(_layout(
        title=f'📐 QQ Plot — {col}',
        xaxis_title='Theoretical Quantiles',
        yaxis_title='Sample Quantiles',
    ))
    _apply_axes(fig)
    return _safe_json(fig)


def _violin_num(df, num_cols):
    """Violin plot untuk semua kolom numerik."""
    fig = go.Figure()
    for i, col in enumerate(num_cols):
        clean = df[col].dropna()
        fig.add_trace(go.Violin(
            y=clean, name=col,
            box_visible=True,
            meanline_visible=True,
            fillcolor=COLORS[i % len(COLORS)],
            line_color=COLORS[i % len(COLORS)],
            opacity=0.7,
            hovertemplate=f'{col}: %{{y:.2f}}<extra></extra>',
        ))
    fig.update_layout(_layout(title='🎻 Violin Plot — All Numeric Variables'))
    _apply_axes(fig)
    return _safe_json(fig)


# ════════════════════════════════════════════════════════════════════════════
# b) CATEGORICAL VISUALIZATIONS
# ════════════════════════════════════════════════════════════════════════════

def _bar_cat(df, cat_cols):
    """Bar chart top-10 kategori untuk kolom kategorik pertama."""
    col = cat_cols[0]
    vc  = df[col].value_counts().head(10).reset_index()
    vc.columns = [col, 'Count']

    fig = px.bar(
        vc, x=col, y='Count',
        color='Count', color_continuous_scale='Blues',
        text='Count',
        title=f'📋 Bar Chart: Top 10 — {col}',
    )
    fig.update_traces(textposition='outside',
                      hovertemplate='%{x}<br>Count: %{y:,}<extra></extra>')
    fig.update_layout(_layout(coloraxis_showscale=False))
    _apply_axes(fig)
    return _safe_json(fig)


def _pie_cat(df, cat_cols):
    """Donut / Pie chart untuk kolom kategorik pertama."""
    col = cat_cols[0]
    vc  = df[col].value_counts().head(8)

    fig = go.Figure(go.Pie(
        labels=vc.index.astype(str),
        values=vc.values,
        hole=0.38,
        marker_colors=COLORS[:len(vc)],
        textinfo='percent+label',
        hovertemplate='%{label}<br>Count: %{value:,}<br>Pct: %{percent}<extra></extra>',
    ))
    fig.update_layout(_layout(title=f'🍩 Donut Chart: {col}', showlegend=True))
    return _safe_json(fig)


def _count_cat(df, cat_cols):
    """Count plot (horizontal bar) untuk semua kolom kategorik (max 3)."""
    cols = cat_cols[:3]
    fig  = make_subplots(rows=1, cols=len(cols),
                         subplot_titles=[f'Count: {c}' for c in cols])

    for i, col in enumerate(cols, start=1):
        vc = df[col].value_counts().head(8)
        fig.add_trace(go.Bar(
            y=vc.index.astype(str), x=vc.values,
            orientation='h',
            name=col,
            marker_color=COLORS[i % len(COLORS)],
            hovertemplate='%{y}<br>Count: %{x:,}<extra></extra>',
        ), row=1, col=i)

    fig.update_layout(_layout(title='📊 Count Plot — Categorical Columns', showlegend=False))
    _apply_axes(fig)
    return _safe_json(fig)


def _pareto_cat(df, cat_cols):
    """Pareto chart (bar + cumulative %) untuk kolom kategorik pertama."""
    col = cat_cols[0]
    vc  = df[col].value_counts().head(10)
    cum = (vc.cumsum() / vc.sum() * 100).values

    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Bar(
        x=vc.index.astype(str), y=vc.values,
        name='Count', marker_color=COLORS[0], opacity=0.8,
        hovertemplate='%{x}<br>Count: %{y:,}<extra></extra>',
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=vc.index.astype(str), y=cum,
        name='Cumulative %', mode='lines+markers',
        line=dict(color=COLORS[3], width=2.5),
        marker=dict(size=7),
        hovertemplate='%{x}<br>Cumulative: %{y:.1f}%<extra></extra>',
    ), secondary_y=True)

    # 80% reference line
    fig.add_hline(y=80, line_dash='dash', line_color=COLORS[2],
                  annotation_text='80%', secondary_y=True)

    fig.update_yaxes(title_text='Count',       secondary_y=False)
    fig.update_yaxes(title_text='Cumulative %', secondary_y=True, range=[0, 105])
    fig.update_layout(_layout(title=f'📈 Pareto Chart: {col} (80/20 Rule)'))
    _apply_axes(fig)
    return _safe_json(fig)


# ════════════════════════════════════════════════════════════════════════════
# c) BIVARIATE & MULTIVARIATE
# ════════════════════════════════════════════════════════════════════════════

def _scatter_biv(df, num_cols, cat_cols):
    """Scatter plot dua variabel numerik pertama, warna dari cat col."""
    if len(num_cols) < 2:
        return None
    x_col, y_col = num_cols[0], num_cols[1]
    color_col = cat_cols[0] if cat_cols and df[cat_cols[0]].nunique() <= 15 else None

    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col,
        color_discrete_sequence=COLORS,
        opacity=0.65,
        title=f'🔵 Scatter Plot: {x_col} vs {y_col}',
        trendline='ols' if color_col is None else None,
        hover_data={x_col: ':.2f', y_col: ':.2f'},
    )
    fig.update_layout(_layout())
    _apply_axes(fig)
    return _safe_json(fig)


def _heatmap(df, num_cols):
    """Correlation heatmap."""
    if len(num_cols) < 2:
        return None
    corr = df[num_cols].corr().round(3)

    fig = px.imshow(
        corr, text_auto=True, aspect='auto',
        color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
        title='🔥 Correlation Heatmap',
    )
    fig.update_traces(hovertemplate='%{x} × %{y}<br>r = %{z:.3f}<extra></extra>')
    fig.update_layout(_layout())
    return _safe_json(fig)


def _scatter_matrix(df, num_cols, cat_cols):
    """Pair plot / scatter matrix (max 5 kolom numerik)."""
    cols = num_cols[:5]
    color_col = None
    if cat_cols and df[cat_cols[0]].nunique() <= 10:
        color_col = cat_cols[0]

    df_s = df[cols + ([color_col] if color_col else [])].dropna()
    if df_s.empty:
        return None

    fig = px.scatter_matrix(
        df_s, dimensions=cols, color=color_col,
        color_discrete_sequence=COLORS,
        title='🔗 Pair Plot / Scatter Matrix',
    )
    fig.update_traces(
        diagonal_visible=False,
        marker=dict(size=3, opacity=0.55),
        hovertemplate='%{xaxis.title.text}: %{x:.2f}<br>%{yaxis.title.text}: %{y:.2f}<extra></extra>',
    )
    fig.update_layout(_layout())
    return _safe_json(fig)


def _regression_plot(df, num_cols):
    """Regression plot (OLS) + 95% CI."""
    if len(num_cols) < 2:
        return None
    x_col, y_col = num_cols[0], num_cols[1]
    df_r = df[[x_col, y_col]].dropna()

    slope, intercept, r, p, se = scipy_stats.linregress(df_r[x_col], df_r[y_col])
    x_line = np.linspace(df_r[x_col].min(), df_r[x_col].max(), 200)
    y_line = slope * x_line + intercept

    # 95% CI
    n    = len(df_r)
    t_cv = scipy_stats.t.ppf(0.975, df=n - 2)
    x_m  = df_r[x_col].mean()
    s_e  = np.sqrt(np.sum((df_r[y_col] - (slope * df_r[x_col] + intercept)) ** 2) / (n - 2))
    ci   = t_cv * s_e * np.sqrt(1 / n + (x_line - x_m) ** 2 / np.sum((df_r[x_col] - x_m) ** 2))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_r[x_col], y=df_r[y_col], mode='markers',
        name='Data', marker=dict(color=COLORS[0], size=5, opacity=0.6),
        hovertemplate=f'{x_col}: %{{x:.2f}}<br>{y_col}: %{{y:.2f}}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line, mode='lines',
        name=f'OLS (r={r:.3f})',
        line=dict(color=COLORS[3], width=2.5),
    ))
    # CI band
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_line, x_line[::-1]]),
        y=np.concatenate([y_line + ci, (y_line - ci)[::-1]]),
        fill='toself', fillcolor='rgba(238,93,80,0.10)',
        line=dict(color='rgba(0,0,0,0)'),
        name='95% CI', showlegend=True,
    ))
    fig.update_layout(_layout(
        title=f'📈 Regression Plot: {x_col} → {y_col} | R²={r**2:.3f}',
        xaxis_title=x_col, yaxis_title=y_col,
    ))
    _apply_axes(fig)
    return _safe_json(fig)


def _bubble_chart(df, num_cols, cat_cols):
    """Bubble chart (x, y, size = 3 kolom numerik pertama)."""
    if len(num_cols) < 3:
        return None
    x_col, y_col, size_col = num_cols[0], num_cols[1], num_cols[2]
    color_col = cat_cols[0] if cat_cols and df[cat_cols[0]].nunique() <= 12 else None

    df_b = df[[x_col, y_col, size_col] + ([color_col] if color_col else [])].dropna()
    size_scaled = (df_b[size_col] - df_b[size_col].min()) / (df_b[size_col].max() - df_b[size_col].min() + 1e-9) * 35 + 5

    fig = go.Figure()
    if color_col:
        for i, cat in enumerate(df_b[color_col].unique()):
            mask = df_b[color_col] == cat
            fig.add_trace(go.Scatter(
                x=df_b.loc[mask, x_col], y=df_b.loc[mask, y_col],
                mode='markers', name=str(cat),
                marker=dict(size=size_scaled[mask], color=COLORS[i % len(COLORS)],
                            opacity=0.65, line=dict(width=0.5, color='white')),
                hovertemplate=f'{x_col}: %{{x:.2f}}<br>{y_col}: %{{y:.2f}}<br>{size_col}: %{{marker.size:.1f}}<extra>{cat}</extra>',
            ))
    else:
        fig.add_trace(go.Scatter(
            x=df_b[x_col], y=df_b[y_col], mode='markers',
            marker=dict(size=size_scaled, color=COLORS[0], opacity=0.65,
                        line=dict(width=0.5, color='white')),
            hovertemplate=f'{x_col}: %{{x:.2f}}<br>{y_col}: %{{y:.2f}}<br>{size_col}: %{{marker.size:.1f}}<extra></extra>',
        ))

    fig.update_layout(_layout(
        title=f'🫧 Bubble Chart: {x_col} × {y_col} (size={size_col})',
        xaxis_title=x_col, yaxis_title=y_col,
    ))
    _apply_axes(fig)
    return _safe_json(fig)


# ════════════════════════════════════════════════════════════════════════════
# d) CATEGORICAL vs NUMERICAL
# ════════════════════════════════════════════════════════════════════════════

def _box_cat_num(df, num_cols, cat_cols):
    """Boxplot by category."""
    num_col, cat_col = num_cols[0], cat_cols[0]
    df_f = _top_cats(df, cat_col)

    fig = px.box(
        df_f, x=cat_col, y=num_col,
        color=cat_col, color_discrete_sequence=COLORS,
        title=f'📦 Boxplot: {num_col} by {cat_col}',
        points='outliers',
    )
    fig.update_layout(_layout(showlegend=False))
    _apply_axes(fig)
    return _safe_json(fig)


def _violin_cat_num(df, num_cols, cat_cols):
    """Violin plot by category."""
    num_col, cat_col = num_cols[0], cat_cols[0]
    df_f = _top_cats(df, cat_col)

    fig = px.violin(
        df_f, x=cat_col, y=num_col,
        color=cat_col, color_discrete_sequence=COLORS,
        box=True, points='outliers',
        title=f'🎻 Violin: {num_col} by {cat_col}',
    )
    fig.update_layout(_layout(showlegend=False))
    _apply_axes(fig)
    return _safe_json(fig)


def _grouped_bar(df, num_cols, cat_cols):
    """Grouped bar chart: mean of numeric per category."""
    if len(cat_cols) < 1:
        return None
    num_col  = num_cols[0]
    cat_col  = cat_cols[0]
    cat_col2 = cat_cols[1] if len(cat_cols) > 1 else None

    if cat_col2 and df[cat_col2].nunique() <= 6:
        grp = df.groupby([cat_col, cat_col2])[num_col].mean().reset_index()
        grp.columns = [cat_col, cat_col2, 'Mean']
        fig = px.bar(
            grp, x=cat_col, y='Mean', color=cat_col2,
            barmode='group', color_discrete_sequence=COLORS,
            title=f'📊 Grouped Bar: Mean {num_col} by {cat_col} & {cat_col2}',
            text_auto='.2f',
        )
    else:
        grp = df.groupby(cat_col)[num_col].mean().reset_index()
        grp.columns = [cat_col, 'Mean']
        fig = px.bar(
            grp.head(10), x=cat_col, y='Mean',
            color='Mean', color_continuous_scale='Blues',
            title=f'📊 Bar Chart: Mean {num_col} by {cat_col}',
            text_auto='.2f',
        )
        fig.update_layout(coloraxis_showscale=False)

    fig.update_layout(_layout())
    _apply_axes(fig)
    return _safe_json(fig)


def _strip_plot(df, num_cols, cat_cols):
    """Strip plot."""
    num_col, cat_col = num_cols[0], cat_cols[0]
    df_f = _top_cats(df, cat_col)

    fig = px.strip(
        df_f, x=cat_col, y=num_col,
        color=cat_col, color_discrete_sequence=COLORS,
        title=f'⚡ Strip Plot: {num_col} by {cat_col}',
    )
    fig.update_layout(_layout(showlegend=False))
    _apply_axes(fig)
    return _safe_json(fig)


# ════════════════════════════════════════════════════════════════════════════
# e) KOMPARASI
# ════════════════════════════════════════════════════════════════════════════

def _violin_compare(df, num_cols):
    """Violin compare — semua variabel numerik berdampingan."""
    return _violin_num(df, num_cols)  # Alias — sudah bagus


def _grouped_bar_compare(df, num_cols):
    """Grouped bar — mean & std semua variabel numerik."""
    stats_df = pd.DataFrame({
        'Column': num_cols,
        'Mean'  : [df[c].mean() for c in num_cols],
        'Std'   : [df[c].std()  for c in num_cols],
    })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Mean', x=stats_df['Column'], y=stats_df['Mean'],
        marker_color=COLORS[0], opacity=0.85,
        error_y=dict(type='data', array=stats_df['Std'], visible=True),
        hovertemplate='%{x}<br>Mean: %{y:.3f}<extra></extra>',
    ))
    fig.update_layout(_layout(
        title='📊 Grouped Bar — Mean ± Std (All Numeric Columns)',
        barmode='group',
    ))
    _apply_axes(fig)
    return _safe_json(fig)


def _parallel_coords(df, num_cols, cat_cols):
    """Parallel coordinates — pola multivariabel."""
    cols = num_cols[:6]
    df_p = df[cols].dropna().sample(min(500, len(df)), random_state=42)

    # Color by first cat col if available
    color_vals = None
    color_label = 'Index'
    if cat_cols:
        cc = cat_cols[0]
        df_p = df.loc[df_p.index, cols + [cc]].dropna()
        codes, _ = pd.factorize(df_p[cc])
        color_vals  = codes
        color_label = cc
    else:
        color_vals = np.arange(len(df_p))

    dims = [dict(label=c, values=df_p[c]) for c in cols]

    fig = go.Figure(go.Parcoords(
        line=dict(color=color_vals, colorscale='Viridis', showscale=True,
                  colorbar=dict(title=color_label, thickness=12)),
        dimensions=dims,
    ))
    fig.update_layout(_layout(title='🔗 Parallel Coordinates — Multivariable Pattern'))
    return _safe_json(fig)


# ════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

def generate_plots(df, num_cols, cat_cols):
    """
    Menghasilkan semua grafik Plotly dalam format JSON.
    Mengembalikan dict { key: plotly_json }.
    
    OPTIMASI: Untuk dataset besar (>5000 baris), ambil sample untuk visualisasi
    agar response JSON tidak terlalu besar dan loading cepat.
    """
    # ── SAMPLING: Gunakan sample jika dataset > 5000 baris ──────────────────────
    if len(df) > 5000:
        df_viz = df.sample(n=5000, random_state=42)
    else:
        df_viz = df
    
    plots = {}

    def _try(key, fn, *args):
        try:
            result = fn(*args)
            if result is not None:
                plots[key] = result
        except Exception as e:
            print(f"[visualizations] Skipping '{key}': {e}")

    # ── a) Numerical ──────────────────────────────────────────────────────────
    if num_cols:
        _try('hist_num',     _hist_num,     df_viz, num_cols)
        _try('density_num',  _density_num,  df_viz, num_cols)
        _try('boxplot_num',  _boxplot_num,  df_viz, num_cols)
        _try('qq_num',       _qq_num,       df_viz, num_cols)
        _try('violin_num',   _violin_num,   df_viz, num_cols)

    # ── b) Categorical ────────────────────────────────────────────────────────
    if cat_cols:
        _try('bar_cat',    _bar_cat,    df_viz, cat_cols)
        _try('pie_cat',    _pie_cat,    df_viz, cat_cols)
        _try('count_cat',  _count_cat,  df_viz, cat_cols)
        _try('pareto_cat', _pareto_cat, df_viz, cat_cols)

    # ── c) Bivariate & Multivariate ───────────────────────────────────────────
    if len(num_cols) >= 2:
        _try('scatter_biv',    _scatter_biv,    df_viz, num_cols, cat_cols)
        _try('heatmap',        _heatmap,        df_viz, num_cols)
        _try('scatter_matrix', _scatter_matrix, df_viz, num_cols, cat_cols)
        _try('regression_plot',_regression_plot,df_viz, num_cols)
        _try('bubble_chart',   _bubble_chart,   df_viz, num_cols, cat_cols)

    # ── d) Cat vs Num ─────────────────────────────────────────────────────────
    if num_cols and cat_cols:
        _try('box_cat_num',    _box_cat_num,    df_viz, num_cols, cat_cols)
        _try('violin_cat_num', _violin_cat_num, df_viz, num_cols, cat_cols)
        _try('grouped_bar',    _grouped_bar,    df_viz, num_cols, cat_cols)
        _try('strip_plot',     _strip_plot,     df_viz, num_cols, cat_cols)

    # ── e) Komparasi ──────────────────────────────────────────────────────────
    if len(num_cols) >= 2:
        _try('violin_compare',       _violin_compare,       df_viz, num_cols)
        _try('grouped_bar_compare',  _grouped_bar_compare,  df_viz, num_cols)
        _try('parallel_coords',      _parallel_coords,      df_viz, num_cols, cat_cols)

    return plots