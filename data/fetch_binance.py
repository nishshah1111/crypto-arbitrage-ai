import ccxt
import pandas as pd
import time
import os

# Load settings from the project-root config.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXCHANGES, API_KEYS, ML_PAIRS as PAIRS, DATA_START, DATA_END

# Initialize Binance with API key (optional)
exchange = ccxt.binance({
    'enableRateLimit': True,
    'apiKey': EXCHANGES['binance']['apiKey'],
    'secret': EXCHANGES['binance']['secret']
})
limit = 1000  # Max per Binance

# Time range from config.py (UTC, adjusted to match IST 2025-10-20 19:28:00 to 2025-10-25 15:12:00)
start_time = int(pd.Timestamp(DATA_START).timestamp() * 1000)  # 2025-10-20 19:28:00 IST in UTC
end_time = int(pd.Timestamp(DATA_END).timestamp() * 1000)    # 2025-10-25 15:12:00 IST in UTC

# Fetch paginated data for each pair
for pair in PAIRS:
    all_ohlcv = []
    last_timestamp = start_time

    print(f"Fetching {pair} from Binance (paginated with API)...")
    while last_timestamp < end_time:
        try:
            print(f"Attempting fetch with since: {last_timestamp}")  # Debug the since value
            ohlcv = exchange.fetch_ohlcv(pair, '1m', since=last_timestamp, limit=limit)
            if ohlcv and len(ohlcv) > 0:
                all_ohlcv.extend(ohlcv)
                last_timestamp = ohlcv[-1][0] + 1  # Update to next timestamp
                print(f"Fetched batch: {len(ohlcv)} rows, new since: {pd.to_datetime(last_timestamp, unit='ms')}")
            else:
                print(f"No more data at timestamp: {pd.to_datetime(last_timestamp, unit='ms')}")
                break
            time.sleep(2)
        except Exception as e:
            print(f"Error for {pair} from Binance: {e}")
            break

    if all_ohlcv:
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        # Filter to exact static range (UTC)
        df = df[(df['timestamp'] >= pd.Timestamp(DATA_START)) & 
                (df['timestamp'] <= pd.Timestamp(DATA_END))]
        df['exchange'] = 'binance'
        df['pair'] = pair
        output_file = f'data/binance_{pair.replace("/", "_")}.csv'
        if os.path.exists(output_file):
            existing_df = pd.read_csv(output_file)
            df = pd.concat([existing_df, df]).drop_duplicates(subset=['timestamp'], keep='last')
        df.to_csv(output_file, index=False)
        print(f"Saved {len(df)} rows for {pair} from Binance to {output_file}")
    else:
        print(f"No data for {pair} from Binance")