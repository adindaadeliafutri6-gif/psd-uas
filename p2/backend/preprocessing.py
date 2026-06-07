import pandas as pd

def detect_data_types(df):
    """Classifies columns into Numerical and Categorical."""
    # Detect numerical columns (integers and floats)
    num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # Detect categorical columns (objects, categories, strings)
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    
    return num_cols, cat_cols