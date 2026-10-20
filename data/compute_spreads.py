# compute_spreads.py - Computes spreads from merged CSV and saves to *_spreads.csv

import pandas as pd
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Pairs to process
pairs = ['BTC/USDT', 'ETH/USDT']
sources = ['binance', 'coinbase', 'kraken', 'cryptocompare']  # For spread calculations

for pair in pairs:
    merged_file = f'data/{pair.replace("/", "_")}_merged.csv'
    if not pd.io.common.file_exists(merged_file):
        print(f"Missing merged file for {pair}: {merged_file}. Run merging script first.")
        continue
    
    print(f"Computing spreads for {pair}...")
    df = pd.read_csv(merged_file, parse_dates=['timestamp'])
    
    # Pivot on 'close' for each exchange (includes all sources like cryptocompare)
    pivot_close = df.pivot(index='timestamp', columns='exchange', values='close')
    
    # Calculate percentage spreads (using Binance as base; includes cryptocompare if data available)
    spreads = []
    if 'binance' in pivot_close.columns:
        for other in [s for s in sources if s != 'binance']:
            if other in pivot_close.columns:
                spread_col = f'spread_binance_{other}'
                pivot_close[spread_col] = (pivot_close['binance'] - pivot_close[other]) / pivot_close['binance'] * 100
                spreads.append(spread_col)
    
    # Handle NaNs in spreads (drop rows where all spreads are NaN, but keep where partial data exists)
    pivot_close = pivot_close.dropna(subset=spreads, how='all')
    
    # Save the spreads file (wide format with exchanges as columns + spreads)
    output_file = f'data/{pair.replace("/", "_").lower()}_spreads.csv'
    pivot_close.reset_index().to_csv(output_file, index=False)
    print(f"Saved spreads for {pair} to {output_file} ({len(pivot_close)} rows)")
    
    # Preview: Check spreads (cryptocompare spread will be NaN until its data starts)
    print("Sample spreads:")
    print(pivot_close.reset_index()[['timestamp'] + spreads].head(10))

print("Spread computation complete! Check /data/*_spreads.csv files. Run add_features.py next.")