import requests
import pandas as pd
import time
import os

# Load settings from the project-root config.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXCHANGES, API_KEYS, ML_PAIRS as PAIRS, DATA_START, DATA_END

# CryptoCompare API base URL
BASE_URL = "https://min-api.cryptocompare.com/data/v2/histominute"

# Time range from config.py (UTC, aligned with IST 2025-10-20 19:28:00 to 2025-10-25 15:12:00)
start_time = int(pd.Timestamp(DATA_START).timestamp())
end_time = int(pd.Timestamp(DATA_END).timestamp())

# Mapping of pairs to CryptoCompare symbols and exchanges
coin_mapping = {
    'BTC/USDT': {'fsym': 'BTC', 'tsym': 'USD', 'e': 'CCCAGG'},  # Aggregated
    'ETH/USDT': {'fsym': 'ETH', 'tsym': 'USD', 'e': 'CCCAGG'}
}

# Fetch data for each pair
for pair in PAIRS:
    all_ohlcv = []
    current_time = start_time

    print(f"Fetching {pair} from CryptoCompare...")
    while current_time < end_time:
        try:
            params = {
                'fsym': coin_mapping[pair]['fsym'],
                'tsym': coin_mapping[pair]['tsym'],
                'e': coin_mapping[pair]['e'],
                'limit': 2000,  # Max per call
                'toTs': current_time + 2000 * 60,  # 2000 minutes from current_time
                'api_key': API_KEYS['cryptocompare']
            }
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            histo = data.get('Data', {}).get('Data', [])
            if histo:
                df = pd.DataFrame(histo)
                df['timestamp'] = pd.to_datetime(df['time'], unit='s')
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volumeto']].rename(columns={'volumeto': 'volume'})
                print(f"Raw data sample: {df.head()}")

                # Filter to exact static range
                df = df[(df['timestamp'] >= pd.Timestamp(DATA_START)) & 
                        (df['timestamp'] <= pd.Timestamp(DATA_END))]
                all_ohlcv.extend([[int(t.timestamp.value / 10**6), t.open, t.high, t.low, t.close, t.volume] for t in df.itertuples()])

                current_time = int(df['timestamp'].iloc[-1].timestamp()) + 60  # Move to next minute
                print(f"Fetched batch: {len(df)} rows, new since: {pd.to_datetime(current_time * 1000, unit='ms')}")
            else:
                print(f"No more data at timestamp: {pd.to_datetime(current_time * 1000, unit='ms')}")
                break
            time.sleep(1)  # Respect rate limits
        except requests.exceptions.RequestException as e:
            print(f"Error for {pair} from CryptoCompare: {e}")
            break
        except Exception as e:
            print(f"Unexpected error for {pair} from CryptoCompare: {e}")
            break

    if all_ohlcv:
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['exchange'] = 'cryptocompare'
        df['pair'] = pair
        output_file = f'data/cryptocompare_{pair.replace("/", "_")}.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved {len(df)} rows for {pair} from CryptoCompare to {output_file}")
    else:
        print(f"No data for {pair} from CryptoCompare")