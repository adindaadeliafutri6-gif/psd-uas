"""
backend/descriptive_stats.py
Descriptive Statistics Generator — Kelompok 2 ITSB

Numerical columns output:
  Mean, Median, Min, Max, Std Dev, Variance, Mode,
  Skewness, Kurtosis, Missing Count, Missing %, Normality, Outliers

Categorical columns output:
  Unique, Mode, Mode Freq, Mode %, Missing Count, Missing %
"""

import pandas as pd
import numpy as np
from scipy.stats import shapiro


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(val, decimals=2):
    """
    Format angka menjadi float dengan `decimals` digit.
    Jika bukan angka atau NaN → kembalikan string 'N/A'.
    """
    if val is None:
        return "N/A"
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return "N/A"
        return round(f, decimals)
    except (TypeError, ValueError):
        return "N/A"


def _pct(count, total, decimals=2):
    """Hitung persentase dengan aman."""
    if total == 0:
        return "0.00%"
    return f"{round(count / total * 100, decimals)}%"


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY METRICS  (untuk KPI cards di dashboard)
# ─────────────────────────────────────────────────────────────────────────────

def get_summary_metrics(df, num_cols=None, cat_cols=None):
    """
    Mengembalikan dict metrik level dataset.
    Dipanggil di app.py dan dioper ke template sebagai `metrics`.

    num_cols dan cat_cols bersifat opsional — jika tidak diisi,
    akan di-detect otomatis dari df sehingga app.py lama tetap bisa
    memanggil get_summary_metrics(df) tanpa error.

    Keys yang dikembalikan:
        total_rows, total_columns,
        num_count, cat_count,
        missing_cells, missing_pct
    """
    # Auto-detect jika tidak dioper dari app.py
    if num_cols is None:
        num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    if cat_cols is None:
        cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()

    total_rows    = len(df)
    total_columns = len(df.columns)
    missing_cells = int(df.isna().sum().sum())
    total_cells   = total_rows * total_columns
    missing_pct   = round(missing_cells / total_cells * 100, 2) if total_cells > 0 else 0.0

    return {
        "total_rows":     f"{total_rows:,}",
        "total_columns":  f"{total_columns:,}",
        "num_count":      len(num_cols),
        "cat_count":      len(cat_cols),
        "missing_cells":  f"{missing_cells:,}",
        "missing_pct":    f"{missing_pct}%",
    }


# ─────────────────────────────────────────────────────────────────────────────
# DESCRIPTIVE STATS
# ─────────────────────────────────────────────────────────────────────────────

def get_descriptive_stats(df, num_cols, cat_cols):
    """
    Menghitung statistik deskriptif lengkap.

    Returns
    -------
    num_stats : list[dict]
        Satu dict per kolom numerik, berisi 14 metrik.
    cat_stats : list[dict]
        Satu dict per kolom kategorik, berisi 6 metrik.
    """
    total_rows = len(df)

    # ══════════════════════════════════════════════════════════════════════════
    # NUMERICAL STATISTICS
    # ══════════════════════════════════════════════════════════════════════════
    num_stats = []

    for col in num_cols:
        series      = df[col]
        clean       = series.dropna()
        n_clean     = len(clean)

        # ── Missing values ────────────────────────────────────────────────────
        missing_count = int(series.isna().sum())
        missing_pct   = _pct(missing_count, total_rows)

        # ── Jika tidak ada data bersih → isi semua N/A ────────────────────────
        if n_clean == 0:
            num_stats.append({
                "Column":        col,
                "Mean":          "N/A",
                "Median":        "N/A",
                "Min":           "N/A",
                "Max":           "N/A",
                "Std Dev":       "N/A",
                "Variance":      "N/A",
                "Mode":          "N/A",
                "Skewness":      "N/A",
                "Kurtosis":      "N/A",
                "Missing Count": missing_count,
                "Missing %":     missing_pct,
                "Normality":     "N/A",
                "Outliers":      0,
            })
            continue

        # ── Central tendency ──────────────────────────────────────────────────
        mean_val   = _fmt(clean.mean())
        median_val = _fmt(clean.median())
        min_val    = _fmt(clean.min())
        max_val    = _fmt(clean.max())

        # ── Dispersion ────────────────────────────────────────────────────────
        std_val = _fmt(clean.std())
        var_val = _fmt(clean.var())

        # ── Mode ──────────────────────────────────────────────────────────────
        mode_series = clean.mode()
        mode_val    = _fmt(mode_series.iloc[0]) if not mode_series.empty else "N/A"

        # ── Shape ─────────────────────────────────────────────────────────────
        skew_val = _fmt(clean.skew(), decimals=4)
        kurt_val = _fmt(clean.kurt(), decimals=4)

        # ── Normality Test (Shapiro-Wilk) ─────────────────────────────────────
        #    Minimal 3 data; sample max 5000 agar tidak lambat
        if n_clean >= 3:
            sample = clean if n_clean <= 5000 else clean.sample(5000, random_state=42)
            if sample.nunique() <= 1:
                # Data konstan → pasti tidak normal
                normality = "Not Normal"
            else:
                try:
                    _, p_val = shapiro(sample)
                    normality = "Normal" if p_val > 0.05 else "Not Normal"
                except Exception:
                    normality = "N/A"
        else:
            normality = "N/A (n<3)"

        # ── Outliers (metode IQR) ─────────────────────────────────────────────
        q1  = clean.quantile(0.25)
        q3  = clean.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers_count = int(((clean < lower) | (clean > upper)).sum())

        num_stats.append({
            "Column":        col,
            "Mean":          mean_val,
            "Median":        median_val,
            "Min":           min_val,
            "Max":           max_val,
            "Std Dev":       std_val,
            "Variance":      var_val,
            "Mode":          mode_val,
            "Skewness":      skew_val,
            "Kurtosis":      kurt_val,
            "Missing Count": missing_count,
            "Missing %":     missing_pct,
            "Normality":     normality,
            "Outliers":      outliers_count,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORICAL STATISTICS
    # ══════════════════════════════════════════════════════════════════════════
    cat_stats = []

    for col in cat_cols:
        series        = df[col]
        clean         = series.dropna()

        # ── Missing values ────────────────────────────────────────────────────
        missing_count = int(series.isna().sum())
        missing_pct   = _pct(missing_count, total_rows)

        # ── Jika tidak ada data bersih ────────────────────────────────────────
        if clean.empty:
            cat_stats.append({
                "Column":        col,
                "Unique":        0,
                "Mode":          "N/A",
                "Mode Freq":     0,
                "Mode %":        "0.00%",
                "Missing Count": missing_count,
                "Missing %":     missing_pct,
            })
            continue

        # ── Unique categories ─────────────────────────────────────────────────
        unique_count = int(clean.nunique())

        # ── Mode ──────────────────────────────────────────────────────────────
        vc        = clean.value_counts()
        mode_val  = str(vc.index[0]) if not vc.empty else "N/A"
        mode_freq = int(vc.iloc[0])  if not vc.empty else 0
        mode_pct  = _pct(mode_freq, len(clean))

        cat_stats.append({
            "Column":        col,
            "Unique":        unique_count,
            "Mode":          mode_val,
            "Mode Freq":     mode_freq,
            "Mode %":        mode_pct,
            "Missing Count": missing_count,
            "Missing %":     missing_pct,
        })

    return num_stats, cat_stats