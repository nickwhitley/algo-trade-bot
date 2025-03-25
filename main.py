from api.oanda_api import OandaApi
from infrastructure.instrument_collection import InstrumentCollection
from infrastructure import data_collection


if __name__ == '__main__':
    api = OandaApi()
    instument_collection = InstrumentCollection(api)
    instument_collection.load_instruments('./data/')
    data_collection.run_collection(instument_collection, api)
    print('finished data collection!!!')
