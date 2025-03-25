import pandas as pd
import datetime as dt
from dateutil import parser
from infrastructure.instrument_collection import InstrumentCollection
from api.oanda_api import OandaApi

CANDLE_COUNT = 3000
INCREMENTS = {
    'M1': 1 * CANDLE_COUNT,
    'M2': 2 * CANDLE_COUNT,
    'M5': 5 * CANDLE_COUNT,
    'M15': 15 * CANDLE_COUNT,
    'M30': 30 * CANDLE_COUNT,
    'H1': 60 * CANDLE_COUNT,
    'H4': 240 * CANDLE_COUNT,
    'D': 1440 * CANDLE_COUNT
}

# saves panda dataframe to pkl file
def save_file(final_df: pd.DataFrame, file_prefix, granularity, pair):
    file_name = f"{file_prefix}{pair}_{granularity}.pkl"

    final_df.drop_duplicates(subset=['time'], inplace=True)
    final_df.sort_values(by='time', inplace=True)
    final_df.reset_index(drop=True, inplace=True)
    final_df.to_pickle(file_name)

# makes call to api and gathers candle data into dataframe
def fetch_candles(pair, granularity, from_date: dt.datetime, to_date: dt.datetime, api: OandaApi):
    fetch_attempts = 0
    candles_df = pd.DataFrame()

    while fetch_attempts < 3:
        candles_df = api.get_candles_df(
            pair,
            granularity=granularity,
            from_date=from_date,
            to_date=to_date
        )

        if candles_df is not None:
            break

        attempts += 1

    if candles_df is not None and candles_df.empty == False:
        return candles_df
    else:
        return None
    
def collect_data(pair, granularity, from_date, to_date, api: OandaApi):
    time_step = INCREMENTS[granularity]
    end_date = parser.parse(to_date)
    from_date = parser.parse(from_date)
    candle_dfs = []
    to_date = from_date
    file_prefix = "./data/"

    while to_date < end_date:
        to_date = from_date + dt.timedelta(minutes=time_step)
        if to_date > end_date:
             to_date = end_date

        candles = fetch_candles(
            pair,
            granularity,
            from_date,
            to_date,
            api
        )

        if candles is not None:
            candle_dfs.append(candles)
            print(f"{pair} {granularity} {from_date} {to_date} --> {candles.shape[0]} candles loaded")
        else:
            print(f"{pair} {granularity} {from_date} {to_date} --> NO CANDLES")

        from_date = to_date

    if len(candle_dfs) > 0:
        final_df = pd.concat(candle_dfs)
        save_file(final_df, file_prefix, granularity, pair)
        print(f"{pair} {granularity} --> DATA SAVED!")
    else:
        print(f"{pair} {granularity} --> NO DATA SAVED!")

def run_collection(ic: InstrumentCollection, api: OandaApi):
    print('running data collection...')
    currencies = ['AUD', 'CAD', 'USD', 'EUR', 'JPY', 'GBP', 'NZD', 'CHF']
    granularities = ['H1', 'H4', 'D']
    from_date = '2024-10-01T00:00:00Z'
    to_date = '2025-03-01T00:00:00Z'

    for c1 in currencies:
        for c2 in currencies:
            pair = f"{c1}_{c2}"
            if pair in ic.instrument_dict.keys():
                for g in granularities:
                    print('running collection for pair...')
                    collect_data(
                        pair,
                        g,
                        from_date,
                        to_date,
                        api
                    )
    
