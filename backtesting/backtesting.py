from infrastructure.instrument_collection import InstrumentCollection
from infrastructure import trade_simulation
from technicals import trend
from technicals import zone
from technicals import pattern
from technicals import bottom
from technicals import candle
import datetime as dt
import pandas as pd
from tqdm import tqdm
import psutil

def run_wirly_dirly_test(pairs, granularities, ic: InstrumentCollection, from_date=None, to_date=None):
    ic.load_instruments("./data")

    config = {
        "sl_pips": 0,
        "tp_to_sl_ratio": 0.5,
        "bottom_zone_lookback": 60,
        "bottom_to_confirmation_spacing": 6,
        "confirmation_wick_ratio": 0.7,
        "exit_threshold": 55,
        "reentry_to_confirm_max_space": 15
    }
    
    from_date = "2020-01-01T00:00:00Z"
    to_date = "2025-01-01T00:00:00Z"

    for p in pairs:
        for g in granularities:
            analyze_pair(p, g, config, from_date, to_date)

def analyze_pair(pair, granularity, config, from_date=None, to_date=None):
    print(f"Analyzing {pair} for {granularity}...")
    df = pd.read_pickle(f"./data/{pair}_{granularity}.pkl")
    if from_date is not None and to_date is not None:
        df = filter_df_by_date(df, from_date, to_date)
    apply_technicals(df, pair)

    pip_divisor = 100 if 'JPY' in pair else 10000
    sl_tp_pips = config['sl_pips'] / pip_divisor
    exit_threshold_pips = config['exit_threshold'] / pip_divisor

    if df is None:
        raise ValueError("DataFrame is None — make sure it's loaded and returned correctly before this point.")
    if df.empty:
        raise ValueError("Filtered DataFrame is empty — check your date range or data source.")

    df['trade'] = None
    df['entry_price'] = None
    df['stop_loss'] = None
    df['take_profit'] = None
    df['pips'] = None

    active_trade = None
    active_bottom_zone_low = None
    active_bottom_zone_high = None
    active_bottom_index = None
    current_stage = None
    reentry_index = None
    exit_threshold_price = None
    trailing_stop_pips = None
    trailing_active = False

    for i in range(len(df)):
        if len(df) >= 100 and i % (len(df) // 100) == 0:
            print(f"Progress: {i}/{len(df)}".ljust(30), end='\r')
        df.loc[i, 'stage'] = current_stage

        if active_trade is None:
            # locate bottom
            if df.loc[i, 'is_bottom'] and df.loc[i, 'in_downtrend']:
                active_bottom_zone_low = df.loc[i, 'mid_l']
                active_bottom_zone_high = df.loc[i, 'mid_h']
                active_bottom_index = i
                current_stage = 'bottom'
                df.loc[i, 'stage'] = current_stage
                continue

            elif df.loc[i, 'is_bottom']:
                active_bottom_zone_low = None
                active_bottom_zone_high = None
                active_bottom_index = None
                current_stage = None
                df.loc[i, 'stage'] = current_stage
                continue

            if current_stage == 'bottom':
                # locate exit
                if df.loc[i, 'mid_l'] > active_bottom_zone_high:
                    current_stage = 'exit'
                    df.loc[i, 'stage'] = current_stage
                    exit_threshold_price = active_bottom_zone_high + exit_threshold_pips
                continue

            if current_stage == 'exit':
                # detect exit threshold breach
                if df.loc[i, 'mid_h'] > exit_threshold_price:
                    active_bottom_zone_low = None
                    active_bottom_zone_high = None
                    active_bottom_index = None
                    current_stage = None
                    exit_threshold_price = None
                    continue

                # detect reentry into zone
                price_within_zone = df.loc[i, 'mid_l'] < active_bottom_zone_high and df.loc[i, 'mid_l'] > active_bottom_zone_low

                if price_within_zone:
                    current_stage = 'reentry'
                    reentry_index = i
                    df.loc[i, 'stage'] = current_stage
                    continue

            if current_stage == 'reentry':
            # detect confirmation candle (entry candle)
                if i > (reentry_index + config['reentry_to_confirm_max_space']):
                    active_bottom_zone_low = None
                    active_bottom_zone_high = None
                    active_bottom_index = None
                    current_stage = None
                    reentry_index = None
                    exit_threshold_price = None
                    continue

                # if df.loc[i, 'mid_l'] > exit_threshold_price:
                #     active_bottom_zone_low = None
                #     active_bottom_zone_high = None
                #     active_bottom_index = None
                #     current_stage = None
                #     reentry_index = None
                #     exit_threshold_price = None
                #     continue

                if df.loc[i, 'strong_bullish'] == True:
                    current_stage = 'confirmation'
                    df.loc[i, 'stage'] = current_stage
                    df.loc[i, 'trade'] = 'opened'
                    entry_price = df.loc[i, 'mid_c']
                    stop_loss = active_bottom_zone_low - sl_tp_pips
                    take_profit = entry_price + ((entry_price - stop_loss) * config['tp_to_sl_ratio'])
                    df.loc[i, 'entry_price'] = entry_price
                    df.loc[i, 'stop_loss'] = stop_loss
                    df.loc[i, 'take_profit'] = take_profit
                    df.loc[i, 'rows_since_bottom'] = i - active_bottom_index
                    df.loc[i, 'bottom_low'] = active_bottom_zone_low
                    active_trade = {
                        'entry_idx': i,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    }

        if active_trade is not None:
            current_stage = 'in_trade'
            df.loc[i, 'stage'] = current_stage

            # SL check — always comes first
            if df.loc[i, 'mid_l'] <= active_trade['stop_loss']:
                df.loc[i, 'trade'] = 'closed - sl'
                df.loc[i, 'pips'] = (active_trade['stop_loss'] - active_trade['entry_price']) * pip_divisor
                df.loc[i, 'rows_since_entry'] = i - active_trade['entry_idx']
                active_trade = None
                active_bottom_zone_low = None
                active_bottom_zone_high = None
                active_bottom_index = None
                current_stage = None
                exit_threshold_price = None
                trailing_active = False
                trailing_stop_pips = None
                df.loc[i, 'stage'] = current_stage
                continue

            # TP check — initialize trailing stop if not active
            if df.loc[i, 'mid_h'] >= active_trade['take_profit']:
                if not trailing_active:
                    trailing_active = True
                    trailing_distance_pips = (active_trade['take_profit'] - active_trade['entry_price']) * pip_divisor
                    df.loc[i, 'stop_loss'] = df.loc[i, 'mid_c'] - (trailing_distance_pips / pip_divisor)
                else:
                    # Trailing stop logic
                    new_stop = df.loc[i, 'mid_c'] - (trailing_distance_pips / pip_divisor)
                    if new_stop > active_trade['stop_loss']:
                        active_trade['stop_loss'] = new_stop
                        df.loc[i, 'stop_loss'] = new_stop

            

    df.reset_index(inplace=True)
    df.to_pickle(f"./backtesting/results/{pair}_{granularity}_analyzed.pkl")
    print(f"{pair} analysis complete.")

def filter_df_by_date(df, start, end):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    return df[(df['time'] >= start) & (df['time'] <= end)].reset_index(drop=True)

def apply_technicals(df, pair):

    df['sTime'] = [dt.datetime.strftime(x, "s%y-%m-%d %H:%M") for x in df.time]
    trend.apply_downtrend(df)
    bottom.apply_bottom_zones(df)
    # zone.apply_zone_exits_and_reentries(df, 50, pair)
    candle.detect_strong_bullish(df)
    # candle.mark_confirmations(df)
