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

EXCHANGES = {
    'binance': {'name': 'binance', 'apiKey': os.getenv('BINANCE_API_KEY', ''), 'secret': os.getenv('BINANCE_SECRET', '')},
    'coinbase': {'name': 'coinbase', 'apiKey': os.getenv('COINBASE_API_KEY', ''), 'secret': os.getenv('COINBASE_SECRET', '')},
    'kraken': {'name': 'kraken', 'apiKey': os.getenv('KRAKEN_API_KEY', ''), 'secret': os.getenv('KRAKEN_SECRET', '')},
    'cryptocompare': {'name': 'cryptocompare', 'apiKey': os.getenv('CRYPTOCOMPARE_API_KEY', ''), 'secret': ''}
}
API_KEYS = {
    'coinmarketcap': os.getenv('COINMARKETCAP_API_KEY', ''),
    'cryptocompare': os.getenv('CRYPTOCOMPARE_API_KEY', '')
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
