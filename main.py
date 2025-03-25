from api.oanda_api import OandaApi
from infrastructure.instrument_collection import InstrumentCollection
from infrastructure import run_collection


if __name__ == '__main__':
    instument_collection = InstrumentCollection()
    api = OandaApi()
    
