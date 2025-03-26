from infrastructure.instrument_collection import InstrumentCollection
from technicals import trend_checker
from technicals import zone_detector
from technicals import pattern_detector
import datetime as dt
import pandas as pd

def run_wirly_dirly_test(pairs, granularities, ic: InstrumentCollection, from_date=None, to_date=None):
    ic.load_instruments("./data")

    for p in pairs:
        for g in granularities:
            analyze_pair(p, g)

    # apply detectors
    # enter trade
    # set stop loss and take profit
        # stop loss is within 3 pips beneath bottom of entry zone
        # take profit is at the top of second zone
    # change stop loss to breakeven when price enters first zone
    # change stop loss to bottom of second zone when price hits top of second zone
    # change stop loss to trail when price hits third zone starting at top of second zone

def analyze_pair(pair, granularity):
    df = pd.read_pickle(f"./data/{pair}_{granularity}.pkl")
    df = apply_technicals(df)

def apply_technicals(df):
    df['sTime'] = [dt.datetime.strftime(x, "s%y-%m-%d %H:%M") for x in df.time]
    trend_checker.apply_downtrend(df) 
    #need to make this not return a df but add in place
    df = pattern_detector.detect_bottom_reversal_setups(df)
    zone_detector.attach_zones_to_confirmations(df)
