"""
Utility functions for the Arbitrage Agentic AI System
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def calculate_roi(buy_price: float, sell_price: float, 
                 amount: float, fee_rate: float = 0.001) -> float:
    """
    Calculate ROI for an arbitrage trade
    
    Args:
        buy_price: Buy price per unit
        sell_price: Sell price per unit
        amount: Amount to trade
        fee_rate: Trading fee rate
        
    Returns:
        ROI as percentage
    """
    buy_cost = buy_price * amount * (1 + fee_rate)
    sell_proceeds = sell_price * amount * (1 - fee_rate)
    profit = sell_proceeds - buy_cost
    roi = (profit / buy_cost) * 100
    return roi


def format_currency(amount: float, decimals: int = 2) -> str:
    """Format currency with commas and decimals"""
    return f"${amount:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with % sign"""
    return f"{value:.{decimals}f}%"


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for a series of returns
    
    Args:
        returns: List of return percentages
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        Sharpe ratio
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
    
    if returns_array.std() == 0:
        return 0.0
    
    sharpe = excess_returns.mean() / returns_array.std()
    return sharpe * np.sqrt(252)  # Annualized


def calculate_max_drawdown(portfolio_values: List[float]) -> float:
    """
    Calculate maximum drawdown from portfolio values
    
    Args:
        portfolio_values: List of portfolio values over time
        
    Returns:
        Maximum drawdown as percentage
    """
    if not portfolio_values or len(portfolio_values) < 2:
        return 0.0
    
    values = np.array(portfolio_values)
    cummax = np.maximum.accumulate(values)
    drawdown = (values - cummax) / cummax
    max_dd = drawdown.min() * 100
    
    return max_dd


def load_historical_features(pair: str, data_dir: str = 'data') -> pd.DataFrame:
    """
    Load historical features for a trading pair
    
    Args:
        pair: Trading pair (e.g., 'BTC/USDT')
        data_dir: Directory containing data files
        
    Returns:
        DataFrame with features
    """
    filename = f"{data_dir}/{pair.replace('/', '_').lower()}_features.csv"
    try:
        df = pd.read_csv(filename, parse_dates=['timestamp'])
        return df
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return pd.DataFrame()


def save_results(results: Dict, filename: str = 'results.json'):
    """
    Save results to JSON file
    
    Args:
        results: Dictionary with results
        filename: Output filename
    """
    import json
    from datetime import datetime
    
    # Convert datetime objects to strings
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    with open(filename, 'w') as f:
        json.dump(results, f, default=convert_datetime, indent=2)
    
    print(f"Results saved to {filename}")


def create_trade_log(trades: List[Dict], filename: str = 'trade_log.csv'):
    """
    Create a CSV log of trades
    
    Args:
        trades: List of trade dictionaries
        filename: Output filename
    """
    if not trades:
        print("No trades to log")
        return
    
    df = pd.DataFrame(trades)
    df.to_csv(filename, index=False)
    print(f"Trade log saved to {filename}")


def get_timestamp() -> str:
    """Get current timestamp as formatted string"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def validate_price_data(df: pd.DataFrame) -> bool:
    """
    Validate price data DataFrame
    
    Args:
        df: Price DataFrame
        
    Returns:
        True if valid, False otherwise
    """
    required_cols = ['exchange', 'price']
    
    if df.empty:
        print("Error: Empty DataFrame")
        return False
    
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Missing required column '{col}'")
            return False
    
    if df['price'].isna().any():
        print("Warning: NaN values in price data")
        return False
    
    return True


class PerformanceTracker:
    """Track and analyze performance metrics"""
    
    def __init__(self):
        self.metrics = []
    
    def add_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Add a performance metric"""
        self.metrics.append({
            'metric': metric_name,
            'value': value,
            'timestamp': timestamp or datetime.now()
        })
    
    def get_summary(self) -> pd.DataFrame:
        """Get summary of all metrics"""
        if not self.metrics:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.metrics)
        summary = df.groupby('metric')['value'].agg(['mean', 'std', 'min', 'max', 'count'])
        return summary
    
    def export_to_csv(self, filename: str = 'performance_metrics.csv'):
        """Export metrics to CSV"""
        if not self.metrics:
            print("No metrics to export")
            return
        
        df = pd.DataFrame(self.metrics)
        df.to_csv(filename, index=False)
        print(f"Metrics exported to {filename}")


def print_banner(text: str, char: str = "=", width: int = 80):
    """Print a formatted banner"""
    print(char * width)
    print(text.center(width))
    print(char * width)


def estimate_gas_fees(exchange: str, network: str = 'ethereum') -> float:
    """
    Estimate gas fees for blockchain transactions
    
    Args:
        exchange: Exchange name
        network: Blockchain network
        
    Returns:
        Estimated fee in USD
    """
    # Simplified - in production would query real-time gas prices
    base_fees = {
        'ethereum': 5.0,
        'binance_smart_chain': 0.50,
        'polygon': 0.10
    }
    
    return base_fees.get(network.lower(), 1.0)


def check_exchange_status(exchange: str) -> Dict:
    """
    Check if exchange is operational
    
    Args:
        exchange: Exchange name
        
    Returns:
        Status dictionary
    """
    # Simplified - in production would query exchange status APIs
    return {
        'exchange': exchange,
        'operational': True,
        'latency_ms': 100,
        'last_check': datetime.now()
    }
