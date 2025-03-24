import json
from models.instrument import Instrument

class InstrumentCollection:
    FILENAME = 'instruments.json'
    API_KEYS = ['name', 'type', 'displayName', 'pipLocation', 'displayPrecision', 'tradeUnitsPrecision', 'marginRate']

    def __init__(self):
        self.instrument_dict = {}

    def load_instruments(self, path):
        