# Crypto Arbitrage AI — Agentic Arbitrage Detection & Prediction

A capstone project that detects and simulates **cross-exchange cryptocurrency arbitrage** in real time, using a team of five cooperating AI agents and machine-learning models (Random Forest, XGBoost, LSTM) trained on historical market data.

> ⚠️ **Educational project. Paper trading only.** No real orders are ever placed. Nothing here is financial advice.

---

## Features

- **Live prices** from Binance, Coinbase, Kraken and CryptoCompare (via [CCXT](https://github.com/ccxt/ccxt)) for 12 trading pairs
- **Five-agent pipeline**: Perception → Analysis → Prediction → Decision → Execution
- **81 pre-trained ML models** for BTC/USDT and ETH/USDT (RF, XGBoost, LSTM × spread thresholds 0.1/0.2/0.3/0.5% × horizons 1/3/5 min)
- **Rule-based fallback** for pairs without ML models
- **Risk-aware decisions** (conservative / moderate / aggressive) with position sizing
- **Paper-trading portfolio** with fees (0.1%) and slippage (0.05%), saved between runs
- **Web dashboard** (FastAPI + HTML) with auto-refresh, trade history and closed-opportunity tracking

## Architecture

```
               ┌──────────────────────────────────────────────┐
               │       api.py (FastAPI)  /  main.py (CLI)       │
               └──────────────────────────────────────────────┘
                                   │
 ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
 │ Perception │──▶│  Analysis  │──▶│ Prediction │──▶│  Decision  │──▶│ Execution  │
 │ live prices│   │  spreads & │   │ ML ensemble│   │ risk score │   │ paper trade│
 │ 4 sources  │   │ fee filter │   │ RF/XGB/LSTM│   │ & sizing   │   │ & portfolio│
 └────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details and [docs/AGENTIC_AI_COMPARISON.md](docs/AGENTIC_AI_COMPARISON.md) for how this differs from a rule-based bot.

## Quick start

**Requirements:** Python 3.10+ (tested on 3.13, Windows 11). Node.js only for the optional React frontend.

```bash
git clone https://github.com/<your-username>/crypto-arbitrage-ai.git
cd crypto-arbitrage-ai

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**API keys (optional):** live public prices work without any keys. To use your own:

```bash
cp .env.example .env      # Windows: copy .env.example .env
# then edit .env
```

### Run the dashboard

```bash
python api.py
```

Or double-click `START_SYSTEM.bat` on Windows. Wait for `Total models loaded: 81`, then open:

| URL | What |
|---|---|
| http://localhost:8000/dashboard | Dashboard |
| http://localhost:8000/docs | Interactive API docs (Swagger) |

Startup takes about 10 s (model loading). The first opportunity scan takes about 20 s while prices are fetched from every exchange. The dashboard then refreshes every 30 s.

### Other ways to run

| Command | Description |
|---|---|
| `python main.py` | CLI: single cycle, continuous monitoring, or demo mode |
| `python main_agentic.py` | CLI with goal-driven "cognitive cycle" agent loop |
| `python main_advanced.py` | LangChain reasoning (needs optional deps + `OPENAI_API_KEY`) |
| `python test_system.py` | Component tests for all agents |
| `python verify_prices.py` | Cross-check live prices between exchanges |
| `cd frontend && npm install && npm start` | Optional React frontend (talks to the API on port 8000) |

## Project structure

```
crypto-arbitrage-ai/
├── api.py                  # FastAPI backend + serves dashboard.html
├── dashboard.html          # Web dashboard
├── main.py                 # CLI orchestrator
├── main_agentic.py         # Agentic CLI orchestrator
├── main_advanced.py        # LangChain variant (optional)
├── config.py               # Pairs, exchanges, data window; keys from .env
├── agents/
│   ├── perception.py       # Fetch live prices (CCXT + CryptoCompare)
│   ├── analysis.py         # Spread calculation & opportunity detection
│   ├── prediction.py       # Load models, ensemble prediction, heuristic fallback
│   ├── decision.py         # Risk assessment & trade decisions
│   └── execution.py        # Paper trading, portfolio, persistence
├── data/                   # Historical datasets + data-pipeline scripts
├── models/                 # 81 trained models + training scripts
├── analysis/               # Validation, economic analysis, figure generation
├── results/                # Result tables used in the report (Chapter 4)
├── frontend/               # Optional React frontend
├── utils/helpers.py
└── docs/                   # Architecture, troubleshooting, frontend guide
```

## Data & models

### Dataset

- **Pairs:** BTC/USDT, ETH/USDT
- **Sources:** Binance, Coinbase, Kraken, CryptoCompare (1-minute candles)
- **Window:** 2025-10-20 13:58 to 2025-10-25 09:42 UTC (about 6,900 minutes per pair)
- **Features:** cross-exchange spreads, lagged prices (1 and 5 min), rolling volatility

### Live data vs. training data

| | Live? |
|---|---|
| Prices and opportunities on the dashboard | ✅ Fetched live from the exchanges on every refresh |
| Training data and models | ❌ Fixed historical snapshot (window above). Retraining is a manual offline step. |

Pairs other than BTC/USDT and ETH/USDT have no trained model and use rule-based heuristics. The dashboard labels these clearly.

### Rebuilding the dataset and retraining (optional)

Edit `DATA_START` / `DATA_END` (and `ML_PAIRS`) in `config.py`, then run from the project root:

```bash
# 1. Fetch raw 1-minute data
python data/fetch_binance.py
python data/fetch_coinbase.py
python data/fetch_kraken.py
python data/fetch_cryptocompare.py

# 2. Merge sources per pair
python data/merging_btc_usdt.py
python data/merging_etc_usdt.py     # ETH/USDT

# 3. Spreads and features
python data/compute_spreads.py
python data/add_features.py

# 4. Train (overwrites models/ and data/model_results.csv, so back them up first)
python models/train_simplified.py   # RF + XGBoost
python models/pred2.py              # full set incl. LSTM + Prophet (needs `pip install prophet`)
```

Fetching is rate-limited and can take a while. Training LSTMs on CPU takes longer still.

## Results

- Model metrics: [`data/model_results.csv`](data/model_results.csv)
- Report tables (1/3/5-minute horizons, trading simulation): [`results/`](results/)
- Paper-trading simulation (about 1 hour, $10,000 starting capital): **13 trades, 84.6% success rate, +1.27% ROI** after fees and slippage. See [`results/Table_4_4_Trading_Simulation_Results.csv`](results/Table_4_4_Trading_Simulation_Results.csv).

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/pairs`, `/api/exchanges` | Configured pairs / exchanges |
| GET | `/api/prices/all`, `/api/prices/{pair}` | Live prices |
| GET | `/api/opportunities` | Scan for opportunities with AI decision |
| GET | `/api/active-opportunities`, `/api/closed-opportunities` | Opportunity lifecycle |
| POST | `/api/execute-trade` | Execute a paper trade |
| GET | `/api/portfolio`, `/api/trades`, `/api/stats` | Portfolio & performance |
| WS | `/ws/live` | Live updates |

## Known limitations

- ML models exist only for **BTC/USDT and ETH/USDT**, trained on a **5-day window**. Their performance on today's market is not guaranteed.
- During live prediction, lag/volatility features are zero-filled because no price history is passed from the API. This is a known simplification.
- CryptoCompare is an aggregated index, not a tradable venue. Very large "spreads" against it (e.g. MATIC) are data artefacts, not real opportunities.
- Some pairs are not listed on every exchange (e.g. MATIC/USDT and UNI/USDT on Coinbase/Kraken). The console shows `✗ Error fetching ...` for these, and they are skipped.
- `analysis/economic_analysis.py` currently has a syntax error (damaged lines) and does not run. Its output is already saved in `data/economic_analysis_results.csv`.
- Trades are simulated. Real execution would face latency, withdrawal times and order-book depth that are not modelled.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md). Common fixes:

- **Port 8000 in use (Windows):** `netstat -ano | findstr :8000`, then `taskkill /PID <pid> /F`
- **`ModuleNotFoundError`:** activate the virtual environment and run `pip install -r requirements.txt`
- **Reset the paper portfolio:** stop the server and delete `portfolio_state.json`

## Disclaimer

This software is for education and research. It does not provide financial advice, and the authors accept no liability for any use of it. Cryptocurrency trading involves substantial risk of loss.
