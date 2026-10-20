# config.py
# API keys are read from environment variables (or a local .env file).
# Copy .env.example to .env and fill in your own keys. Never commit .env.
# All keys are optional: public market data works without them.
import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass


def _env(name):
    """Read a key from the environment, ignoring empty or placeholder values."""
    value = os.getenv(name, '').strip()
    return '' if value.startswith('your_') else value


EXCHANGES = {
    'binance': {'name': 'binance', 'apiKey': _env('BINANCE_API_KEY'), 'secret': _env('BINANCE_SECRET')},
    'coinbase': {'name': 'coinbase', 'apiKey': _env('COINBASE_API_KEY'), 'secret': _env('COINBASE_SECRET')},
    'kraken': {'name': 'kraken', 'apiKey': _env('KRAKEN_API_KEY'), 'secret': _env('KRAKEN_SECRET')},
    'cryptocompare': {'name': 'cryptocompare', 'apiKey': _env('CRYPTOCOMPARE_API_KEY'), 'secret': ''}
}
API_KEYS = {
    'coinmarketcap': _env('COINMARKETCAP_API_KEY'),
    'cryptocompare': _env('CRYPTOCOMPARE_API_KEY')
}

# Trading pairs to monitor
# Note: ML models only available for BTC/USDT and ETH/USDT
# Other pairs will work for arbitrage detection without ML predictions
PAIRS = [
    'BTC/USDT',   # Bitcoin - ML models available
    'ETH/USDT',   # Ethereum - ML models available
    'SOL/USDT',   # Solana
    'XRP/USDT',   # Ripple
    'ADA/USDT',   # Cardano
    'DOGE/USDT',  # Dogecoin
    'MATIC/USDT', # Polygon
    'DOT/USDT',   # Polkadot
    'AVAX/USDT',  # Avalanche
    'LINK/USDT',  # Chainlink
    'UNI/USDT',   # Uniswap
    'ATOM/USDT',  # Cosmos
]

DAYS = 7  # 7 days of data

# Historical data pipeline (data/fetch_*.py)
# Pairs used for model training
ML_PAIRS = ['BTC/USDT', 'ETH/USDT']
# Collection window in UTC (IST 2025-10-20 19:28 to 2025-10-25 15:12).
# This is the window the shipped datasets and models were built from.
DATA_START = '2025-10-20 13:58:00'
DATA_END = '2025-10-25 09:42:00'
