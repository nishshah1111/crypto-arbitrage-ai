"""
Perception Agent - Real-time Price Fetching
Monitors exchanges and collects current price data
"""

import ccxt
import pandas as pd
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
import warnings

warnings.filterwarnings("ignore")


class PerceptionAgent:
    """
    Autonomous agent for perceiving the crypto market environment.
    Fetches real-time prices from multiple exchanges.
    """
    
    def __init__(self, exchanges_config: Dict, pairs: List[str]):
        """
        Initialize the Perception Agent
        
        Args:
            exchanges_config: Dictionary with exchange credentials
            pairs: List of trading pairs to monitor (e.g., ['BTC/USDT'])
        """
        self.exchanges_config = exchanges_config
        self.pairs = pairs
        self.exchanges = {}
        self.last_prices = {}
        self.cryptocompare_api_key = None
        
        # Initialize exchange connections
        self._init_exchanges()
        
    def _init_exchanges(self):
        """Initialize connections to exchanges"""
        for exchange_name, config in self.exchanges_config.items():
            try:
                if exchange_name == 'binance':
                    self.exchanges[exchange_name] = ccxt.binance({
                        'enableRateLimit': True,
                        'apiKey': config.get('apiKey', ''),
                        'secret': config.get('secret', '')
                    })
                elif exchange_name == 'coinbase':
                    self.exchanges[exchange_name] = ccxt.coinbase({
                        'enableRateLimit': True,
                        'apiKey': config.get('apiKey', ''),
                        'secret': config.get('secret', '')
                    })
                elif exchange_name == 'kraken':
                    self.exchanges[exchange_name] = ccxt.kraken({
                        'enableRateLimit': True,
                        'apiKey': config.get('apiKey', ''),
                        'secret': config.get('secret', '')
                    })
                elif exchange_name == 'cryptocompare':
                    # CryptoCompare is a data provider, not an exchange
                    # Store API key for later use
                    self.cryptocompare_api_key = config.get('apiKey', '')
                    print(f"✓ Connected to {exchange_name} (data provider)")
                    continue
                print(f"✓ Connected to {exchange_name}")
            except Exception as e:
                print(f"✗ Failed to connect to {exchange_name}: {e}")
    
    def fetch_prices(self, pair: str) -> pd.DataFrame:
        """
        Fetch current prices for a specific pair from all exchanges
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            DataFrame with columns: exchange, price, timestamp, volume
        """
        prices = []
        timestamp = datetime.now()
        
        # Fetch from regular exchanges (CCXT)
        for exchange_name, exchange in self.exchanges.items():
            try:
                ticker = exchange.fetch_ticker(pair)
                prices.append({
                    'exchange': exchange_name,
                    'pair': pair,
                    'price': ticker['last'],
                    'bid': ticker.get('bid', ticker['last']),
                    'ask': ticker.get('ask', ticker['last']),
                    'volume': ticker.get('volume', 0),
                    'timestamp': timestamp
                })
                print(f"  {exchange_name}: ${ticker['last']:,.2f}")
            except Exception as e:
                print(f"  ✗ Error fetching {pair} from {exchange_name}: {e}")
        
        # Fetch from CryptoCompare (direct API)
        if self.cryptocompare_api_key:
            try:
                cc_price = self._fetch_cryptocompare_price(pair)
                if cc_price:
                    prices.append(cc_price)
                    print(f"  cryptocompare: ${cc_price['price']:,.2f}")
            except Exception as e:
                print(f"  ✗ Error fetching {pair} from cryptocompare: {e}")
        
        df = pd.DataFrame(prices)
        self.last_prices[pair] = df
        return df
    
    def _fetch_cryptocompare_price(self, pair: str) -> Optional[Dict]:
        """
        Fetch price from CryptoCompare API
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            
        Returns:
            Price data dictionary or None if failed
        """
        try:
            # Parse pair (e.g., 'BTC/USDT' -> from='BTC', to='USDT')
            from_symbol, to_symbol = pair.split('/')
            
            # CryptoCompare API endpoint
            url = f"https://min-api.cryptocompare.com/data/price"
            params = {
                'fsym': from_symbol,
                'tsyms': to_symbol,
                'api_key': self.cryptocompare_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if to_symbol in data:
                    price = data[to_symbol]
                    return {
                        'exchange': 'cryptocompare',
                        'pair': pair,
                        'price': price,
                        'bid': price,  # CryptoCompare doesn't provide bid/ask
                        'ask': price,
                        'volume': 0,
                        'timestamp': datetime.now()
                    }
            return None
        except Exception as e:
            print(f"  CryptoCompare API error: {e}")
            return None
    
    def fetch_all_pairs(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch prices for all configured pairs
        
        Returns:
            Dictionary mapping pair -> DataFrame
        """
        results = {}
        print(f"\n🔍 Perception Agent: Fetching prices at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for pair in self.pairs:
            print(f"\n{pair}:")
            results[pair] = self.fetch_prices(pair)
            time.sleep(1)  # Rate limiting
        
        return results
    
    def get_price_history(self, pair: str, exchange: str, 
                         timeframe: str = '1m', limit: int = 100) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for building features
        
        Args:
            pair: Trading pair
            exchange: Exchange name
            timeframe: Candle timeframe (1m, 5m, etc.)
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        if exchange not in self.exchanges:
            raise ValueError(f"Exchange {exchange} not initialized")
        
        try:
            ohlcv = self.exchanges[exchange].fetch_ohlcv(pair, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['exchange'] = exchange
            df['pair'] = pair
            return df
        except Exception as e:
            print(f"Error fetching history from {exchange}: {e}")
            return pd.DataFrame()
    
    def monitor_continuous(self, interval: int = 10, callback=None):
        """
        Continuously monitor prices at specified interval
        
        Args:
            interval: Seconds between updates
            callback: Optional function to call with results
        """
        print(f"\n🤖 Starting continuous monitoring (every {interval}s)...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                results = self.fetch_all_pairs()
                
                if callback:
                    callback(results)
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n⏹ Monitoring stopped by user")
    
    def perceive(self, pair: str) -> str:
        """
        High-level perception method for agentic workflow
        Returns natural language description of current market state
        
        Args:
            pair: Trading pair to perceive
            
        Returns:
            String description of market state
        """
        df = self.fetch_prices(pair)
        
        if df.empty:
            return f"Unable to perceive {pair} - no data available"
        
        prices = df.set_index('exchange')['price'].to_dict()
        min_price = df['price'].min()
        max_price = df['price'].max()
        spread_pct = ((max_price - min_price) / min_price) * 100
        
        min_exchange = df.loc[df['price'].idxmin(), 'exchange']
        max_exchange = df.loc[df['price'].idxmax(), 'exchange']
        
        perception = f"""
Market Perception for {pair}:
- Prices: {', '.join([f'{ex}: ${p:,.2f}' for ex, p in prices.items()])}
- Spread: {spread_pct:.3f}% (${max_price - min_price:,.2f})
- Lowest: {min_exchange} at ${min_price:,.2f}
- Highest: {max_exchange} at ${max_price:,.2f}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return perception.strip()


# Test function
def test_perception_agent():
    """Test the Perception Agent"""
    from config import EXCHANGES, PAIRS
    
    agent = PerceptionAgent(EXCHANGES, PAIRS)
    
    # Test single fetch
    print("\n" + "="*80)
    print("TEST: Single Price Fetch")
    print("="*80)
    perception = agent.perceive('BTC/USDT')
    print(perception)
    
    # Test all pairs
    print("\n" + "="*80)
    print("TEST: All Pairs Fetch")
    print("="*80)
    results = agent.fetch_all_pairs()
    for pair, df in results.items():
        print(f"\n{pair}:")
        print(df.to_string(index=False))


if __name__ == "__main__":
    test_perception_agent()
