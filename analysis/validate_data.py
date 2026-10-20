"""
Data Validation Script
Checks all data quality, logic, and threshold labels
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("DATA VALIDATION AND VERIFICATION")
print("=" * 80)

for pair in ['BTC/USDT', 'ETH/USDT']:
    print(f"\n{'='*80}")
    print(f"{pair} VALIDATION")
    print(f"{'='*80}")
    
    # Load features
    features_file = f'data/{pair.replace("/", "_").lower()}_features.csv'
    df = pd.read_csv(features_file, parse_dates=['timestamp'])
    
    print(f"\n1. BASIC DATA INFO")
    print(f"   Total rows: {len(df):,}")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   Duration: {(df['timestamp'].max() - df['timestamp'].min()).days} days")
    print(f"   Total columns: {len(df.columns)}")
    
    # Check for missing values
    print(f"\n2. MISSING VALUES CHECK")
    missing = df.isnull().sum()
    critical_cols = ['binance', 'coinbase', 'kraken', 'spread_binance_coinbase', 
                     'spread_binance_kraken', 'arbitrage_label']
    print(f"   Total missing values: {missing.sum():,}")
    for col in critical_cols:
        if col in df.columns:
            print(f"   {col}: {missing[col]:,} ({missing[col]/len(df)*100:.2f}%)")
    
    # Spread statistics
    print(f"\n3. SPREAD STATISTICS (in %)")
    spread_cols = [c for c in df.columns if 'spread_binance_' in c]
    for col in spread_cols:
        data = df[col].dropna()
        if len(data) > 0:
            print(f"\n   {col}:")
            print(f"      Count: {len(data):,}")
            print(f"      Mean: {data.mean():.4f}%")
            print(f"      Std: {data.std():.4f}%")
            print(f"      Min: {data.min():.4f}%")
            print(f"      Max: {data.max():.4f}%")
            print(f"      >0.1%: {(data.abs() > 0.1).sum()} ({(data.abs() > 0.1).sum()/len(data)*100:.2f}%)")
            print(f"      >0.3%: {(data.abs() > 0.3).sum()} ({(data.abs() > 0.3).sum()/len(data)*100:.2f}%)")
            print(f"      >0.5%: {(data.abs() > 0.5).sum()} ({(data.abs() > 0.5).sum()/len(data)*100:.2f}%)")
    
    # Threshold label verification
    print(f"\n4. THRESHOLD LABEL VERIFICATION")
    if 'arbitrage_label_0.5' in df.columns:
        label_05 = df['arbitrage_label_0.5'].sum()
        label_03 = df['arbitrage_label_0.3'].sum()
        label_01 = df['arbitrage_label_0.1'].sum()
        
        print(f"   0.5% threshold: {label_05} opportunities ({label_05/len(df)*100:.3f}%)")
        print(f"   0.3% threshold: {label_03} opportunities ({label_03/len(df)*100:.3f}%)")
        print(f"   0.1% threshold: {label_01} opportunities ({label_01/len(df)*100:.3f}%)")
        print(f"   Default label: {df['arbitrage_label'].sum()} (should match 0.3%)")
        
        # Verify logic: 0.5 should be subset of 0.3 should be subset of 0.1
        if label_05 <= label_03 <= label_01:
            print(f"   ✅ Logic check PASSED: 0.5% ≤ 0.3% ≤ 0.1%")
        else:
            print(f"   ❌ Logic check FAILED: Unexpected hierarchy")
    
    # Manual verification of threshold logic
    print(f"\n5. MANUAL THRESHOLD LOGIC VERIFICATION")
    # Find rows where spread > 0.5%
    manual_05 = 0
    manual_03 = 0
    manual_01 = 0
    
    for idx, row in df.iterrows():
        max_spread = 0
        for col in spread_cols:
            if not pd.isna(row[col]):
                max_spread = max(max_spread, abs(row[col]))
        
        if max_spread > 0.5:
            manual_05 += 1
        if max_spread > 0.3:
            manual_03 += 1
        if max_spread > 0.1:
            manual_01 += 1
    
    print(f"   Manual count (>0.5%): {manual_05}")
    print(f"   Manual count (>0.3%): {manual_03}")
    print(f"   Manual count (>0.1%): {manual_01}")
    
    if 'arbitrage_label_0.5' in df.columns:
        if manual_05 == label_05:
            print(f"   ✅ 0.5% threshold matches manual calculation")
        else:
            print(f"   ❌ 0.5% threshold mismatch: {label_05} vs {manual_05}")
        
        if manual_03 == label_03:
            print(f"   ✅ 0.3% threshold matches manual calculation")
        else:
            print(f"   ❌ 0.3% threshold mismatch: {label_03} vs {manual_03}")
        
        if manual_01 == label_01:
            print(f"   ✅ 0.1% threshold matches manual calculation")
        else:
            print(f"   ❌ 0.1% threshold mismatch: {label_01} vs {manual_01}")
    
    # Feature completeness check
    print(f"\n6. FEATURE COMPLETENESS")
    lag_cols = [c for c in df.columns if '_lag_' in c]
    vol_cols = [c for c in df.columns if '_volatility' in c]
    
    print(f"   Lag features: {len(lag_cols)} columns")
    print(f"   Volatility features: {len(vol_cols)} columns")
    
    # Check first few rows (should have NaN for lags/volatility)
    print(f"   First 5 rows lag_1 NaNs: {df[lag_cols[0]].head(5).isnull().sum()}/5 (expected: 1)")
    if len(vol_cols) > 0:
        print(f"   First 60 rows volatility NaNs: {df[vol_cols[0]].head(60).isnull().sum()}/60 (expected: 60)")
    
    # Show sample opportunities
    print(f"\n7. SAMPLE ARBITRAGE OPPORTUNITIES")
    if df['arbitrage_label_0.1'].sum() > 0:
        opp_samples = df[df['arbitrage_label_0.1'] == 1].head(3)
        for idx, row in opp_samples.iterrows():
            print(f"\n   Opportunity at {row['timestamp']}:")
            for col in spread_cols:
                if not pd.isna(row[col]):
                    print(f"      {col}: {row[col]:.4f}%")
    else:
        print(f"   No opportunities found at 0.1% threshold")

print(f"\n{'='*80}")
print("OVERALL ASSESSMENT")
print(f"{'='*80}")

# Load both files and compare
btc_df = pd.read_csv('data/btc_usdt_features.csv')
eth_df = pd.read_csv('data/eth_usdt_features.csv')

print(f"\nData Quality Summary:")
print(f"  BTC rows: {len(btc_df):,}")
print(f"  ETH rows: {len(eth_df):,}")
print(f"  BTC opportunities (0.1%): {btc_df['arbitrage_label_0.1'].sum()}")
print(f"  ETH opportunities (0.1%): {eth_df['arbitrage_label_0.1'].sum()}")

print(f"\nRecommendation for Model Training:")
if btc_df['arbitrage_label_0.1'].sum() > 100:
    print(f"  ✅ 0.1% threshold: Sufficient data for ML training")
else:
    print(f"  ⚠️  0.1% threshold: Limited data, may need data augmentation")

if btc_df['arbitrage_label_0.3'].sum() > 10:
    print(f"  ⚠️  0.3% threshold: Limited but usable with SMOTE")
else:
    print(f"  ❌ 0.3% threshold: Too few samples for reliable training")

if btc_df['arbitrage_label_0.5'].sum() > 5:
    print(f"  ⚠️  0.5% threshold: Minimal data, expect low F1-scores")
else:
    print(f"  ❌ 0.5% threshold: Insufficient data for training")

print(f"\n{'='*80}")
print("VALIDATION COMPLETE")
print(f"{'='*80}")
