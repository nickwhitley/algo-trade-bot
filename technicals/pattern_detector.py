import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

def bullish_strength(row):
    open_price = row['mid_o']
    close_price = row['mid_c']
    high = row['mid_h']
    low = row['mid_l']
    
    body = close_price - open_price
    total_range = high - low
    upper_wick = high - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low
    
    if total_range == 0:
        return 0  # avoid division by zero
    
    # Relative body size (0 to 1)
    body_score = max(body, 0) / total_range

    # Wick penalty: 1 is clean (no wicks), 0 is all wicks
    wick_score = 1 - ((upper_wick + lower_wick) / total_range)

    # Close near high bonus (closes near the top)
    close_to_high_score = (high - close_price) / total_range
    close_to_high_score = 1 - min(close_to_high_score, 1)

    # Weighted total score
    total_score = (0.5 * body_score) + (0.3 * wick_score) + (0.2 * close_to_high_score)
    
    return round(total_score, 3)

def detect_bottom_reversal_setups(
    df,
    strength_col='bullish_strength_score',
    strength_threshold=0.5,
    lookahead=35,
    proximity_pips=0.0050,
    rolling_window=25
):
    """
    Detects bottom reversal setups using new lows that occur only during downtrends.

    A setup is:
    1. A bottom candle (lowest in a window, while in_downtrend is True)
    2. A breakout candle (low + high > zone high)
    3. A reentry candle (low reenters the zone but never breaks below zone low)
    4. A strong bullish candle (close near zone high and strength score high)

    Returns:
        DataFrame with setup_stage column added.
    """
    df = df.copy().reset_index(drop=True)
    df['setup_stage'] = None

    # Step 1: Find valid bottom candles (new lows during in_downtrend)
    df['is_bottom'] = (
        (df['mid_l'] == df['mid_l'].rolling(window=rolling_window, min_periods=1).min()) &
        (df['in_downtrend'] == True)
    )
    bottom_indexes = df.index[df['is_bottom']].tolist()

    active_zone_low = None
    active_zone_high = None
    active_bottom_idx = None

    for i in bottom_indexes:
        bottom_candle = df.iloc[i]
        new_zone_low = bottom_candle['mid_l']
        new_zone_high = bottom_candle['mid_h']

        # Invalidate any existing setup if this low is lower than prior zone
        if active_zone_low is not None and new_zone_low < active_zone_low:
            active_zone_low = None
            active_zone_high = None
            active_bottom_idx = None

        # Start tracking new potential setup
        active_zone_low = new_zone_low
        active_zone_high = new_zone_high
        active_bottom_idx = i

        # Step 2: Look for valid breakout (entire candle above zone)
        breakout_idx = None
        for j in range(i + 1, len(df)):
            row_j = df.iloc[j]
            if row_j['mid_l'] < active_zone_low:
                break  # setup invalidated
            if row_j['mid_l'] > active_zone_high and row_j['mid_h'] > active_zone_high:
                breakout_idx = j
                break

        if breakout_idx is None or breakout_idx - i > lookahead:
            continue

        # Step 3: Reentry into zone without breaking below zone low
        reentry_idx = None
        for k in range(breakout_idx + 1, breakout_idx + lookahead):
            if k >= len(df):
                break
            row_k = df.iloc[k]
            if active_zone_low <= row_k['mid_l'] <= active_zone_high:
                reentry_idx = k
                break
            if row_k['mid_l'] < active_zone_low:
                break  # reentry invalidated

        if reentry_idx is None:
            continue

        # Step 4: Strong bullish confirmation near the zone
        confirmation_found = False
        for m in range(reentry_idx + 1, reentry_idx + lookahead):
            if m >= len(df):
                break
            row_m = df.iloc[m]
            if row_m['mid_l'] < active_zone_low:
                break  # invalidated
            if row_m[strength_col] >= strength_threshold:
                if abs(row_m['mid_c'] - active_zone_high) <= proximity_pips:
                    # Tag each stage
                    df.at[active_bottom_idx, 'setup_stage'] = 'bottom'
                    df.at[breakout_idx, 'setup_stage'] = 'breakout'
                    df.at[reentry_idx, 'setup_stage'] = 'reentry'
                    df.at[m, 'setup_stage'] = 'confirmation'
                    confirmation_found = True
                    break

        if confirmation_found:
            active_zone_low = None
            active_zone_high = None
            active_bottom_idx = None

    return df