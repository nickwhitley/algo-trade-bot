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

def get_zones_for_price(price, support_levels, resistance_levels, num_of_zones=3, min_gap=0.0, min_width=0.0015):
    """
    Returns non-overlapping (support, resistance) zones where the support is above the given price,
    and there's at least `min_gap` space and `min_width` size.

    Args:
        price (float): Current price.
        support_levels (list of float): Detected support levels.
        resistance_levels (list of float): Detected resistance levels.
        num_of_zones (int): Number of zones to return.
        min_gap (float): Minimum gap between zones.
        min_width (float): Minimum acceptable width of a zone.

    Returns:
        List of tuples: [(support1, resistance1), (support2, resistance2), ...]
    """

    support_levels = sorted(support_levels)
    resistance_levels = sorted(resistance_levels)

    zones = []
    last_resistance = price

    sup_above = [s for s in support_levels if s > price]

    for support in sup_above:
        if support <= last_resistance + min_gap:
            continue

        possible_resistances = [r for r in resistance_levels if r > support]
        for resistance in possible_resistances:
            width = resistance - support
            if width >= min_width:
                zones.append((support, resistance))
                last_resistance = resistance
                break  # Move on to the next zone

        if len(zones) == num_of_zones:
            break

    return zones

def attach_zones_to_confirmations(
    df,
    window=3,
    clustering_threshold=0.0050,
    num_of_zones=3
):
    """
    For each confirmation candle:
        - Attach relevant support/resistance zones based on past data only
        - Compute zone-to-stop-loss ratio using second zone
        - Add 'confirmation_zones', 'zone_sl_ratio', and 'meets_ratio' columns
    """
    from copy import deepcopy
    df['confirmation_zones'] = None
    df['zone_sl_ratio'] = None
    df['meets_ratio'] = False

    for i in range(len(df)):
        if df.at[i, 'setup_stage'] == 'confirmation':
            past_df = df.iloc[:i]
            if len(past_df) < window * 2:
                continue

            support_levels, resistance_levels = find_support_resistance(
                past_df,
                price_col='mid_c',
                high_col='mid_h',
                low_col='mid_l',
                window=window,
                clustering_threshold=clustering_threshold
            )

            current_price = df.at[i, 'mid_c']
            current_low = df.at[i, 'mid_l']

            zones = get_zones_for_price(
                price=current_price,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                num_of_zones=num_of_zones
            )

            df.at[i, 'confirmation_zones'] = deepcopy(zones)

            if len(zones) >= 2:
                zone_top = zones[1][1]  # Top of second zone (resistance)
                reward = zone_top - current_price
                risk = current_price - current_low

                if risk > 0:
                    ratio = reward / risk
                    df.at[i, 'zone_sl_ratio'] = round(ratio, 3)
                    df.at[i, 'meets_ratio'] = ratio >= 1.0


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