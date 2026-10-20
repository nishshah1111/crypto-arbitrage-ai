import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split, cross_validate  # Updated: for multi-metric CV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mean_squared_error, accuracy_score, precision_score, recall_score, f1_score
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from prophet import Prophet
from xgboost import XGBClassifier
import joblib
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Pairs, horizons, and thresholds
pairs = ['BTC/USDT', 'ETH/USDT']
horizons = [1, 3, 5]
thresholds = [0.1, 0.2, 0.5]  # Train models at all three thresholds

# Results list for CSV
results = []

def create_sequences(data, seq_length=60, horizon=1, target_col=-1):
    xs, ys = [], []
    for i in range(len(data) - seq_length - horizon + 1):
        xs.append(data[i:i+seq_length])
        ys.append(data[i+seq_length+horizon-1, target_col])
    return np.array(xs), np.array(ys)

for pair in pairs:
    features_file = f'data/{pair.replace("/", "_").lower()}_features.csv'
    if not pd.io.common.file_exists(features_file):
        print(f"Missing features file for {pair}: {features_file}. Run preprocessing first.")
        continue
    
    print(f"\n{'='*80}")
    print(f"Training models for {pair}")
    print(f"{'='*80}")
    df = pd.read_csv(features_file, parse_dates=['timestamp'])
    
    # Prepare base features
    key_cols = [col for col in df.columns if 'lag_' in col or 'volatility' in col or 'spread_' in col]
    # Remove threshold labels from features
    key_cols = [col for col in key_cols if 'arbitrage_label' not in col]
    
    df = df.dropna(subset=key_cols)
    
    if len(df) < 100:
        print(f"Insufficient data for {pair} after NaN drop ({len(df)} rows). Skipping.")
        continue
    
    X = df[key_cols].values
    
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Loop through thresholds
    for threshold in thresholds:
        threshold_label = f'arbitrage_label_{threshold}'
        
        if threshold_label not in df.columns:
            print(f"  Warning: {threshold_label} not found in data. Skipping.")
            continue
        
        y_class = df[threshold_label].values
        n_opportunities = y_class.sum()
        
        print(f"\n{'-'*80}")
        print(f"Threshold: {threshold}% ({n_opportunities} opportunities, {n_opportunities/len(df)*100:.3f}%)")
        print(f"{'-'*80}")
        
        # Skip if too few opportunities
        if n_opportunities < 2:
            print(f"  ⚠️  Too few opportunities ({n_opportunities}) - skipping ML training")
            results.append({
                'Pair': pair, 
                'Threshold': f'{threshold}%',
                'Model': 'ALL', 
                'Horizon': 'N/A', 
                'RMSE': 'N/A', 
                'Accuracy': 'N/A', 
                'Precision': 'N/A', 
                'Recall': 'N/A', 
                'F1_Score': 'N/A',
                'Note': f'Only {n_opportunities} opportunities - insufficient for training'
            })
            continue
        
        for horizon in horizons:
            print(f"\n  Horizon: {horizon} min")
            
            # LSTM Forecasting (regression on spreads)
            seq_length = 60
            if 'spread_binance_coinbase' in df.columns:
                target_idx = list(df.columns).index('spread_binance_coinbase') - 1
            else:
                target_idx = -2
            
            X_lstm, y_lstm = create_sequences(X_scaled, seq_length, horizon, target_idx)
            if len(X_lstm) == 0:
                continue
            X_train_l, X_test_l, y_train_l, y_test_l = train_test_split(X_lstm, y_lstm, test_size=0.2, shuffle=False)
            
            model_lstm = Sequential()
            model_lstm.add(LSTM(50, return_sequences=True, input_shape=(seq_length, X_scaled.shape[1])))
            model_lstm.add(Dropout(0.2))
            model_lstm.add(LSTM(50))
            model_lstm.add(Dense(1))
            model_lstm.compile(optimizer='adam', loss='mse')
            model_lstm.fit(X_train_l, y_train_l, epochs=50, batch_size=32, validation_split=0.1, verbose=0)
            
            preds_l = model_lstm.predict(X_test_l, verbose=0)
            rmse_lstm = np.sqrt(mean_squared_error(y_test_l, preds_l))
            print(f"    LSTM RMSE: {rmse_lstm:.6f}")
            model_lstm.save(f'models/lstm_{pair.replace("/", "_").lower()}_{threshold}pct_{horizon}min.keras')
            results.append({
                'Pair': pair, 
                'Threshold': f'{threshold}%',
                'Model': 'LSTM', 
                'Horizon': horizon, 
                'RMSE': rmse_lstm, 
                'Accuracy': 'N/A', 
                'Precision': 'N/A', 
                'Recall': 'N/A', 
                'F1_Score': 'N/A',
                'Note': 'Regression model'
            })
            
            # Prophet Forecasting (regression on spreads)
            df_prop = df[['timestamp', key_cols[target_idx + 1]]].rename(columns={key_cols[target_idx + 1]: 'y', 'timestamp': 'ds'})
            model_prop = Prophet(daily_seasonality=False, yearly_seasonality=False)
            model_prop.fit(df_prop.iloc[:-horizon])
            future = model_prop.make_future_dataframe(periods=horizon, freq='min')
            forecast = model_prop.predict(future)
            rmse_prop = np.sqrt(mean_squared_error(df_prop['y'].iloc[-horizon:], forecast['yhat'].iloc[-horizon:]))
            print(f"    Prophet RMSE: {rmse_prop:.6f}")
            results.append({
                'Pair': pair,
                'Threshold': f'{threshold}%',
                'Model': 'Prophet', 
                'Horizon': horizon, 
                'RMSE': rmse_prop, 
                'Accuracy': 'N/A', 
                'Precision': 'N/A', 
                'Recall': 'N/A', 
                'F1_Score': 'N/A',
                'Note': 'Regression model'
            })
            
            # Random Forest Classification
            X_train_rf, X_test_rf, y_train_rf, y_test_rf = train_test_split(X, y_class, test_size=0.2, stratify=None, shuffle=False)
            
            # Apply SMOTE only if we have enough positive samples
            if sum(y_train_rf) >= 2:
                k_neighbors = min(sum(y_train_rf) - 1, 5)
                smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                X_train_rf_res, y_train_rf_res = smote.fit_resample(X_train_rf, y_train_rf)
            else:
                X_train_rf_res, y_train_rf_res = X_train_rf, y_train_rf
            
            clf_rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
            clf_rf.fit(X_train_rf_res, y_train_rf_res)
            
            # Cross-validation (only if enough positive samples)
            if sum(y_class) >= 5:
                pipeline = Pipeline([
                    ('smote', SMOTE(random_state=42, k_neighbors=min(sum(y_class) - 1, 5))),
                    ('rf', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42))
                ])
                scoring = {'f1': 'f1', 'accuracy': 'accuracy', 'precision': 'precision', 'recall': 'recall'}
                cv_results = cross_validate(pipeline, X, y_class, cv=min(5, sum(y_class)), scoring=scoring, error_score=0.0)
                print(f"    RF Mean F1 (CV): {cv_results['test_f1'].mean():.4f}")
                print(f"    RF Mean Accuracy (CV): {cv_results['test_accuracy'].mean():.4f}")
                print(f"    RF Mean Precision (CV): {cv_results['test_precision'].mean():.4f}")
                print(f"    RF Mean Recall (CV): {cv_results['test_recall'].mean():.4f}")
            else:
                print(f"    RF: Too few positives ({sum(y_class)}) for CV, using single split")
                cv_results = {'test_f1': [0], 'test_accuracy': [0], 'test_precision': [0], 'test_recall': [0]}
            
            preds_rf = clf_rf.predict(X_test_rf)
            f1_rf = f1_score(y_test_rf, preds_rf, zero_division=0)
            acc_rf = accuracy_score(y_test_rf, preds_rf)
            prec_rf = precision_score(y_test_rf, preds_rf, zero_division=0)
            rec_rf = recall_score(y_test_rf, preds_rf, zero_division=0)
            print(f"    RF Test F1: {f1_rf:.4f}, Accuracy: {acc_rf:.4f}, Precision: {prec_rf:.4f}, Recall: {rec_rf:.4f}")
            joblib.dump(clf_rf, f'models/rf_{pair.replace("/", "_").lower()}_{threshold}pct_{horizon}min.pkl')
            results.append({
                'Pair': pair,
                'Threshold': f'{threshold}%',
                'Model': 'RF', 
                'Horizon': horizon, 
                'RMSE': 'N/A', 
                'Accuracy': cv_results['test_accuracy'].mean() if sum(y_class) >= 5 else acc_rf, 
                'Precision': cv_results['test_precision'].mean() if sum(y_class) >= 5 else prec_rf, 
                'Recall': cv_results['test_recall'].mean() if sum(y_class) >= 5 else rec_rf, 
                'F1_Score': cv_results['test_f1'].mean() if sum(y_class) >= 5 else f1_rf,
                'Note': 'CV metrics' if sum(y_class) >= 5 else 'Test split metrics'
            })
            
            # XGBoost Classification
            scale_pos_weight = sum(y_class==0)/sum(y_class==1) if sum(y_class)>0 else 1
            clf_xgb = XGBClassifier(n_estimators=100, scale_pos_weight=scale_pos_weight, random_state=42)
            
            if sum(y_train_rf) >= 2:
                k_neighbors = min(sum(y_train_rf) - 1, 5)
                smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                X_train_xgb_res, y_train_xgb_res = smote.fit_resample(X_train_rf, y_train_rf)
                clf_xgb.fit(X_train_xgb_res, y_train_xgb_res)
            else:
                clf_xgb.fit(X_train_rf, y_train_rf)
            
            # Cross-validation
            if sum(y_class) >= 5:
                pipeline_xgb = Pipeline([
                    ('smote', SMOTE(random_state=42, k_neighbors=min(sum(y_class) - 1, 5))),
                    ('xgb', XGBClassifier(n_estimators=100, random_state=42))
                ])
                cv_results_xgb = cross_validate(pipeline_xgb, X, y_class, cv=min(5, sum(y_class)), scoring=scoring, error_score=0.0)
                print(f"    XGBoost Mean F1 (CV): {cv_results_xgb['test_f1'].mean():.4f}")
                print(f"    XGBoost Mean Accuracy (CV): {cv_results_xgb['test_accuracy'].mean():.4f}")
                print(f"    XGBoost Mean Precision (CV): {cv_results_xgb['test_precision'].mean():.4f}")
                print(f"    XGBoost Mean Recall (CV): {cv_results_xgb['test_recall'].mean():.4f}")
            else:
                print(f"    XGBoost: Too few positives for CV, using single split")
                cv_results_xgb = {'test_f1': [0], 'test_accuracy': [0], 'test_precision': [0], 'test_recall': [0]}
            
            preds_xgb = clf_xgb.predict(X_test_rf)
            f1_xgb = f1_score(y_test_rf, preds_xgb, zero_division=0)
            acc_xgb = accuracy_score(y_test_rf, preds_xgb)
            prec_xgb = precision_score(y_test_rf, preds_xgb, zero_division=0)
            rec_xgb = recall_score(y_test_rf, preds_xgb, zero_division=0)
            print(f"    XGBoost Test F1: {f1_xgb:.4f}, Accuracy: {acc_xgb:.4f}, Precision: {prec_xgb:.4f}, Recall: {rec_xgb:.4f}")
            joblib.dump(clf_xgb, f'models/xgb_{pair.replace("/", "_").lower()}_{threshold}pct_{horizon}min.pkl')
            results.append({
                'Pair': pair,
                'Threshold': f'{threshold}%',
                'Model': 'XGBoost', 
                'Horizon': horizon, 
                'RMSE': 'N/A', 
                'Accuracy': cv_results_xgb['test_accuracy'].mean() if sum(y_class) >= 5 else acc_xgb, 
                'Precision': cv_results_xgb['test_precision'].mean() if sum(y_class) >= 5 else prec_xgb, 
                'Recall': cv_results_xgb['test_recall'].mean() if sum(y_class) >= 5 else rec_xgb, 
                'F1_Score': cv_results_xgb['test_f1'].mean() if sum(y_class) >= 5 else f1_xgb,
                'Note': 'CV metrics' if sum(y_class) >= 5 else 'Test split metrics'
            })

# Save results to CSV
results_df = pd.DataFrame(results)
results_df.to_csv('data/model_results.csv', index=False)
print(f"\n{'='*80}")
print("TRAINING COMPLETE!")
print(f"{'='*80}")
print(f"\nResults saved to data/model_results.csv")
print(f"Total models trained: {len(results)}")
print(f"\nSummary by threshold:")
for threshold in thresholds:
    threshold_results = results_df[results_df['Threshold'] == f'{threshold}%']
    if len(threshold_results) > 0:
        print(f"\n{threshold}% threshold:")
        print(f"  Models: {len(threshold_results)}")
        # Show best F1 scores
        best_results = threshold_results[threshold_results['F1_Score'] != 'N/A'].copy()
        if len(best_results) > 0:
            best_results['F1_Score'] = pd.to_numeric(best_results['F1_Score'], errors='coerce')
            best_model = best_results.loc[best_results['F1_Score'].idxmax()]
            print(f"  Best F1: {best_model['F1_Score']:.4f} ({best_model['Model']}, {best_model['Pair']}, {best_model['Horizon']}min)")