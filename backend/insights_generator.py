"""
backend/insights_generator.py
Week 15 — Intelligent Insight Generator (Complete)

Insights yang dihasilkan:
  1.  Kualitas data (missing values)
  2.  Ukuran & struktur dataset
  3.  Variabel dengan rata-rata tertinggi
  4.  Variabel dengan missing value terbanyak
  5.  Variabel dengan outlier terbanyak
  6.  Variabel dengan standar deviasi terbesar
  7.  Korelasi terkuat antar variabel
  8.  Identifikasi distribusi normal vs tidak normal
  9.  Distribusi kategorik (class balance)
  10. Time series patterns (jika ada — dioper dari time_series.py)
  11. Rekomendasi analisis lanjut
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from backend.data_sanitizer import sanitize_series, safe_corr_matrix


# ─── Helper ──────────────────────────────────────────────────────────────────

def _pct(a, b):
    return round(a / b * 100, 1) if b > 0 else 0.0


def _normality(series, max_sample=5000):
    """Mengembalikan 'Normal' atau 'Not Normal' via Shapiro-Wilk."""
    clean = sanitize_series(series)  # forced numeric, drop NaN
    if len(clean) < 3 or clean.nunique() <= 1:
        return 'N/A'
    sample = clean if len(clean) <= max_sample else clean.sample(max_sample, random_state=42)
    try:
        _, p = scipy_stats.shapiro(sample)
        return 'Normal' if p > 0.05 else 'Not Normal'
    except Exception:
        return 'N/A'


def _outlier_count(series):
    """Hitung outlier dengan metode IQR (safe terhadap non-numeric)."""
    clean = sanitize_series(series)  # forced numeric, drop NaN
    if len(clean) < 4:
        return 0
    try:
        q1, q3 = float(clean.quantile(0.25)), float(clean.quantile(0.75))
        iqr = q3 - q1
        if iqr == 0:
            return 0
        return int(((clean < q1 - 1.5 * iqr) | (clean > q3 + 1.5 * iqr)).sum())
    except Exception:
        return 0


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def generate_auto_insights(df, num_cols, cat_cols, ts_insights=None):
    """
    Menghasilkan list insight otomatis berbasis data.

    Parameters
    ----------
    df          : DataFrame lengkap
    num_cols    : list kolom numerik
    cat_cols    : list kolom kategorik
    ts_insights : list insight dari time_series.py (opsional)

    Returns
    -------
    insights : list[dict]  →  {type, icon, title, desc}
    """
    insights = []
    total_rows  = len(df)
    total_cells = df.size

    # ── 1. KUALITAS DATA (missing values) ────────────────────────────────────
    total_missing = int(df.isna().sum().sum())
    miss_pct = _pct(total_missing, total_cells)

    if total_missing == 0:
        insights.append({
            'type': 'success', 'icon': 'fa-check-circle',
            'title': ' Excellent Data Quality — Zero Missing Values',
            'desc': ('Tidak ditemukan missing values sama sekali. '
                     'Dataset bersih dan siap digunakan untuk analisis statistik '
                     'maupun pemodelan machine learning tanpa preprocessing tambahan.')
        })
    elif miss_pct < 5:
        insights.append({
            'type': 'warning', 'icon': 'fa-exclamation-triangle',
            'title': f' Minor Missing Values ({miss_pct}%)',
            'desc': (f'Terdapat {total_missing:,} sel kosong ({miss_pct}% dari total data). '
                     'Tingkat ini masih tergolong aman, namun disarankan melakukan imputasi '
                     '(mean/median/modus) sebelum pemodelan.')
        })
    else:
        insights.append({
            'type': 'danger', 'icon': 'fa-times-circle',
            'title': f' High Missing Rate ({miss_pct}%)',
            'desc': (f'Dataset memiliki {total_missing:,} missing values ({miss_pct}% dari total data). '
                     'Tingkat ini cukup tinggi dan dapat mempengaruhi validitas analisis. '
                     'Pertimbangkan strategi penanganan missing data yang lebih agresif '
                     '(imputation, deletion, atau model-based filling).')
        })

    # ── 2. UKURAN & STRUKTUR DATASET ─────────────────────────────────────────
    if total_rows >= 100_000:
        size_note = 'Dataset berukuran sangat besar. Pertimbangkan sampling strategis atau distributed computing.'
    elif total_rows >= 10_000:
        size_note = 'Dataset berukuran besar — cocok untuk analisis statistik yang robust dan machine learning.'
    elif total_rows >= 1_000:
        size_note = 'Ukuran dataset cukup representatif untuk analisis statistik yang handal.'
    elif total_rows >= 100:
        size_note = 'Dataset berukuran sedang. Hasil analisis cukup stabil namun perlu divalidasi.'
    else:
        size_note = 'Dataset berukuran kecil (< 100 baris). Hasil statistik mungkin kurang stabil — hati-hati dalam generalisasi.'

    insights.append({
        'type': 'info', 'icon': 'fa-database',
        'title': f' Dataset: {total_rows:,} Rows × {len(df.columns)} Columns',
        'desc': (f'{size_note} '
                 f'Terdiri dari {len(num_cols)} kolom numerik dan {len(cat_cols)} kolom kategorik.')
    })

    # ── 3. VARIABEL DENGAN RATA-RATA TERTINGGI ────────────────────────────────
    if num_cols:
        means = {}
        for col in num_cols:
            try:
                s = sanitize_series(df[col] if col in df.columns else pd.Series(dtype=float), col)
                if not s.empty:
                    means[col] = float(s.mean())
            except Exception:
                pass
        if means:
            top_mean_col = max(means, key=means.get)
            top_mean_val = round(means[top_mean_col], 2)
            s_top = sanitize_series(df[top_mean_col], top_mean_col)
            median_v = round(float(s_top.median()), 2) if not s_top.empty else 'N/A'
            std_v    = round(float(s_top.std()), 2) if len(s_top) >= 2 else 'N/A'
            insights.append({
                'type': 'primary', 'icon': 'fa-arrow-up',
                'title': f' Highest Average Value: {top_mean_col}',
                'desc': (f'Kolom <strong>{top_mean_col}</strong> memiliki nilai rata-rata tertinggi '
                         f'sebesar <strong>{top_mean_val:,}</strong>. '
                         f'Median: {median_v}, Std: {std_v}.')
            })

    # ── 4. VARIABEL DENGAN MISSING VALUE TERBANYAK ───────────────────────────
    miss_per_col = df.isna().sum()
    if miss_per_col.max() > 0:
        worst_col   = miss_per_col.idxmax()
        worst_count = int(miss_per_col.max())
        worst_pct   = _pct(worst_count, total_rows)
        insights.append({
            'type': 'danger', 'icon': 'fa-exclamation',
            'title': f' Most Missing Values: {worst_col}',
            'desc': (f'Kolom <strong>{worst_col}</strong> memiliki missing values terbanyak: '
                     f'<strong>{worst_count:,} baris ({worst_pct}%)</strong>. '
                     f'{"Disarankan untuk membuang kolom ini jika >50% hilang." if worst_pct > 50 else "Pertimbangkan imputasi untuk kolom ini."}')
        })

    # ── 5. VARIABEL DENGAN OUTLIER TERBANYAK ─────────────────────────────────
    if num_cols:
        outlier_counts = {col: _outlier_count(df[col]) for col in num_cols}
        max_out_col = max(outlier_counts, key=outlier_counts.get)
        max_out_val = outlier_counts[max_out_col]
        max_out_pct = _pct(max_out_val, total_rows)

        if max_out_val > 0:
            insights.append({
                'type': 'warning', 'icon': 'fa-dot-circle',
                'title': f' Most Outliers: {max_out_col}',
                'desc': (f'Kolom <strong>{max_out_col}</strong> memiliki outlier terbanyak: '
                         f'<strong>{max_out_val:,} titik data ({max_out_pct}%)</strong> '
                         f'berdasarkan metode IQR (±1.5×IQR). '
                         f'Tinjau apakah outlier ini merupakan error data atau nilai ekstrem yang valid.')
            })
        else:
            insights.append({
                'type': 'success', 'icon': 'fa-bullseye',
                'title': ' No Outliers Detected',
                'desc': ('Tidak ditemukan outlier pada seluruh kolom numerik '
                         'menggunakan metode IQR. Data terdistribusi dalam rentang yang wajar.')
            })

    # ── 6. VARIABEL DENGAN STANDAR DEVIASI TERBESAR ──────────────────────────
    if num_cols:
        stds = {}
        for col in num_cols:
            try:
                s = sanitize_series(df[col] if col in df.columns else pd.Series(dtype=float), col)
                if not s.empty and len(s) >= 2:
                    stds[col] = float(s.std())
            except Exception:
                pass
        if stds:
            top_std_col = max(stds, key=stds.get)
            top_std_val = round(stds[top_std_col], 4)
            s_top = sanitize_series(df[top_std_col], top_std_col)
            mean_top = float(s_top.mean()) if not s_top.empty else 0
            cv = round(top_std_val / mean_top * 100, 1) if mean_top != 0 else 0
            insights.append({
                'type': 'orange', 'icon': 'fa-ruler-horizontal',
                'title': f' Highest Std Deviation: {top_std_col}',
                'desc': (f'Kolom <strong>{top_std_col}</strong> memiliki standar deviasi terbesar '
                         f'sebesar <strong>{top_std_val:,}</strong> (CV={cv}%). '
                         f'Variabilitas {"sangat tinggi" if cv > 30 else ("tinggi" if cv > 15 else "wajar")} '
                         f'pada kolom ini menunjukkan sebaran data yang {"lebar" if cv > 15 else "moderat"}.')
            })


    # ── 7. KORELASI TERKUAT — via safe_corr_matrix ────────────────────────────
    if len(num_cols) > 1:
        try:
            valid_cols, corr_df = safe_corr_matrix(df, num_cols)
            if corr_df is not None and len(valid_cols) >= 2:
                np.fill_diagonal(corr_df.values, np.nan)
                abs_corr = corr_df.abs()
                flat     = abs_corr.values.flatten()
                flat_nan = flat[~np.isnan(flat)]
                if len(flat_nan) > 0:
                    max_idx  = np.unravel_index(np.nanargmax(abs_corr.values), abs_corr.shape)
                    col_a, col_b = valid_cols[max_idx[0]], valid_cols[max_idx[1]]
                    r_val = round(float(corr_df.iloc[max_idx[0], max_idx[1]]), 3)
                    direction = 'positif' if r_val > 0 else 'negatif'
                    strength  = ('Sangat Kuat' if abs(r_val) > 0.8
                                 else 'Kuat' if abs(r_val) > 0.6
                                 else 'Sedang' if abs(r_val) > 0.4
                                 else 'Lemah')
                    insights.append({
                        'type': 'primary', 'icon': 'fa-link',
                        'title': f' Strongest Correlation: {col_a} ↔ {col_b} (r={r_val})',
                        'desc': (f'Korelasi {strength} ({direction}) ditemukan antara '
                                 f'<strong>{col_a}</strong> dan <strong>{col_b}</strong> dengan r = {r_val}. '
                                 f'{"Hubungan ini sangat signifikan dan layak diinvestigasi lebih lanjut." if abs(r_val) > 0.6 else "Hubungan ini moderat dan mungkin dipengaruhi variabel lain."}'
                                 f' (R² = {round(r_val**2, 3)})')
                    })
        except Exception:
            pass

    # ── 8. DISTRIBUSI NORMAL vs TIDAK NORMAL ─────────────────────────────────
    if num_cols:
        normal_cols     = []
        not_normal_cols = []
        for col in num_cols:
            result = _normality(df[col])
            if result == 'Normal':
                normal_cols.append(col)
            elif result == 'Not Normal':
                not_normal_cols.append(col)

        if normal_cols or not_normal_cols:
            total_tested = len(normal_cols) + len(not_normal_cols)
            normal_pct   = _pct(len(normal_cols), total_tested)
            nn_list = ', '.join(not_normal_cols[:3]) + (f' (+{len(not_normal_cols)-3} lainnya)' if len(not_normal_cols) > 3 else '')
            n_list  = ', '.join(normal_cols[:3])     + (f' (+{len(normal_cols)-3} lainnya)'     if len(normal_cols) > 3 else '')

            insights.append({
                'type': 'info', 'icon': 'fa-bell',
                'title': f' Normality Test — {len(normal_cols)}/{total_tested} Columns Normal',
                'desc': (
                    (f'Kolom berdistribusi normal: {n_list}. ' if normal_cols else '') +
                    (f'Kolom TIDAK normal: {nn_list}. ' if not_normal_cols else '') +
                    (f'Kolom tidak normal ({100 - normal_pct}%) memerlukan uji non-parametrik '
                     f'(Mann-Whitney, Kruskal-Wallis) atau transformasi data '
                     f'(log, sqrt, Box-Cox) sebelum analisis parametrik.'
                     if not_normal_cols else
                     'Semua kolom berdistribusi normal — analisis parametrik dapat dilakukan.')
                )
            })

        # Skewness — sanitized
        skewed = []
        for col in num_cols:
            try:
                s = sanitize_series(df[col] if col in df.columns else pd.Series(dtype=float), col)
                if not s.empty and s.nunique() >= 2:
                    skw = float(s.skew())
                    if abs(skw) > 1:
                        skewed.append(f'{col} (skew={round(skw, 2)})')
            except Exception:
                pass
        if skewed:
            insights.append({
                'type': 'warning', 'icon': 'fa-chart-line',
                'title': f' Skewed Distributions: {len(skewed)} Column(s)',
                'desc': (f'Kolom berikut memiliki skewness > 1: {", ".join(skewed[:4])}. '
                         'Distribusi miring ini dapat memengaruhi hasil analisis parametrik. '
                         'Pertimbangkan transformasi log atau Box-Cox.')
            })

    # ── 9. DISTRIBUSI KATEGORIK ───────────────────────────────────────────────
    if cat_cols:
        col = cat_cols[0]
        vc  = df[col].value_counts()
        dom_pct = _pct(vc.iloc[0], total_rows) if not vc.empty else 0

        if dom_pct > 70:
            balance_type  = 'danger'
            balance_label = 'Sangat Tidak Seimbang'
            balance_note  = f'Kategori "{vc.index[0]}" mendominasi {dom_pct}% data — waspadai class imbalance dalam pemodelan.'
        elif dom_pct > 50:
            balance_type  = 'warning'
            balance_label = 'Kurang Seimbang'
            balance_note  = f'Kategori "{vc.index[0]}" cukup dominan ({dom_pct}%). Pertimbangkan oversampling jika digunakan untuk klasifikasi.'
        else:
            balance_type  = 'success'
            balance_label = 'Seimbang'
            balance_note  = f'Distribusi kategori cukup merata. Kategori terbanyak: "{vc.index[0]}" ({dom_pct}%).'

        insights.append({
            'type': balance_type, 'icon': 'fa-tags',
            'title': f' Categorical Balance ({col}): {balance_label}',
            'desc': (f'{balance_note} '
                     f'Total {df[col].nunique()} kategori unik pada kolom {col}.')
        })

    # ── 10. TIME SERIES INSIGHTS (dari time_series.py) ───────────────────────
    if ts_insights:
        for ts_ins in ts_insights:
            insights.append(ts_ins)

    # ── 11. REKOMENDASI ANALISIS LANJUT ──────────────────────────────────────
    recs = []
    if num_cols and cat_cols:
        recs.append('One-Way ANOVA / T-Test untuk membandingkan rata-rata antar grup kategorik')
    if len(num_cols) > 1:
        recs.append('Regresi Linear / Logistik untuk prediksi dan pemodelan')
    if len(cat_cols) >= 2:
        recs.append('Chi-Square + Cramér\'s V untuk asosiasi antar variabel kategorik')
    if any(_normality(df[c]) == 'Not Normal' for c in num_cols):
        recs.append('Uji Non-Parametrik (Mann-Whitney, Spearman) untuk kolom tidak normal')
    if len(num_cols) >= 3:
        recs.append('Principal Component Analysis (PCA) untuk reduksi dimensi')

    if recs:
        insights.append({
            'type': 'success', 'icon': 'fa-rocket',
            'title': '24n Rekomendasi Analisis Lanjut',
            'desc': 'Berdasarkan struktur dataset ini, teknik yang disarankan: ' + '; '.join(recs) + '.'
        })

    return insights