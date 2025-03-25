import json
import os
from models.instrument import Instrument
from api.oanda_api import OandaApi

class InstrumentCollection:
    FILENAME = 'instruments.json'
    API_KEYS = ['name', 'type', 'displayName', 'pipLocation', 'displayPrecision', 'tradeUnitsPrecision', 'marginRate']

    def __init__(self, api: OandaApi):
        self.instrument_dict = {}
        self.api = api

    def load_instruments(self, path):
        self.instrument_dict = {}
        file_name = f"{path}/{self.FILENAME}"

        if not os.path.exists(file_name):
            ins_data = self.api.get_account_instruments()
            self.create_file(ins_data, path)

        with open(file_name, 'r') as f:
            data = json.loads(f.read())
            for k, v in data.items():
                self.instrument_dict[k] = Instrument.from_api_object(v)

    def create_file(self, data, path):
        if data is None:
            print("Instrument file creation failed, data is nil.")
            return
        
        instruments_dict = {}
        for i in data:
            key = i['name']
            instruments_dict[key] = {k: i[k] for k in self.API_KEYS}

        file_name = f"{path}/{self.FILENAME}"
        with open(file_name, 'w') as f:
            f.write(json.dumps(instruments_dict, indent=2))

    def print_instrument(self):
        [print(k, v) for k, v in self.instrument_dict.items()]
        print(len(self.instrument_dict.keys()), 'instruments')
