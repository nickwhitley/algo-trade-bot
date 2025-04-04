import pandas as pd
import plotly.graph_objects as go
from tqdm import tqdm
tqdm.pandas()

def detect_downtrend(row):
    return row['ma_10'] < row['ma_150']

def apply_downtrend(df):
    df['ma_10'] = df.mid_c.rolling(window=10).mean()
    df['ma_150'] = df.mid_c.rolling(window=150).mean()
    df.dropna(inplace=True)

    # Use tqdm's progress bar here
    df['in_downtrend'] = df.progress_apply(detect_downtrend, axis=1)

def highlight_downtrend_candles(df):
    fig = go.Figure()
    df_downtrend = df[df['in_downtrend'] == True]

    fig.add_trace(go.Candlestick(
        x=df.sTime,
        open=df.mid_o,
        high=df.mid_h,
        low=df.mid_l,
        close=df.mid_c,
        line=dict(width=1), opacity=1,
        increasing_fillcolor='#24A06B', 
        decreasing_fillcolor='#CC2E3C',
        increasing_line_color='#24A06B',
        decreasing_line_color='#FF3A4C'
    ))

    fig.add_trace(go.Candlestick(
        x=df_downtrend.sTime,
        open=df_downtrend.mid_o,
        high=df_downtrend.mid_h,
        low=df_downtrend.mid_l,
        close=df_downtrend.mid_c,
        line=dict(width=1), opacity=1,
        increasing_fillcolor='blue', 
        decreasing_fillcolor='blue',
        increasing_line_color='blue',
        decreasing_line_color='blue'
    ))

    fig.update_yaxes(
        gridcolor="#1f292f"
    )

    fig.update_xaxes(
        gridcolor="#1f292f",
        rangeslider=dict(visible=True),
        nticks=5
    )

    fig.update_layout(
        width=1200,
        height=600,
        margin=dict(l=10,r=10,b=10,t=10),
        paper_bgcolor="#2c303c",
        plot_bgcolor="#2c303c",
        font=dict(size=10, color="#e1e1e1")
    )

    return fig