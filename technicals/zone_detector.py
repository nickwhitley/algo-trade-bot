import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import plotly.graph_objects as go

def find_support_resistance(df, price_col='mid_c', high_col='mid_h', low_col='mid_l', window=3, clustering_threshold=0.0050):
    """
    Identifies support and resistance levels in candlestick data.
    
    Args:
        df (pd.DataFrame): Your OHLC dataframe.
        price_col (str): Column name for close/mid price.
        high_col (str): Column name for highs.
        low_col (str): Column name for lows.
        window (int): Lookback window to detect local highs/lows.
        clustering_threshold (float): Maximum distance between levels to consider them the same zone.

    Returns:
        Tuple[List[float], List[float]]: (support_levels, resistance_levels)
    """
    
    # Find local minima and maxima
    local_min_idx = argrelextrema(df[low_col].values, np.less_equal, order=window)[0]
    local_max_idx = argrelextrema(df[high_col].values, np.greater_equal, order=window)[0]

    raw_supports = df.iloc[local_min_idx][low_col].values
    raw_resistances = df.iloc[local_max_idx][high_col].values

    def cluster_levels(levels):
        clustered = []
        levels = sorted(levels)
        for level in levels:
            if not clustered:
                clustered.append([level])
            elif abs(level - np.mean(clustered[-1])) <= clustering_threshold:
                clustered[-1].append(level)
            else:
                clustered.append([level])
        return [round(np.mean(group), 5) for group in clustered if len(group) >= 2]  # Only return stronger levels

    support_levels = cluster_levels(raw_supports)
    resistance_levels = cluster_levels(raw_resistances)

    return support_levels, resistance_levels

def plot_candles_with_levels(fig, df, support_levels, resistance_levels,
                              time_col='time', open_col='mid_o', high_col='mid_h',
                              low_col='mid_l', close_col='mid_c'):
    """
    Plots a candlestick chart with support and resistance levels.

    Args:
        df (pd.DataFrame): Your OHLC dataframe.
        support_levels (list): List of support price levels.
        resistance_levels (list): List of resistance price levels.
        time_col, open_col, high_col, low_col, close_col: Column names for OHLC data.

    Returns:
        fig (plotly.graph_objects.Figure): Candlestick chart with levels.
    """

    # Plot support levels
    for level in support_levels:
        fig.add_trace(go.Scatter(
            x=[df[time_col].iloc[0], df[time_col].iloc[-1]],
            y=[level, level],
            mode='lines',
            name=f'Support {level}',
            line=dict(color='green', width=1.5, dash='dash')
        ))

    # Plot resistance levels
    for level in resistance_levels:
        fig.add_trace(go.Scatter(
            x=[df[time_col].iloc[0], df[time_col].iloc[-1]],
            y=[level, level],
            mode='lines',
            name=f'Resistance {level}',
            line=dict(color='red', width=1.5, dash='dot')
        ))

    fig.update_layout(
        title='Candlestick Chart with Support & Resistance',
        xaxis_title='Time',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        template='plotly_white'
    )

    return fig