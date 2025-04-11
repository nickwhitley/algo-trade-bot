import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from tqdm import tqdm

# def bullish_strength(row):
#     open_price = row['mid_o']
#     close_price = row['mid_c']
#     high = row['mid_h']
#     low = row['mid_l']
    
#     body = close_price - open_price
#     total_range = high - low
#     upper_wick = high - max(open_price, close_price)
#     lower_wick = min(open_price, close_price) - low
    
#     if total_range == 0:
#         return 0  # avoid division by zero
    
#     # Relative body size (0 to 1)
#     body_score = max(body, 0) / total_range

#     # Wick penalty: 1 is clean (no wicks), 0 is all wicks
#     wick_score = 1 - ((upper_wick + lower_wick) / total_range)

#     # Close near high bonus (closes near the top)
#     close_to_high_score = (high - close_price) / total_range
#     close_to_high_score = 1 - min(close_to_high_score, 1)

#     # Weighted total score
#     total_score = (0.5 * body_score) + (0.3 * wick_score) + (0.2 * close_to_high_score)
    
#     return round(total_score, 3)

def bullish_strength_with_context(df, i, lookback=200):
    if 'bullish_strength_score' not in df.columns:
        df['bullish_strength_score'] = 0.0

    row = df.iloc[i]
    
    open_price = row['mid_o']
    close_price = row['mid_c']
    high = row['mid_h']
    low = row['mid_l']

    if close_price <= open_price:
        return

    body = close_price - open_price
    total_range = high - low

    if body < (total_range * 0.7):
        return

    start = max(i - lookback, 0)
    candle_sizes = [df.iloc[j]['mid_h'] - df.iloc[j]['mid_l'] for j in range(start, i)]

    if not candle_sizes:
        return

    candle_avg = np.mean(candle_sizes)
    if body >= candle_avg:
        df.at[i, 'bullish_strength_score'] = 1.0
    else:
        df.at[i, 'bullish_strength_score'] = round((body / candle_avg) * 0.9, 3)


def detect_bottom_reversal_setups(
    df,
    row,
    pair,
    strength_col='bullish_strength_score',
    strength_threshold=0.7,
    lookahead=25,
    proximity_pips=0.0030,
    rolling_window=40,
    breakout_threshold=20  # in pips
):
    index = row.name  # Assumes `row` is a row from df.iterrows()

    # Ensure required columns exist
    for col in ['setup_stage', 'is_bottom', 'active_zone_low', 'active_zone_high']:
        if col not in df.columns:
            df[col] = None

    # Step 1: Bottom detection (on-the-fly)
    if (
        row['mid_l'] == df['mid_l'].iloc[max(index - rolling_window, 0):index + 1].min()
        and row['in_downtrend']
    ):
        df.at[index, 'setup_stage'] = 'bottom'
        df.at[index, 'is_bottom'] = True
        df.at[index, 'active_zone_low'] = row['mid_l']
        df.at[index, 'active_zone_high'] = row['mid_h']
        return  # We reset the setup here, wait for future rows to trigger breakout

    # Grab the most recent zone (based on active values or setup_stage == 'bottom')
    subset = df.loc[:index].iloc[::-1]
    active_zone_row = subset[subset['setup_stage'] == 'bottom'].head(1)

    if active_zone_row.empty:
        return  # No active setup

    zone_low = active_zone_row['mid_l'].values[0]
    zone_high = active_zone_row['mid_h'].values[0]
    zone_index = active_zone_row.index[0]

    # Store the zone for current row
    df.at[index, 'active_zone_low'] = zone_low
    df.at[index, 'active_zone_high'] = zone_high

    # Invalidate setup if price strays too far
    max_allowed_low = zone_high + breakout_threshold / (100 if 'JPY' in pair else 10000)
    if row['mid_l'] > max_allowed_low:
        return  # Setup invalidated, do nothing

    # Step 2: Breakout
    if (
        'breakout' not in df.loc[zone_index:index, 'setup_stage'].values
        and row['mid_l'] > zone_high
    ):
        df.at[index, 'setup_stage'] = 'breakout'
        return

    # Step 3: Reentry
    if (
        'breakout' in df.loc[zone_index:index, 'setup_stage'].values
        and 'reentry' not in df.loc[zone_index:index, 'setup_stage'].values
        and zone_low <= row['mid_l'] <= zone_high
    ):
        df.at[index, 'setup_stage'] = 'reentry'
        return

    # Step 4: Confirmation
    if (
        'reentry' in df.loc[zone_index:index, 'setup_stage'].values
        and row[strength_col] > strength_threshold
    ):
        df.at[index, 'setup_stage'] = 'confirmation'