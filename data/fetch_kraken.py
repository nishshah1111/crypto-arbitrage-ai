import ccxt
import pandas as pd
import time
import os

# Load settings from the project-root config.py
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXCHANGES, API_KEYS, ML_PAIRS as PAIRS, DATA_START, DATA_END

# Initialize Kraken with API key
exchange = ccxt.kraken({
    'enableRateLimit': True,
    'apiKey': EXCHANGES['kraken']['apiKey'],
    'secret': EXCHANGES['kraken']['secret']
})
limit = 1000  # Adjusted limit for trades

# Time range from config.py (naive UTC, aligned with IST 2025-10-20 19:28:00 to 2025-10-25 15:12:00)
start_time = int(pd.Timestamp(DATA_START).timestamp() * 1000)  # 2025-10-20 19:28:00 IST in UTC
end_time = int(pd.Timestamp(DATA_END).timestamp() * 1000)    # 2025-10-25 15:12:00 IST in UTC

# Function to aggregate trades to 1-minute OHLCV
def trades_to_ohlcv(trades, timeframe='1min'):
    if not trades or not isinstance(trades, list):
        return pd.DataFrame()
    df = pd.DataFrame(trades, columns=['timestamp', 'price', 'amount'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    print(f"Trade data sample: {df.head()}")  # Debug trade data
    df = df.set_index('timestamp').resample(timeframe).agg({
        'price': ['first', 'max', 'min', 'last'],
        'amount': 'sum'
    })
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.reset_index().dropna()
    print(f"Aggregated OHLCV sample: {df.head()}")  # Debug aggregated data
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

# Fetch paginated data for each pair
for pair in ['XXBTZUSD', 'XETHZUSD']:  # Correct Kraken pair symbols
    all_ohlcv = []
    last_timestamp = start_time
    retry_count = 0
    max_retries = 5  # Limit retries to avoid infinite loop

    print(f"Fetching {pair} from Kraken (paginated with API)...")
    while last_timestamp < end_time:
        try:
            print(f"Attempting fetch with since: {last_timestamp}")  # Debug the since value
            trades = exchange.fetch_trades(pair, since=last_timestamp, limit=limit)
            if trades and len(trades) > 0:
                df_trades = trades_to_ohlcv(trades, '1min')
                if not df_trades.empty:
                    # Convert to list of lists for all_ohlcv
                    trade_ohlcv = [[int(t.timestamp.value / 10**6), t.open, t.high, t.low, t.close, t.volume] for t in df_trades.itertuples()]
                    # Filter trades within the range
                    df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
                    df_trades = df_trades[(df_trades['timestamp'] >= pd.Timestamp(DATA_START)) & 
                                          (df_trades['timestamp'] <= pd.Timestamp(DATA_END))]
                    all_ohlcv.extend(trade_ohlcv)
                    # Update last_timestamp to the max timestamp, ensure at least 1-minute advance
                    max_timestamp = df_trades['timestamp'].max() if not df_trades.empty else pd.Timestamp('1970-01-01')
                    new_timestamp = int(max_timestamp.value / 10**6) + 60000 if not df_trades.empty else last_timestamp + (limit * 60000)
                    last_timestamp = max(new_timestamp, last_timestamp + 60000)  # Ensure progress
                    print(f"Fetched trades batch: {len(df_trades)} rows, new since: {pd.to_datetime(last_timestamp, unit='ms')}")
                    retry_count = 0  # Reset retry count on successful fetch
                else:
                    print(f"No valid trade data at timestamp: {pd.to_datetime(last_timestamp, unit='ms')}")
                    last_timestamp += 60000  # Advance by 1 minute if no valid data
                    retry_count += 1
                    if retry_count > max_retries:
                        print(f"Max retries reached at {pd.to_datetime(last_timestamp, unit='ms')}, breaking loop")
                        break
            else:
                print(f"No more data at timestamp: {pd.to_datetime(last_timestamp, unit='ms')}")
                break
            time.sleep(2)
        except Exception as e:
            print(f"Error for {pair} from Kraken: {e}")
            break

    if all_ohlcv:
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        # Final filter to ensure range
        df = df[(df['timestamp'] >= pd.Timestamp(DATA_START)) & 
                (df['timestamp'] <= pd.Timestamp(DATA_END))]
        df['exchange'] = 'kraken'
        df['pair'] = pair.replace('XXBTZ', 'BTC').replace('XETHZ', 'ETH') + '/USD'
        output_file = f'data/kraken_{pair.replace("Z", "").replace("X", "").replace("BT", "BTC").replace("ETH", "ETH")}.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved {len(df)} rows for {pair} from Kraken to {output_file}")
    else:
        print(f"No data for {pair} from Kraken")