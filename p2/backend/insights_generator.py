"""
backend/insights_generator.py
Week 15 — Smart Insights Generator (Enhanced)
"""
import pandas as pd
import numpy as np
from scipy import stats


def generate_auto_insights(df, num_cols, cat_cols):
    """Menghasilkan wawasan otomatis yang lebih kaya dari dataset."""
    insights = []

    total_rows = len(df)
    total_missing = df.isna().sum().sum()
    total_cells = df.size

    # ── 1. KUALITAS DATA ─────────────────────────────────────────────────────
    missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0
    if total_missing == 0:
        insights.append({"type": "success", "icon": "fa-check-circle",
                         "title": "Excellent Data Quality",
                         "desc": "Tidak ditemukan missing values. Dataset bersih dan siap digunakan untuk Machine Learning maupun analisis statistik lanjut."})
    elif missing_pct < 5:
        insights.append({"type": "warning", "icon": "fa-exclamation-triangle",
                         "title": f"Data Minor Gaps ({round(missing_pct, 1)}% Missing)",
                         "desc": f"Terdapat {int(total_missing):,} sel kosong ({round(missing_pct, 1)}% dari total data). Tingkat ini masih aman untuk analisis namun sebaiknya dilakukan imputasi."})
    else:
        insights.append({"type": "danger", "icon": "fa-times-circle",
                         "title": f"High Missing Rate ({round(missing_pct, 1)}%)",
                         "desc": f"Dataset memiliki {int(total_missing):,} missing values ({round(missing_pct, 1)}%). Disarankan melakukan pembersihan data sebelum analisis."})

    # ── 2. UKURAN DATASET ────────────────────────────────────────────────────
    if total_rows >= 10000:
        size_note = "Dataset berukuran besar (Big Data). Pertimbangkan sampling atau penggunaan distributed computing."
    elif total_rows >= 1000:
        size_note = "Ukuran dataset cukup representatif untuk analisis statistik yang handal."
    else:
        size_note = "Dataset berukuran kecil. Hasil analisis mungkin kurang stabil secara statistik."
    insights.append({"type": "info", "icon": "fa-database",
                     "title": f"Dataset Size: {total_rows:,} Rows × {len(df.columns)} Cols",
                     "desc": size_note})

    # ── 3. DISTRIBUSI NUMERIK ────────────────────────────────────────────────
    if num_cols:
        skewed_cols = []
        outlier_cols = []
        for col in num_cols:
            s = df[col].dropna()
            if len(s) < 3:
                continue
            skew = s.skew()
            if abs(skew) > 1:
                skewed_cols.append(f"{col} (skew={round(skew,2)})")
            # Outliers IQR
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            n_out = ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()
            if n_out > 0:
                outlier_cols.append(f"{col} ({n_out} outliers)")

        if skewed_cols:
            insights.append({"type": "warning", "icon": "fa-chart-line",
                             "title": "Skewed Distributions Detected",
                             "desc": f"Kolom berikut memiliki distribusi miring (skewness > 1): {', '.join(skewed_cols[:3])}. Pertimbangkan transformasi log atau Box-Cox."})

        if outlier_cols:
            insights.append({"type": "danger", "icon": "fa-exclamation",
                             "title": "Outliers Detected",
                             "desc": f"Outlier ditemukan pada: {', '.join(outlier_cols[:3])}. Tinjau apakah ini error data atau nilai ekstrem yang valid."})

    # ── 4. KORELASI ──────────────────────────────────────────────────────────
    if len(num_cols) > 1:
        try:
            corr = df[num_cols].corr().abs()
            # Hapus diagonal
            np.fill_diagonal(corr.values, 0)
            max_val = corr.values.max()
            max_idx = np.unravel_index(corr.values.argmax(), corr.shape)
            col_a, col_b = num_cols[max_idx[0]], num_cols[max_idx[1]]
            raw_corr = df[num_cols].corr().iloc[max_idx[0], max_idx[1]]
            direction = "positif" if raw_corr > 0 else "negatif"
            strength = "Sangat Kuat" if max_val > 0.8 else ("Kuat" if max_val > 0.6 else ("Sedang" if max_val > 0.4 else "Lemah"))
            insights.append({"type": "primary", "icon": "fa-link",
                             "title": f"Strongest Correlation: r = {round(raw_corr, 3)}",
                             "desc": f"Korelasi {strength} ({direction}) ditemukan antara '{col_a}' dan '{col_b}'. Nilai r = {round(raw_corr, 3)} mengindikasikan hubungan {'linier yang signifikan' if max_val > 0.6 else 'yang perlu diinvestigasi lebih lanjut'}."})
        except Exception:
            pass

    # ── 5. KATEGORIKAL ───────────────────────────────────────────────────────
    if cat_cols:
        col = cat_cols[0]
        vc = df[col].value_counts()
        dominant_pct = (vc.iloc[0] / len(df) * 100) if len(df) > 0 else 0
        if dominant_pct > 70:
            balance = f"TIDAK SEIMBANG — kategori '{vc.index[0]}' mendominasi {round(dominant_pct,1)}% data. Waspada class imbalance pada pemodelan."
        elif dominant_pct > 50:
            balance = f"Cukup seimbang, namun kategori '{vc.index[0]}' masih mendominasi {round(dominant_pct,1)}%."
        else:
            balance = f"Distribusi kategori cukup merata. Kategori terbanyak: '{vc.index[0]}' ({round(dominant_pct,1)}%)."
        insights.append({"type": "info", "icon": "fa-tags",
                         "title": f"Categorical Balance: {col}",
                         "desc": balance})

    # ── 6. REKOMENDASI ANALISIS LANJUT ───────────────────────────────────────
    recs = []
    if num_cols and cat_cols:
        recs.append("ANOVA/T-Test untuk membandingkan rata-rata antar grup")
    if len(num_cols) > 1:
        recs.append("Regresi linear untuk memprediksi variabel target")
    if cat_cols:
        recs.append("Chi-Square untuk menguji asosiasi antar variabel kategorik")
    if recs:
        insights.append({"type": "success", "icon": "fa-rocket",
                         "title": "Rekomendasi Analisis Lanjut",
                         "desc": "Berdasarkan struktur dataset ini, teknik yang disarankan: " + "; ".join(recs) + "."})

    return insights
