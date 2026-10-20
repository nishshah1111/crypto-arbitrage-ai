"""
Prediction Agent - ML-based Arbitrage Prediction
Uses trained models to predict if arbitrage opportunities will persist or widen
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import joblib
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Try to import TensorFlow, but make it optional
try:
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. LSTM predictions will be disabled.")


class PredictionAgent:
    """
    Autonomous agent for predicting arbitrage opportunity viability.
    Uses pre-trained ML models (LSTM, XGBoost, Random Forest).
    """
    
    def __init__(self, models_dir: str = 'models'):
        """
        Initialize the Prediction Agent
        
        Args:
            models_dir: Directory containing trained models
        """
        # Get absolute path relative to this file
        import os
        if not os.path.isabs(models_dir):
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_dir = os.path.join(script_dir, models_dir)
        
        self.models_dir = Path(models_dir)
        self.models = {}
        self.scalers = {}
        self.prediction_history = []
        
        print(f"🔮 Initializing Prediction Agent...")
        self._load_models()
    
    def _load_models(self):
        """Load available pre-trained models"""
        if not self.models_dir.exists():
            print(f"Warning: Models directory {self.models_dir} not found")
            return
        
        # Load XGBoost and Random Forest models
        for model_file in self.models_dir.glob('*.pkl'):
            try:
                model_name = model_file.stem
                self.models[model_name] = joblib.load(model_file)
                print(f"  ✓ Loaded {model_name}")
            except Exception as e:
                print(f"  ✗ Failed to load {model_file.name}: {e}")
        
        # Load LSTM models if TensorFlow is available
        if TENSORFLOW_AVAILABLE:
            for model_file in self.models_dir.glob('*.keras'):
                try:
                    model_name = model_file.stem
                    self.models[model_name] = keras.models.load_model(model_file)
                    print(f"  ✓ Loaded {model_name}")
                except Exception as e:
                    print(f"  ✗ Failed to load {model_file.name}: {e}")
        
        print(f"  Total models loaded: {len(self.models)}")
    
    def prepare_features(self, price_df: pd.DataFrame, 
                         historical_df: Optional[pd.DataFrame] = None) -> np.ndarray:
        """
        Prepare features from current price data
        
        Args:
            price_df: Current price DataFrame
            historical_df: Optional historical data for lag features
            
        Returns:
            Feature array ready for model input
        """
        features = []
        
        # Calculate basic spread features
        exchanges = price_df['exchange'].unique()
        prices = price_df.set_index('exchange')['price'].to_dict()
        
        # Add exchange-specific prices
        for exchange in ['binance', 'coinbase', 'kraken', 'cryptocompare']:
            features.append(prices.get(exchange, np.nan))
        
        # Calculate spreads between exchanges
        if 'binance' in prices and 'coinbase' in prices:
            spread_bc = ((prices['binance'] - prices['coinbase']) / prices['binance']) * 100
            features.append(spread_bc)
        else:
            features.append(np.nan)
        
        if 'binance' in prices and 'kraken' in prices:
            spread_bk = ((prices['binance'] - prices['kraken']) / prices['binance']) * 100
            features.append(spread_bk)
        else:
            features.append(np.nan)
        
        if 'binance' in prices and 'cryptocompare' in prices:
            spread_bcr = ((prices['binance'] - prices['cryptocompare']) / prices['binance']) * 100
            features.append(spread_bcr)
        else:
            features.append(np.nan)
        
        # Add lag and volatility features (simplified - use zeros if no historical data)
        if historical_df is not None and len(historical_df) > 5:
            for exchange in ['binance', 'coinbase', 'kraken', 'cryptocompare']:
                ex_data = historical_df[historical_df['exchange'] == exchange]['price'].values
                if len(ex_data) > 5:
                    features.extend([
                        ex_data[-1],  # lag_1
                        ex_data[-5] if len(ex_data) >= 5 else ex_data[0],  # lag_5
                        ex_data[-5:].std() if len(ex_data) >= 5 else 0  # volatility
                    ])
                else:
                    features.extend([np.nan, np.nan, np.nan])
        else:
            # Add placeholder features (3 per exchange: lag_1, lag_5, volatility)
            features.extend([np.nan] * 12)
        
        return np.array(features).reshape(1, -1)
    
    def predict_opportunity(self, pair: str, current_prices: pd.DataFrame,
                          threshold: float = 0.1, horizon: int = 1,
                          model_type: str = 'xgb') -> Dict:
        """
        Predict if an arbitrage opportunity is viable
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            current_prices: Current price DataFrame
            threshold: Spread threshold percentage
            horizon: Prediction horizon in minutes
            model_type: Model type to use ('xgb', 'rf', 'lstm')
            
        Returns:
            Prediction dictionary with confidence and reasoning
        """
        pair_key = pair.replace('/', '_').lower()
        model_key = f"{model_type}_{pair_key}_{threshold}pct_{horizon}min"
        
        # Check if model exists
        if model_key not in self.models:
            # Try without threshold if exact model not found
            model_key_alt = f"{model_type}_{pair_key}_{horizon}min"
            if model_key_alt in self.models:
                model_key = model_key_alt
            else:
                # No ML model available - use heuristic prediction
                print(f"    ℹ️  No ML model for {pair} - using heuristic prediction")
                return self._heuristic_prediction(current_prices, threshold)
        
        try:
            # Prepare features
            features = self.prepare_features(current_prices)
            
            # Handle NaN values
            if np.isnan(features).any():
                # Fill NaN with 0 for prediction (not ideal, but allows inference)
                features = np.nan_to_num(features, nan=0.0)
            
            # Get model
            model = self.models[model_key]
            
            # Make prediction
            if model_type == 'lstm' and TENSORFLOW_AVAILABLE:
                # LSTM expects 3D input: (batch, timesteps, features)
                # For simplicity, we'll skip LSTM real-time prediction
                return {
                    'predicted': None,
                    'confidence': 0.0,
                    'model_used': model_key,
                    'reason': 'LSTM requires sequential data - use XGBoost/RF for real-time'
                }
            else:
                # XGBoost or Random Forest (binary classification)
                prediction = model.predict(features)[0]
                
                # Get probability if available
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(features)[0]
                    confidence = proba[1] if prediction == 1 else proba[0]
                else:
                    confidence = 0.8 if prediction == 1 else 0.2
                
                result = {
                    'predicted': bool(prediction),
                    'confidence': float(confidence),
                    'model_used': model_key,
                    'model_type': model_type.upper(),
                    'prediction_time': datetime.now(),
                    'pair': pair,
                    'threshold': threshold,
                    'horizon_minutes': horizon
                }
                
                self.prediction_history.append(result)
                return result
                
        except Exception as e:
            return {
                'predicted': None,
                'confidence': 0.0,
                'model_used': model_key,
                'reason': f'Prediction error: {str(e)}'
            }
    
    def predict_with_ensemble(self, pair: str, current_prices: pd.DataFrame,
                            threshold: float = 0.1, horizon: int = 1) -> Dict:
        """
        Use ensemble of models for more robust prediction
        
        Args:
            pair: Trading pair
            current_prices: Current price DataFrame
            threshold: Spread threshold
            horizon: Prediction horizon
            
        Returns:
            Ensemble prediction with aggregated confidence
        """
        predictions = []
        
        for model_type in ['xgb', 'rf']:
            pred = self.predict_opportunity(pair, current_prices, threshold, horizon, model_type)
            if pred['predicted'] is not None:
                predictions.append(pred)
        
        if not predictions:
            return {
                'predicted': None,
                'confidence': 0.0,
                'reason': 'No models available for ensemble'
            }
        
        # Aggregate predictions
        votes = sum([1 if p['predicted'] else 0 for p in predictions])
        avg_confidence = np.mean([p['confidence'] for p in predictions])
        
        ensemble_result = {
            'predicted': votes > len(predictions) / 2,
            'confidence': avg_confidence,
            'ensemble_size': len(predictions),
            'votes_positive': votes,
            'individual_predictions': predictions,
            'prediction_time': datetime.now()
        }
        
        return ensemble_result
    
    def analyze_prediction(self, prediction: Dict, opportunity: Dict) -> str:
        """
        Generate natural language analysis of prediction
        
        Args:
            prediction: Prediction dictionary
            opportunity: Opportunity dictionary from AnalysisAgent
            
        Returns:
            String with prediction analysis
        """
        if prediction['predicted'] is None:
            return f"""
