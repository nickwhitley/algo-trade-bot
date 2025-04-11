from infrastructure.instrument_collection import InstrumentCollection
from technicals import trend
from technicals import zone
from technicals import pattern
import datetime as dt
import pandas as pd
from tqdm import tqdm
import psutil

def run_wirly_dirly_test(pairs, granularities, ic: InstrumentCollection, from_date=None, to_date=None):
    ic.load_instruments("./data")

    for p in pairs:
        for g in granularities:
            analyze_pair(p, g)

def analyze_pair(pair, granularity):
    print(f"Analyzing {pair} for {granularity}...")
    df = pd.read_pickle(f"./data/{pair}_{granularity}.pkl")
    df = apply_technicals(df, pair)

    df['trade'] = None
    df['pips'] = None

    active_trade = None
    pip_size = 0.01 if pair == 'USD_JPY' else 0.0001

    for i in tqdm(range(len(df)), desc=f"Analyzing {pair}"):
        row = df.iloc[i]

        if active_trade:
            price = row['mid_c']
            high = row['mid_h']
            low = row['mid_l']

            # Check for SL hit
            if low <= active_trade['stop_loss']:
                df.at[i, 'trade'] = 'closed - sl hit'
                pnl = (active_trade['stop_loss'] - active_trade['entry_price']) / pip_size
                df.at[i, 'pips'] = round(pnl, 1)
                active_trade = None
                continue

            # Check for TP hit
            if high >= active_trade['take_profit']:
                df.at[i, 'trade'] = 'closed - tp hit'
                pnl = (active_trade['take_profit'] - active_trade['entry_price']) / pip_size
                df.at[i, 'pips'] = round(pnl, 1)
                active_trade = None
                continue

            # Price enters Zone 2
            z2_low, z2_high = active_trade['zones'][1]
            if z2_low <= low <= z2_high and active_trade['stage'] == 'initial':
                active_trade['stop_loss'] = active_trade['entry_price']  # move SL to breakeven
                active_trade['take_profit'] = active_trade['zones'][2][0]  # move TP to bottom of zone 3
                active_trade['stage'] = 'breakeven'
                df.at[i, 'trade'] = 'sl to breakeven'

            # Price moves above zone 2 top
            elif high > z2_high and active_trade['stage'] == 'breakeven':
                active_trade['stop_loss'] = z2_low  # SL to bottom of zone 2
                active_trade['take_profit'] = active_trade['zones'][2][1]  # TP to top of zone 3
                active_trade['stage'] = 'zone 2 breakout'
                df.at[i, 'trade'] = 'sl to zone 2 bottom'

            # Price enters zone 3 — begin trailing
            elif active_trade['stage'] == 'zone 2 breakout':
                z3_low, z3_high = active_trade['zones'][2]
                if z3_low <= low <= z3_high:
                    # Trail SL from z2 high upward (fixed trail distance, say 10 pips)
                    trail_buffer = 0.0010  # 10 pips
                    new_sl = max(active_trade['stop_loss'], high - trail_buffer)
                    if new_sl > active_trade['stop_loss']:
                        active_trade['stop_loss'] = new_sl
                        df.at[i, 'trade'] = 'sl trail from zone 2 top'

        # No active trade — look for confirmation entry
        if not active_trade and row['setup_stage'] == 'confirmation' and row['meets_ratio'] == True:
            if row['confirmation_zones'] and len(row['confirmation_zones']) >= 3:
                # Find bottom candle to get stop
                bottom_idx = df.index[:i][df['setup_stage'][:i] == 'bottom'].max()
                bottom_candle = df.loc[bottom_idx]
                stop_loss = bottom_candle['mid_l'] - 0.0005  # 5 pips below

                entry_price = row['ask_c']
                take_profit = row['confirmation_zones'][1][1]  # top of zone 2

                active_trade = {
                    'entry_idx': i,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'stage': 'initial',
                    'zones': row['confirmation_zones'],
                }

                df.at[i, 'trade'] = 'opened'

    # Optionally save or return df
    df.to_pickle(f"./backtesting/results/{pair}_{granularity}_analyzed.pkl")
    tqdm.write(f"{pair} analysis complete.")

def apply_technicals(df, pair):
    trend.apply_downtrend(df)
    

    progress = tqdm(range(len(df)), desc="Applying technicals")

    for i in progress:
        trend.apply_downtrend(df, i)
        pattern.bullish_strength_with_context(df, i)
        pattern.detect_bottom_reversal_setups(df, df.iloc[i], pair)
        zone.attach_zones_to_confirmations(df, i)

        # ✅ Update CPU + MEM only every 1000 iterations or on the last
        if i % 1000 == 0 or i == len(df) - 1:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory().percent
            progress.set_postfix(cpu=f"{cpu:.1f}%", mem=f"{mem:.1f}%")

    return df
