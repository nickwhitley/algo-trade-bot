import requests
import constants
import pandas as pd
from dateutil import parser
from datetime import datetime as dt

class OandaApi:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {constants.API_KEY}",
                "Content-Type": "application/json"
            }
        )

    def make_request(self, url, verb='get', code=200, params=None, data=None, headers=None):
        full_url = f"{constants.OANDA_URL}/{url}"
        try:
            response = None
            if verb == 'get':
                response = self.session.get(full_url, params=params, data=data, headers=headers)
            if response == None:
                raise Exception('Response was none')
            if response.status_code == code:
                return True, response.json()
            else:
                return False, response.json()
        except Exception as ex:
            return False, {'Exception': ex}
        
    def get_account_ep(self, ep, data_key):
        url = f"accounts/{constants.ACCOUNT_ID}/{ep}"
        ok, data = self.make_request(url)
        if ok == True and data_key in data:
            return data[data_key]
        else:
            print('*** ERROR get_account_ep()', data)
            return None
        
    def get_account_summary(self):
        return self.get_account_ep('summary', 'account')
    
    def get_account_instruments(self):
        return self.get_account_ep('instruments', 'instruments')
    
    def fetch_candles(self, pair_name, count=10, granularity='H4', price='MBA', from_date=None, to_date=None):
        url = f"instruments/{pair_name}/candles"
        params = dict(
            granularity=granularity,
            price=price
        )

        if from_date is not None and to_date is not None:
            date_format = '%Y-%m-%dT%H:%M:%SZ'
            params['from'] = dt.strftime(from_date, date_format)
            params['to'] = dt.strftime(to_date, date_format)
        else:
            params['count'] = count

        ok, data = self.make_request(url, params=params)
        if ok == True and 'candles' in data:
            return data['candles']
        else:
            print('*** ERROR fetch_candles()', params, data)
            return None
        
    def get_candles_df(self, pair_name, **kwargs):
        data = self.fetch_candles(pair_name, **kwargs)
        if data is None or len(data) == 0:
            return pd.DataFrame()
        prices = ['mid', 'bid', 'ask']
        ohlc = ['o', 'h', 'l', 'c']
        final_data = []
        for candle in data:
            if not candle['complete']:
                continue
            new_dict = {'time': parser.parse(candle['time']), 'volume': candle['volume']}
            for p in prices:
                if p in candle:
                    for o in ohlc:
                        new_dict[f"{p}_{o}"] = float(candle[p][o])
            final_data.append(new_dict)
        df = pd.DataFrame.from_dict(final_data)
        return df