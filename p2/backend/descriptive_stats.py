import pandas as pd
import numpy as np
from scipy.stats import shapiro

def get_summary_metrics(df):
    """Returns high-level dataset metrics."""
    return {
        "total_rows": f"{len(df):,}",
        "total_columns": f"{len(df.columns):,}",
        "missing_cells": f"{df.isna().sum().sum():,}"
    }

def get_descriptive_stats(df, num_cols, cat_cols):
    """Calculates Advanced Descriptive Statistics."""
    total_rows = len(df)
    num_stats = []
    
    # ---------------- NUMERICAL VARIABLES ----------------
    for col in num_cols:
        clean_series = df[col].dropna()
        n_clean = len(clean_series)
        
        # Missing Values
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / total_rows) * 100 if total_rows > 0 else 0
        
        if n_clean > 0:
            # Basic Stats
            mean_val = clean_series.mean()
            median_val = clean_series.median()
            min_val = clean_series.min()
            max_val = clean_series.max()
            std_val = clean_series.std()
            var_val = clean_series.var()
            
            # Mode
            mode_s = clean_series.mode()
            mode_val = mode_s.iloc[0] if not mode_s.empty else "N/A"
            
            # Skewness & Kurtosis
            skew_val = clean_series.skew()
            kurt_val = clean_series.kurt()
            
            # Normal Distribution Test (Shapiro-Wilk Test)
            if n_clean >= 3:
                # Ambil sampel max 5000 agar komputasi tidak berat & scipy tidak warning
                sample_series = clean_series if n_clean <= 5000 else clean_series.sample(5000, random_state=42)
                if sample_series.nunique() > 1: # Cek jika datanya tidak statis (ada variansi)
                    stat, p_value = shapiro(sample_series)
                    normality = "Normal" if p_value > 0.05 else "Not Normal"
                else:
                    normality = "Not Normal"
            else:
                normality = "N/A"
            
            # Number of Outliers (IQR Method)
            Q1 = clean_series.quantile(0.25)
            Q3 = clean_series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers_count = ((clean_series < lower_bound) | (clean_series > upper_bound)).sum()
        else:
            mean_val = median_val = min_val = max_val = std_val = var_val = mode_val = "N/A"
            skew_val = kurt_val = "N/A"
            normality = "N/A"
            outliers_count = 0
            
        def fmt(val): return round(val, 2) if isinstance(val, (int, float)) and pd.notna(val) else val

        num_stats.append({
            "Column": col,
            "Mean": fmt(mean_val),
            "Median": fmt(median_val),
            "Min": fmt(min_val),
            "Max": fmt(max_val),
            "Std Dev": fmt(std_val),
            "Variance": fmt(var_val),
            "Mode": fmt(mode_val),
            "Skewness": fmt(skew_val),
            "Kurtosis": fmt(kurt_val),
            "Missing Count": int(missing_count),
            "Missing %": f"{round(missing_pct, 2)}%",
            "Normality": normality,
            "Outliers": int(outliers_count)
        })
    
    # ---------------- CATEGORICAL VARIABLES ----------------
    cat_stats = []
    for col in cat_cols:
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / total_rows) * 100 if total_rows > 0 else 0
        
        clean_series = df[col].dropna()
        
        if not clean_series.empty:
            unique_val = clean_series.nunique()
            mode_s = clean_series.mode()
            mode_val = mode_s.iloc[0] if not mode_s.empty else "N/A"
            
            # Mode Frequency & Percentage
            mode_freq = clean_series.value_counts().iloc[0] if not clean_series.value_counts().empty else 0
            mode_pct = (mode_freq / len(clean_series)) * 100
        else:
            unique_val = mode_freq = mode_pct = 0
            mode_val = "N/A"
            
        cat_stats.append({
            "Column": col,
            "Unique": int(unique_val),
            "Mode": str(mode_val),
            "Mode Freq": int(mode_freq),
            "Mode %": f"{round(mode_pct, 2)}%",
            "Missing Count": int(missing_count),
            "Missing %": f"{round(missing_pct, 2)}%"
        })
        
    return num_stats, cat_stats