Prediction Analysis: Unable to Predict
Reason: {prediction.get('reason', 'Unknown')}
Available models: {prediction.get('available_models', [])}
"""
        
        verdict = "VIABLE" if prediction['predicted'] else "NOT VIABLE"
        confidence_pct = prediction['confidence'] * 100
        
        analysis = f"""
🔮 PREDICTION ANALYSIS

Model: {prediction.get('model_type', 'Ensemble')} ({prediction['model_used']})
Prediction: {verdict}
Confidence: {confidence_pct:.1f}%
Horizon: {prediction.get('horizon_minutes', '?')} minutes

Opportunity Details:
- Pair: {opportunity.get('pair', 'Unknown')}
- Current Spread: {opportunity.get('net_spread_pct', 0):.3f}%
- Buy: {opportunity.get('buy_exchange', '?')} @ ${opportunity.get('buy_price', 0):,.2f}
- Sell: {opportunity.get('sell_exchange', '?')} @ ${opportunity.get('sell_price', 0):,.2f}

Recommendation:
"""
        
        if prediction['predicted'] and confidence_pct >= 70:
            analysis += "✓ STRONG BUY SIGNAL - High confidence opportunity"
        elif prediction['predicted'] and confidence_pct >= 50:
            analysis += "⚠ MODERATE BUY SIGNAL - Proceed with caution"
        else:
            analysis += "✗ HOLD - Low confidence or unfavorable prediction"
        
        return analysis.strip()
    
    def get_model_info(self) -> str:
        """Get information about loaded models"""
        info = f"""
