
import pandas as pd
import datetime as dt
from technicals import trend
from technicals import zone
from technicals import pattern
from technicals import bottom
from technicals import candle

def apply_technicals(df, pair):

    df['sTime'] = [dt.datetime.strftime(x, "s%y-%m-%d %H:%M") for x in df.time]
    trend.apply_downtrend(df)
    bottom.apply_bottom_zones(df)
    zone.apply_zone_exits_and_reentries(df, 50, pair)
    candle.detect_strong_bullish(df)

def analyze_pair(pair, granularity, config):
    print(f"Analyzing {pair} for {granularity}...")
    df = pd.read_pickle(f"./data/{pair}_{granularity}.pkl")
    apply_technicals(df, pair)

    pip_divisor = 100 if 'JPY' in pair else 10000
    pip_size = config['sl_pips'] / pip_divisor

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

    for i in range(len(df)):
        row = df.iloc[i]

        # Check for new confirmation candle to enter trade
        if row['setup_stage'] == 'confirmation':
            zone = row.get('zone')
            if not isinstance(zone, tuple) or len(zone) != 2:
                continue

            zone_low = zone[0]
            entry_price = row['mid_c']
            stop_loss = zone_low - pip_size
            take_profit = entry_price + ((entry_price - stop_loss) * config['tp_to_sl_ratio'])

            active_trade = {
                'entry_idx': i,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }

            df.at[df.index[i], 'trade'] = 'opened'
            df.at[df.index[i], 'entry_price'] = entry_price
            df.at[df.index[i], 'stop_loss'] = stop_loss
            df.at[df.index[i], 'take_profit'] = take_profit
            continue

        # If trade is active, check for SL/TP hit
        if active_trade:
            high = row['mid_h']
            low = row['mid_l']
            idx = df.index[i]

            if low <= active_trade['stop_loss']:
                df.at[idx, 'trade'] = 'closed - sl'
                df.at[idx, 'pips'] = round((active_trade['stop_loss'] - active_trade['entry_price']) / (1 / pip_divisor), 1)
                active_trade = None
            elif high >= active_trade['take_profit']:
                df.at[idx, 'trade'] = 'closed - tp'
                df.at[idx, 'pips'] = round((active_trade['take_profit'] - active_trade['entry_price']) / (1 / pip_divisor), 1)
                active_trade = None

    df.to_pickle(f"./backtesting/results/{pair}_{granularity}_analyzed.pkl")
    print(f"{pair} analysis complete.")