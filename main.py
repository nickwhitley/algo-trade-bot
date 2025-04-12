from api.oanda_api import OandaApi
from infrastructure.instrument_collection import InstrumentCollection
from infrastructure import data_collection
from backtesting import backtesting
import datetime



if __name__ == '__main__':
    start = datetime.datetime.now()
    print(f"🚀 Start Time: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    
    api = OandaApi()
    instument_collection = InstrumentCollection(api)
    pairs = ["AUD_USD", "EUR_USD", "GBP_USD", "USD_CHF", "USD_JPY", "NZD_USD", "USD_CAD"]
    granularities = ['M5', 'M30', 'H1', 'H4']

    instument_collection.load_instruments('./data')
    # data_collection.run_collection(instument_collection, api, granularities)
    backtesting.run_wirly_dirly_test(pairs, granularities, instument_collection)

    end = datetime.datetime.now()
    duration = end - start
    print(f"✅ End Time: {end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ Duration: {str(duration)}")

