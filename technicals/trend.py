import pandas as pd
import plotly.graph_objects as go
from tqdm import tqdm
tqdm.pandas()

def apply_downtrend(df):
    """
    Apply downtrend detection without progress bar intergration
    """
    df['ma_10'] = df.mid_c.rolling(window=10).mean()
    df['ma_50'] = df.mid_c.rolling(window=50).mean()
    df['ma_100'] = df.mid_c.rolling(window=100).mean()
    df['ma_150'] = df.mid_c.rolling(window=150).mean()
    df['in_downtrend'] = (
        (df['ma_10'] < df['ma_50']) &
        (df['ma_50'] < df['ma_100']) &
        (df['ma_100'] < df['ma_150'])
    )
    df.dropna(inplace=True)

