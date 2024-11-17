from datetime import datetime, timezone
import pandas as pd
import requests
from typing import *
import time

class BinanceClient:
    def __init__(self, futures=False):
        self.exchange = "BINANCE"
        self.futures = futures

        if self.futures:
            self._base_url = "https://fapi.binance.com"
        else:
            self._base_url = "https://api.binance.com"

        self.symbols = self._get_symbols()

    def _make_request(self, endpoint: str, query_parameters: Dict):
        try:
            response = requests.get(self._base_url + endpoint, params=query_parameters)
        except Exception as e:
            print("Connection error while making request to %s: %s", endpoint, e)
            return None

        if response.status_code == 200:
            return response.json()
        else:
            print("Error while making request to %s: %s (status code = %s)",
                         endpoint, response.json(), response.status_code)
            return None

    def _get_symbols(self) -> List[str]:

        params = dict()

        endpoint = "/fapi/v1/exchangeInfo" if self.futures else "/api/v3/exchangeInfo"
        data = self._make_request(endpoint, params)

        symbols = [x["symbol"] for x in data["symbols"]]

        return symbols

    def get_historical_data(self, symbol: str, interval: Optional[str] = "1m", start_time: Optional[int] = None, end_time: Optional[int] = None, limit: Optional[int] = 1500):

        params = dict()

        params["symbol"] = symbol
        params["interval"] = interval
        params["limit"] = limit

        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        endpoint = "/fapi/v1/klines" if self.futures else "/api/v3/klines"
        raw_candles = self._make_request(endpoint, params)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append((float(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5]),))
            return candles
        else:
            return None

def ms_to_dt_utc(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

def ms_to_dt_local(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000)

def save_dataframe_to_csv(df, file_name):
    df.to_csv(file_name, mode='a', index=False, header=not pd.io.common.file_exists(file_name))

def GetDataFrame(data):
    df = pd.DataFrame(data, columns=['Timestamp', "Open", "High", "Low", "Close", "Volume"])
    df["Timestamp"] = df["Timestamp"].apply(lambda x: ms_to_dt_utc(x))
    df["Timestamp"] = df["Timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S")
    return df

def GetHistoricalData(client, symbol, start_time, end_time, file_name, interval, limit=1500):

    while start_time < end_time:
        data = client.get_historical_data(symbol, interval=interval, start_time=start_time, end_time=end_time, limit=limit)
        print(client.exchange + " " + symbol + " : Collected " + str(len(data)) + " initial data from "+ str(ms_to_dt_local(data[0][0])) +" to " + str(ms_to_dt_local(data[-1][0])))
        start_time = int(data[-1][0] + 1000)
        df = GetDataFrame(data)
        save_dataframe_to_csv(df, file_name)
    print('Done !')

client = BinanceClient(futures=False)
symbol = "ETHUSDT"
interval = "1s"
start_year, start_month, start_day = 2022, 10, 1
end_year, end_month, end_day = 2022, 11, 15
fromDate = int(datetime.strptime(f"{start_year}-{start_month}-{start_day}", '%Y-%m-%d').timestamp() * 1000)
toDate = int(datetime.strptime(f"{end_year}-{end_month}-{end_day}", '%Y-%m-%d').timestamp() * 1000)
file_name = f'./../Binance_data_{symbol}_{start_year}_{start_month}_{start_day}_to_{end_year}_{end_month}_{end_day}.csv'
GetHistoricalData(client, symbol, fromDate, toDate, file_name, interval)