Loaded Models Summary
=====================
Total Models: {len(self.models)}

Available Models:
"""
        for name in sorted(self.models.keys()):
            model_type = 'LSTM' if 'lstm' in name else 'XGBoost' if 'xgb' in name else 'Random Forest'
            info += f"- {name} ({model_type})\n"
        
        return info.strip()
    
    def _heuristic_prediction(self, current_prices: pd.DataFrame, threshold: float) -> Dict:
        """
        Heuristic prediction when ML models not available
        Uses price volatility and spread consistency for prediction
        
        Args:
            current_prices: Current price DataFrame
            threshold: Spread threshold
            
        Returns:
            Prediction dictionary
        """
        try:
            prices = current_prices['price'].values
            
            # Calculate basic statistics
            price_std = np.std(prices)
            price_mean = np.mean(prices)
            price_cv = price_std / price_mean  # Coefficient of variation
            
            # Calculate spread
            spread_pct = ((np.max(prices) - np.min(prices)) / np.min(prices)) * 100
            
            # Heuristic rules:
            # 1. Higher spread is better
            # 2. Lower volatility (CV) is better (more stable opportunity)
            # 3. Must exceed threshold significantly for high confidence
            
            confidence = 0.5  # Base confidence
            predicted = False
            
            if spread_pct > threshold * 1.5:
                # Spread is 50% above threshold
                predicted = True
                confidence = min(0.8, 0.5 + (spread_pct / threshold) * 0.1)
            elif spread_pct > threshold:
                # Marginal spread
                predicted = True
                confidence = 0.6
            
            # Adjust for volatility
            if price_cv < 0.001:  # Very stable prices
                confidence += 0.1
            
            return {
                'predicted': predicted,
                'confidence': min(confidence, 0.85),  # Cap at 0.85 for heuristic
                'model_used': 'heuristic',
                'model_type': 'RULE_BASED',
                'prediction_time': datetime.now(),
                'spread_pct': spread_pct,
                'price_volatility': price_cv,
                'reason': 'No ML model available - using heuristic rules'
            }
        except Exception as e:
            return {
                'predicted': False,
                'confidence': 0.0,
                'model_used': 'heuristic',
                'reason': f'Heuristic prediction failed: {str(e)}'
            }


# Test function
def test_prediction_agent():
    """Test the Prediction Agent"""
    import pandas as pd
    
    print("\n" + "="*80)
    print("TEST: Prediction Agent")
    print("="*80)
    
    agent = PredictionAgent()
    
    # Show loaded models
    print("\n" + agent.get_model_info())
    
    # Sample price data
    sample_data = pd.DataFrame([
        {'exchange': 'binance', 'pair': 'BTC/USDT', 'price': 100000, 'timestamp': datetime.now()},
        {'exchange': 'coinbase', 'pair': 'BTC/USDT', 'price': 100500, 'timestamp': datetime.now()},
        {'exchange': 'kraken', 'pair': 'BTC/USDT', 'price': 100200, 'timestamp': datetime.now()},
    ])
    
    # Test prediction
    print("\n" + "="*80)
    print("Testing Prediction:")
    print("="*80)
    prediction = agent.predict_opportunity('BTC/USDT', sample_data, threshold=0.2, horizon=1)
    print(prediction)


if __name__ == "__main__":
    test_prediction_agent()
