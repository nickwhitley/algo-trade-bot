import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

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

def bullish_strength_with_context(df, index, lookback=200):
    row = df.iloc[index]
    
    open_price = row['mid_o']
    close_price = row['mid_c']
    high = row['mid_h']
    low = row['mid_l']

    # 1. Must be bullish
    if close_price <= open_price:
        return 0.0

    body = close_price - open_price
    total_range = high - low

    #2. Body must make up most of candle
    if body < (total_range * 0.7):
        return 0.0

    # 3. Relative size vs past lookback of candles
    start = max(index - lookback, 0)
    candle_sizes = []
    for i in range(start, index):
        row_i = df.iloc[i]
        body_i = row_i['mid_h'] - row_i['mid_l']
        candle_sizes.append(body_i)

    if not candle_sizes:
        return 0.0

    # Percentile rank of this candle's body size
    candle_avg = np.mean(candle_sizes)
    if body >= candle_avg:
        return 1.0
    else:
        return round((body / candle_avg) * 0.9, 3)

def detect_bottom_reversal_setups(
    df,
    strength_col='bullish_strength_score',
    strength_threshold=0.7,  # Using > 0 for now
    lookahead=25,
    proximity_pips=0.0030,
    rolling_window=40,
    breakout_threshold=20  # in pips
):
    df = df.copy().reset_index(drop=True)
    df['setup_stage'] = None

    # Step 1: Bottom detection
    df['is_bottom'] = (
        (df['mid_l'] == df['mid_l'].rolling(window=rolling_window).min()) &
        (df['in_downtrend'] == True)
    )
    df.loc[df['is_bottom'], 'setup_stage'] = 'bottom'

    # Step 2: Track active zone
    df['active_zone_low'] = None
    df['active_zone_high'] = None

    current_low = None
    current_high = None
    last_bottom_idx = None
    breakout_found = False
    reentry_found = False
    confirmation_found = False

    for i in range(len(df)):
        if df.at[i, 'is_bottom']:
            # New setup: reset everything
            current_low = df.at[i, 'mid_l']
            current_high = df.at[i, 'mid_h']
            last_bottom_idx = i
            breakout_found = False
            reentry_found = False
            confirmation_found = False

        df.at[i, 'active_zone_low'] = current_low
        df.at[i, 'active_zone_high'] = current_high

        # Skip if setup was invalidated
        if current_high is None:
            continue

        max_allowed_low = current_high + breakout_threshold / 10000.0

        # Invalidate if price goes too far from zone
        if breakout_found and df.at[i, 'mid_l'] > max_allowed_low:
            current_low = None
            current_high = None
            last_bottom_idx = None
            breakout_found = False
            reentry_found = False
            confirmation_found = False
            df.at[i, 'active_zone_low'] = None
            df.at[i, 'active_zone_high'] = None
            continue

        # Step 2: Breakout
        if not breakout_found and df.at[i, 'mid_l'] > current_high:
            df.at[i, 'setup_stage'] = 'breakout'
            breakout_found = True
            continue  # Reentry can't be on the breakout candle

        # Step 3: Reentry
        if breakout_found and not reentry_found:
            if current_low <= df.at[i, 'mid_l'] <= current_high:
                df.at[i, 'setup_stage'] = 'reentry'
                reentry_found = True
                continue  # Confirmation must come after reentry

        # Step 4: Confirmation
        if breakout_found and reentry_found and not confirmation_found:
            if df.at[i, strength_col] > strength_threshold:
                df.at[i, 'setup_stage'] = 'confirmation'
                confirmation_found = True

    return df