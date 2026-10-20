import pandas as pd
import os
from datetime import datetime

results_file = 'data/model_results.csv'

if os.path.exists(results_file):
    df = pd.read_csv(results_file)
    print(f"{'='*80}")
    print(f"TRAINING PROGRESS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"\nTotal models trained so far: {len(df)}")
    
    # Expected total: 2 pairs × 3 thresholds × 3 horizons × 4 models = 72 models
    expected_total = 2 * 3 * 3 * 4
    print(f"Expected total: {expected_total} models")
    print(f"Progress: {len(df)}/{expected_total} ({len(df)/expected_total*100:.1f}%)")
    
    # Show breakdown by pair and threshold
    print(f"\n{'='*80}")
    print("BREAKDOWN BY PAIR AND THRESHOLD:")
    print(f"{'='*80}")
    for pair in df['Pair'].unique():
        print(f"\n{pair}:")
        pair_df = df[df['Pair'] == pair]
        for threshold in sorted(pair_df['Threshold'].unique()):
            threshold_df = pair_df[pair_df['Threshold'] == threshold]
            print(f"  {threshold}%: {len(threshold_df)} models trained")
    
    # Show recent entries
    print(f"\n{'='*80}")
    print("MOST RECENT MODELS:")
    print(f"{'='*80}")
    print(df.tail(10).to_string())
    
else:
    print("Training not started yet - model_results.csv not found.")
