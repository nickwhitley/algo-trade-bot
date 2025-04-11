import pandas as pd
import plotly.graph_objects as go
from tqdm import tqdm
tqdm.pandas()

def apply_downtrend(df):
    """
    Apply downtrend detection without progress bar intergration
    """
    df['ma_10'] = df.mid_c.rolling(window=10).mean()
    df['ma_150'] = df.mid_c.rolling(window=150).mean()
    df['in_downtrend'] = df['ma_10'] < df['ma_150']
    df.dropna(inplace=True)

def detect_downtrend(row):
    return row['ma_10'] < row['ma_150']

def apply_downtrend_with_progress(df):
    """
    Apply downtrend detection with progress bar intergration
    """
    tqdm.pandas(desc="Detecting downtrend")
    df['ma_10'] = df.mid_c.rolling(window=10).mean()
    df['ma_150'] = df.mid_c.rolling(window=150).mean()
    df.dropna(inplace=True)
    df['in_downtrend'] = df.progress_apply(detect_downtrend, axis=1)

