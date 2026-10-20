"""
Simplified Model Training - Random Forest and XGBoost Only
Trains models at all three thresholds (0.1%, 0.2%, 0.5%) for both pairs
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_validate
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import warnings

warnings.filterwarnings("ignore")

# Configuration
pairs = ['BTC/USDT', 'ETH/USDT']
thresholds = [0.1, 0.2, 0.5]
results = []

print("="*80)
print("ARBITRAGE PREDICTION MODEL TRAINING")
print("="*80)
print(f"\nTraining Configuration:")
print(f"  Pairs: {pairs}")
print(f"  Thresholds: {thresholds}")
print(f"  Models: Random Forest, XGBoost")
print(f"  Cross-validation: 5-fold")
print(f"  Class balancing: SMOTE")

for pair in pairs:
    features_file = f'data/{pair.replace("/", "_").lower()}_features.csv'
    
    print(f"\n{'='*80}")
    print(f"Training models for {pair}")
    print(f"{'='*80}")
    
    df = pd.read_csv(features_file, parse_dates=['timestamp'])
    
    # Prepare features (exclude timestamp and label columns)
    feature_cols = [col for col in df.columns if ('lag_' in col or 'volatility' in col or 'spread_' in col) 
                    and 'arbitrage_label' not in col]
    
    # Drop NaN rows
    df_clean = df.dropna(subset=feature_cols)
    X = df_clean[feature_cols].values
    
    print(f"\nDataset: {len(df_clean)} samples, {len(feature_cols)} features")
    
    # Train at each threshold
    for threshold in thresholds:
        print(f"\n{'-'*80}")
        print(f"Threshold: {threshold}%")
        print(f"{'-'*80}")
        
        label_col = f'arbitrage_label_{threshold}'
        y = df_clean[label_col].values
        
        n_opportunities = y.sum()
        n_total = len(y)
        pct_opportunities = (n_opportunities / n_total) * 100
        
        print(f"Opportunities: {n_opportunities}/{n_total} ({pct_opportunities:.2f}%)")
        
        # Skip if no positive samples
        if n_opportunities == 0:
            print(f"⚠️  No opportunities at {threshold}% threshold - skipping")
            continue
        
        # Skip if only 1 positive sample (can't split for CV)
        if n_opportunities < 2:
            print(f"⚠️  Too few opportunities ({n_opportunities}) for training - skipping")
            continue
        
        #  === RANDOM FOREST ===
        print(f"\n  Training Random Forest...")
        
        try:
            # Apply SMOTE for class imbalance
            smote = SMOTE(random_state=42, k_neighbors=min(5, n_opportunities - 1))
            X_resampled, y_resampled = smote.fit_resample(X, y)
            
            print(f"    After SMOTE: {y_resampled.sum()} positive, {len(y_resampled) - y_resampled.sum()} negative")
            
            # Initialize RF
            rf = RandomForestClassifier(
                n_estimators=100,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
            
            # Cross-validation
            cv_results = cross_validate(
                rf, X_resampled, y_resampled,
                cv=min(5, n_opportunities),  # Use fewer folds if needed
                scoring=['accuracy', 'precision', 'recall', 'f1'],
                return_train_score=False
            )
            
            mean_f1 = cv_results['test_f1'].mean()
            mean_acc = cv_results['test_accuracy'].mean()
            mean_prec = cv_results['test_precision'].mean()
            mean_rec = cv_results['test_recall'].mean()
            
            print(f"    CV Results (mean):")
            print(f"      F1: {mean_f1:.4f}")
            print(f"      Accuracy: {mean_acc:.4f}")
            print(f"      Precision: {mean_prec:.4f}")
            print(f"      Recall: {mean_rec:.4f}")
            
            # Save result
            results.append({
                'Pair': pair,
                'Threshold': threshold,
                'Model': 'Random Forest',
                'Samples': n_total,
                'Opportunities': n_opportunities,
                'Opportunity_Pct': f'{pct_opportunities:.2f}%',
                'F1_Score': f'{mean_f1:.4f}',
                'Accuracy': f'{mean_acc:.4f}',
                'Precision': f'{mean_prec:.4f}',
                'Recall': f'{mean_rec:.4f}'
            })
            
        except Exception as e:
            print(f"    ⚠️  Error training Random Forest: {e}")
        
        # === XGBOOST ===
        print(f"\n  Training XGBoost...")
        
        try:
            # Calculate scale_pos_weight for imbalance
            n_neg = (y == 0).sum()
            scale_pos_weight = n_neg / n_opportunities if n_opportunities > 0 else 1
            
            # Initialize XGBoost
            xgb = XGBClassifier(
                n_estimators=100,
                scale_pos_weight=scale_pos_weight,
                random_state=42,
                n_jobs=-1,
                eval_metric='logloss'
            )
            
            # Cross-validation
            cv_results = cross_validate(
                xgb, X, y,
                cv=min(5, n_opportunities),
                scoring=['accuracy', 'precision', 'recall', 'f1'],
                return_train_score=False
            )
            
            mean_f1 = cv_results['test_f1'].mean()
            mean_acc = cv_results['test_accuracy'].mean()
            mean_prec = cv_results['test_precision'].mean()
            mean_rec = cv_results['test_recall'].mean()
            
            print(f"    CV Results (mean):")
            print(f"      F1: {mean_f1:.4f}")
            print(f"      Accuracy: {mean_acc:.4f}")
            print(f"      Precision: {mean_prec:.4f}")
            print(f"      Recall: {mean_rec:.4f}")
            
            # Save result
            results.append({
                'Pair': pair,
                'Threshold': threshold,
                'Model': 'XGBoost',
                'Samples': n_total,
                'Opportunities': n_opportunities,
                'Opportunity_Pct': f'{pct_opportunities:.2f}%',
                'F1_Score': f'{mean_f1:.4f}',
                'Accuracy': f'{mean_acc:.4f}',
                'Precision': f'{mean_prec:.4f}',
                'Recall': f'{mean_rec:.4f}'
            })
            
        except Exception as e:
            print(f"    ⚠️  Error training XGBoost: {e}")

# Save results
print(f"\n\n{'='*80}")
print("TRAINING COMPLETE - RESULTS SUMMARY")
print(f"{'='*80}\n")

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

# Save to CSV
results_df.to_csv('data/model_results.csv', index=False)
print(f"\n\nResults saved to: data/model_results.csv")

# Summary by threshold
print(f"\n\n{'='*80}")
print("SUMMARY BY THRESHOLD:")
print(f"{'='*80}")

for threshold in thresholds:
    threshold_df = results_df[results_df['Threshold'] == threshold]
    if len(threshold_df) > 0:
        print(f"\n{threshold}% Threshold:")
        print(f"  Models trained: {len(threshold_df)}")
        
        # Convert string scores back to float for calculation
        f1_scores = [float(score) for score in threshold_df['F1_Score'].values]
        print(f"  Average F1 Score: {np.mean(f1_scores):.4f}")
        print(f"  Best F1 Score: {np.max(f1_scores):.4f}")
        
        # Show best model
        best_idx = threshold_df['F1_Score'].astype(float).idxmax()
        best_model = threshold_df.loc[best_idx]
        print(f"  Best Model: {best_model['Model']} ({best_model['Pair']})")

print(f"\n\n{'='*80}")
print("KEY FINDINGS:")
print(f"{'='*80}")
print("""
1. THRESHOLD COMPARISON:
   - 0.1%: Many samples (~300), good F1 scores expected
   - 0.2%: Moderate samples (~15), balanced approach
   - 0.5%: Few samples (~2-3), poor F1 scores expected

2. MODEL PERFORMANCE:
   - Random Forest with SMOTE: Handles imbalance well
   - XGBoost with scale_pos_weight: Alternative approach

3. NEXT STEPS:
   - Run economic_analysis.py to evaluate profitability
   - Compare ML performance vs economic viability
   - Write research paper with findings
""")

print("\nTraining complete!")
