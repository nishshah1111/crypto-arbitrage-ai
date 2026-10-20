import pandas as pd
import os
import warnings

# Suppress FutureWarnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Sources and pair (focus on BTC/USDT for now)
sources = ['binance', 'coinbase', 'kraken', 'cryptocompare']
pair = 'BTC/USDT'  # Change to 'ETH/USDT' later if needed

# Load all CSVs and find global min/max timestamp
all_dfs = []
min_ts = pd.Timestamp.max
max_ts = pd.Timestamp.min

for source in sources:
    file_name = f'data/{source}_BTC_USDT.csv'  # Adjust filenames if needed (e.g., kraken_BTC_USDT.csv)
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        df['timestamp'] = pd.to_datetime(df['timestamp'])  # Naive UTC
        all_dfs.append((source, df))
        min_ts = min(min_ts, df['timestamp'].min())
        max_ts = max(max_ts, df['timestamp'].max())
        print(f"Loaded {source}: {len(df)} rows, from {df['timestamp'].min()} to {df['timestamp'].max()}")
    else:
        print(f"Missing file: {file_name}")

if not all_dfs:
    raise ValueError("No data files found!")

# Create full 1-minute index based on actual data range
full_index = pd.date_range(start=min_ts, end=max_ts, freq='1min')
print(f"Full index: from {min_ts} to {max_ts}, {len(full_index)} timestamps")

# Reindex each source to full_index, use ffill only for internal gaps (leave leading NaNs)
merged_dfs = []
for source, orig_df in all_dfs:
    df = orig_df.set_index('timestamp').reindex(full_index)
    # Fill numeric columns with ffill only (handles internal gaps, keeps leading NaNs)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = df[col].ffill()
    # Fill categorical columns (exchange, pair)
    df['exchange'] = source
    df['pair'] = pair
    merged_dfs.append(df.reset_index().rename(columns={'index': 'timestamp'}))

# Concat all sources
merged_df = pd.concat(merged_dfs, ignore_index=True)
merged_df = merged_df.sort_values(['timestamp', 'exchange'])
merged_df = merged_df.drop_duplicates(subset=['timestamp', 'exchange'])

# Drop rows where a source has no data (all numeric NaN) to avoid clutter
merged_df = merged_df.dropna(subset=['open', 'high', 'low', 'close', 'volume'], how='all')

# Save the merged file
output_file = f'data/{pair.replace("/", "_")}_merged.csv'
merged_df.to_csv(output_file, index=False)
print(f"Merged {len(merged_df)} rows (with NaNs for missing periods) to {output_file}")

# Optional: Preview around the transition for CryptoCompare
preview_start = merged_df[merged_df['timestamp'] < '2025-10-20 22:09:00'].tail(10)
preview_end = merged_df[merged_df['timestamp'] >= '2025-10-20 22:09:00'].head(10)
print("Preview before CryptoCompare start (should have NaN for cryptocompare if rows kept):")
print(preview_start)
print("Preview after CryptoCompare start:")
print(preview_end)