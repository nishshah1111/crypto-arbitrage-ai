# add_features.py - Adds ML features and labels to spreads CSV and saves to *_features.csv

import pandas as pd
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Pairs to process
pairs = ['BTC/USDT', 'ETH/USDT']
sources = ['binance', 'coinbase', 'kraken', 'cryptocompare']  # For feature addition

for pair in pairs:
    spreads_file = f'data/{pair.replace("/", "_").lower()}_spreads.csv'
    if not pd.io.common.file_exists(spreads_file):
        print(f"Missing spreads file for {pair}: {spreads_file}. Run compute_spreads.py first.")
        continue
    
    print(f"Adding features for {pair}...")
    df = pd.read_csv(spreads_file, parse_dates=['timestamp'])
    df.set_index('timestamp', inplace=True)  # Set index for rolling/shift
    
    # Identify spread columns (from previous step)
    spreads = [col for col in df.columns if col.startswith('spread_binance_')]
    
    # Add per-exchange lags and volatility (includes cryptocompare where data exists)
    for exchange in sources:
        if exchange in df.columns:
            df[f'{exchange}_lag_1'] = df[exchange].shift(1)
            df[f'{exchange}_lag_5'] = df[exchange].shift(5)
            df[f'{exchange}_volatility'] = df[exchange].rolling(window=60).std()  # 1-hour rolling std
    
    # Add arbitrage labels at multiple thresholds for research analysis
    if spreads:
        # Conservative threshold (0.5% - covers fees + profit)
        df['arbitrage_label_0.5'] = (df[spreads].abs() > 0.5).any(axis=1).astype(int)
        
        # Moderate threshold (0.2% - minimal profit)
        df['arbitrage_label_0.2'] = (df[spreads].abs() > 0.2).any(axis=1).astype(int)
        
        # Aggressive threshold (0.1% - speculative, may not cover fees)
        df['arbitrage_label_0.1'] = (df[spreads].abs() > 0.1).any(axis=1).astype(int)
        
        # Use 0.2% as default (balanced trade-off)
        df['arbitrage_label'] = df['arbitrage_label_0.2']
    
    # Save the features file
    output_file = f'data/{pair.replace("/", "_").lower()}_features.csv'
    df.reset_index().to_csv(output_file, index=False)
    print(f"Saved features for {pair} to {output_file} ({len(df)} rows)")
    
    # Preview: Check features and labels
    print("Sample features and labels:")
    print(df.reset_index()[['timestamp'] + [f'{exchange}_volatility' for exchange in sources if f'{exchange}_volatility' in df.columns] + ['arbitrage_label']].head(10))
    print(f"\nOpportunities detected at different thresholds:")
    print(f"  0.5% (conservative): {df['arbitrage_label_0.5'].sum()} ({df['arbitrage_label_0.5'].mean()*100:.3f}%)")
    print(f"  0.2% (moderate):     {df['arbitrage_label_0.2'].sum()} ({df['arbitrage_label_0.2'].mean()*100:.3f}%)")
    print(f"  0.1% (aggressive):   {df['arbitrage_label_0.1'].sum()} ({df['arbitrage_label_0.1'].mean()*100:.3f}%)")

print("Feature addition complete! Check /data/*_features.csv files.")