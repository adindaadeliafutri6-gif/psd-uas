"""
backend/advanced_stats.py
Week 15 — Analisis Statistik Tingkat Lanjut
Meliputi: Quartile, IQR, CV, Percentiles, Chi-Square, Cramér's V, Point-Biserial
"""
import pandas as pd
import numpy as np
from scipy import stats

def get_advanced_stats(df, num_cols, cat_cols):
    """Menghasilkan statistik lanjutan untuk dashboard Week 15."""
    result = {}

    # ─── 1. ADVANCED NUMERICAL STATS ───────────────────────────────────────────
    adv_num = []
    for col in num_cols:
        s = df[col].dropna()
        if s.empty:
            continue

        q1, q2, q3 = s.quantile([0.25, 0.50, 0.75]).values
        iqr = q3 - q1
        cv = (s.std() / s.mean() * 100) if s.mean() != 0 else 0
        p5, p95 = s.quantile([0.05, 0.95]).values

        # Shapiro-Wilk
        sample = s if len(s) <= 5000 else s.sample(5000, random_state=42)
        try:
            if sample.nunique() > 1:
                _, p_val = stats.shapiro(sample)
                normality = "Normal (p>{:.3f})".format(round(p_val, 3)) if p_val > 0.05 else "Not Normal"
            else:
                normality = "Constant"
        except Exception:
            normality = "N/A"

        adv_num.append({
            "Column": col,
            "Q1": round(q1, 3),
            "Q2 (Median)": round(q2, 3),
            "Q3": round(q3, 3),
            "IQR": round(iqr, 3),
            "CV (%)": round(cv, 2),
            "P5": round(p5, 3),
            "P95": round(p95, 3),
            "Shapiro-Wilk": normality
        })

    result['adv_num'] = adv_num

    # ─── 2. CORRELATION MATRIX TABLE ───────────────────────────────────────────
    if len(num_cols) > 1:
        corr_df = df[num_cols].corr().round(3)
        result['corr_cols'] = list(corr_df.columns)
        result['corr_matrix'] = corr_df.values.tolist()

        # Top 5 strongest pairs
        pairs = []
        cols = list(corr_df.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr_df.iloc[i, j]
                pairs.append((cols[i], cols[j], round(val, 3)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        result['top_corr_pairs'] = pairs[:5]
    else:
        result['corr_cols'] = []
        result['corr_matrix'] = []
        result['top_corr_pairs'] = []

    # ─── 3. CATEGORICAL ANALYSIS ────────────────────────────────────────────────
    cat_freq = []
    for col in cat_cols[:3]:  # Batasi 3 kolom agar tidak berat
        vc = df[col].value_counts(normalize=False).head(10)
        pct = df[col].value_counts(normalize=True).head(10) * 100
        cat_freq.append({
            "col": col,
            "labels": list(vc.index.astype(str)),
            "counts": list(vc.values.astype(int)),
            "pct": [round(p, 1) for p in pct.values]
        })
    result['cat_freq'] = cat_freq

    # ─── 4. CHI-SQUARE & CRAMÉR'S V (antar cat cols) ───────────────────────────
    assoc = []
    if len(cat_cols) >= 2:
        for i in range(min(len(cat_cols), 4)):
            for j in range(i + 1, min(len(cat_cols), 4)):
                col_a, col_b = cat_cols[i], cat_cols[j]
                try:
                    ct = pd.crosstab(df[col_a], df[col_b])
                    chi2, p, dof, _ = stats.chi2_contingency(ct)
                    n = ct.values.sum()
                    v = np.sqrt(chi2 / (n * (min(ct.shape) - 1))) if min(ct.shape) > 1 else 0
                    assoc.append({
                        "col_a": col_a, "col_b": col_b,
                        "chi2": round(chi2, 2), "p": round(p, 4),
                        "cramers_v": round(v, 3),
                        "strength": "Kuat" if v > 0.5 else ("Sedang" if v > 0.3 else "Lemah")
                    })
                except Exception:
                    pass
    result['cat_assoc'] = assoc

    # ─── 5. NUMERICAL vs CATEGORICAL (Point-Biserial / ANOVA Summary) ──────────
    num_cat_analysis = []
    if num_cols and cat_cols:
        for nc in num_cols[:3]:
            for cc in cat_cols[:2]:
                try:
                    groups = df.groupby(cc)[nc].agg(['mean', 'std', 'count']).dropna()
                    groups = groups[groups['count'] >= 2]
                    if groups.empty:
                        continue
                    group_means = groups['mean'].round(3).to_dict()
                    # One-way ANOVA
                    group_data = [df[df[cc] == g][nc].dropna().values for g in groups.index]
                    if len(group_data) >= 2 and all(len(g) >= 2 for g in group_data):
                        f_stat, p_anova = stats.f_oneway(*group_data)
                        num_cat_analysis.append({
                            "num": nc, "cat": cc,
                            "group_means": group_means,
                            "f_stat": round(f_stat, 3),
                            "p_anova": round(p_anova, 4),
                            "significant": p_anova < 0.05
                        })
                except Exception:
                    pass
    result['num_cat'] = num_cat_analysis[:4]  # Max 4

    return result
