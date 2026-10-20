import ccxt
import pandas as pd
import time
import os

# Load settings from the project-root config.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXCHANGES, API_KEYS, ML_PAIRS as PAIRS, DATA_START, DATA_END

# Initialize Coinbase with API key
exchange = ccxt.coinbase({
    'enableRateLimit': True,
    'apiKey': EXCHANGES['coinbase']['apiKey'],
    'secret': EXCHANGES['coinbase']['secret']
})
limit = 200  # Adjusted limit for Coinbase

# Time range from config.py (naive UTC, aligned with IST 2025-10-20 19:28:00 to 2025-10-25 15:12:00)
start_time = int(pd.Timestamp(DATA_START).timestamp() * 1000)  # 2025-10-20 19:28:00 IST in UTC
end_time = int(pd.Timestamp(DATA_END).timestamp() * 1000)    # 2025-10-25 15:12:00 IST in UTC

# Fetch paginated data for each pair
for pair in ['BTC-USD', 'ETH-USD']:  # Coinbase uses hyphen format
    all_ohlcv = []
    last_timestamp = start_time

    print(f"Fetching {pair} from Coinbase (paginated with API)...")
    while last_timestamp < end_time:
        try:
            print(f"Attempting fetch with since: {last_timestamp}")  # Debug the since value
            ohlcv = exchange.fetch_ohlcv(pair, '1m', since=last_timestamp, limit=limit)
            if ohlcv and len(ohlcv) > 0:
                all_ohlcv.extend(ohlcv)
                last_timestamp = ohlcv[-1][0] + 1
                print(f"Fetched batch: {len(ohlcv)} rows, new since: {pd.to_datetime(last_timestamp, unit='ms')}")
            else:
                print(f"No more data at timestamp: {pd.to_datetime(last_timestamp, unit='ms')}")
                break
            time.sleep(2)
        except Exception as e:
            print(f"Error for {pair} from Coinbase: {e}")
            break

    if all_ohlcv:
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        # Filter to exact static range (naive UTC)
        df = df[(df['timestamp'] >= pd.Timestamp(DATA_START)) & 
                (df['timestamp'] <= pd.Timestamp(DATA_END))]
        df['exchange'] = 'coinbase'
        df['pair'] = pair.replace('-', '/')
        output_file = f'data/coinbase_{pair.replace("-", "_")}.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved {len(df)} rows for {pair} from Coinbase to {output_file}")
    else:
        print(f"No data for {pair} from Coinbase")