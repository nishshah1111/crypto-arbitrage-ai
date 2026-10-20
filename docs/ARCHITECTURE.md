# System Architecture Diagram

## 🏗️ Multi-Agent Agentic AI Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         ORCHESTRATOR (main.py)                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Coordinates all agents                                             │ │
│  │  • Manages workflow                                                   │ │
│  │  • Handles errors and retries                                         │ │
│  │  • Tracks performance                                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└──────────────┬──────────────┬──────────────┬──────────────┬───────────────┘
               │              │              │              │
               ▼              ▼              ▼              ▼
       
┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   PERCEPTION  │  │   ANALYSIS    │  │  PREDICTION   │  │   DECISION    │
│     AGENT     │─▶│     AGENT     │─▶│     AGENT     │─▶│     AGENT     │
└───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘
│                  │                  │                  │
│ • Fetch prices  │ • Detect arb    │ • Load ML       │ • Assess risk
│ • Monitor APIs  │ • Calc spreads  │   models        │ • Risk scoring
│ • Track data    │ • Filter by     │ • Feature eng   │ • Position size
│ • Real-time     │   threshold     │ • Predict       │ • Make decision
│   updates       │ • Track opps    │ • Confidence    │
│                  │                  │                  │
▼                  ▼                  ▼                  ▼

    EXCHANGE          SPREADS         ML MODELS         RISK RULES
  ┌──────────┐     ┌──────────┐    ┌──────────┐     ┌──────────┐
  │ Binance  │     │ Binance- │    │ LSTM     │     │ Spread   │
  │ Coinbase │     │ Coinbase │    │ XGBoost  │     │ Volatil. │
  │ Kraken   │     │ Binance- │    │ Rand For │     │ Confid.  │
  └──────────┘     │ Kraken   │    └──────────┘     │ Exchange │
                   └──────────┘                      └──────────┘

                                           │
                                           ▼
                                   ┌───────────────┐
                                   │   EXECUTION   │
                                   │     AGENT     │
                                   └───────────────┘
                                   │
                                   │ • Simulate trade
                                   │ • Update portfolio
                                   │ • Track P&L
                                   │ • Fees/slippage
                                   │ • Generate reports
                                   │
                                   ▼
                            ┌──────────────┐
                            │  PORTFOLIO   │
                            ├──────────────┤
                            │ USDT: $10,000│
                            │ BTC:  0.05   │
                            │ ETH:  0.00   │
                            └──────────────┘
```

## 🔄 Data Flow

```
1. PERCEPTION PHASE
   ┌─────────────────────────────────────────────┐
   │ Fetch prices from Binance, Coinbase, Kraken│
   │ Current Price: BTC/USDT                     │
   │ - Binance:  $100,000                        │
   │ - Coinbase: $100,500                        │
   │ - Kraken:   $100,200                        │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
2. ANALYSIS PHASE
   ┌─────────────────────────────────────────────┐
   │ Calculate spreads and detect arbitrage     │
   │ Gross Spread: 0.50%                        │
   │ Less Fees:    -0.02%                       │
   │ Net Spread:   0.48%                        │
   │ ✓ OPPORTUNITY DETECTED                     │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
3. PREDICTION PHASE
   ┌─────────────────────────────────────────────┐
   │ Load ML model: xgb_btc_usdt_0.2pct_1min   │
   │ Extract features from price data           │
   │ Make prediction                            │
   │ Result: VIABLE (Confidence: 85%)           │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
4. DECISION PHASE
   ┌─────────────────────────────────────────────┐
   │ Assess risk factors:                       │
   │ - Spread: ✓ LOW RISK (0.48% > 0.3%)      │
   │ - Prediction: ✓ LOW RISK (85% > 60%)     │
   │ - Volatility: ✓ LOW RISK                 │
   │ Overall Risk: LOW (Score: 25/100)         │
   │ DECISION: EXECUTE                          │
   │ Position Size: 0.05 BTC                    │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
5. EXECUTION PHASE
   ┌─────────────────────────────────────────────┐
   │ Simulate Trade:                            │
   │ BUY:  0.05 BTC @ $100,000 = $5,000        │
   │ SELL: 0.05 BTC @ $100,500 = $5,025        │
   │ Fees: $10.05                               │
   │ Slippage: $2.50                            │
   │ Net Profit: $12.45                         │
   │ ROI: 0.25%                                 │
   │ ✓ TRADE EXECUTED SUCCESSFULLY              │
   └─────────────────────────────────────────────┘
```

## 🧠 Agent Autonomy Levels

```
LEVEL 1: REACTIVE
┌──────────────┐
│  Perception  │  - Responds to environment
│              │  - No memory
│              │  - Simple fetch operations
└──────────────┘

LEVEL 2: REASONING
┌──────────────┐
│   Analysis   │  - Calculates and compares
│  Prediction  │  - Uses historical data
│              │  - Makes predictions
└──────────────┘

LEVEL 3: AUTONOMOUS
┌──────────────┐
│   Decision   │  - Multi-factor reasoning
│  Execution   │  - Makes independent choices
│              │  - Learns from outcomes
└──────────────┘
```

## 🎯 Agentic AI Principles Applied

```
┌─────────────────────────────────────────────────────────────┐
│                   AGENTIC AI PRINCIPLES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PERCEPTION  ──▶  Agents sense environment              │
│     (Perception Agent fetches real-time prices)            │
│                                                             │
│  2. REASONING   ──▶  Agents analyze and plan               │
│     (Analysis + Prediction agents evaluate data)           │
│                                                             │
│  3. AUTONOMY    ──▶  Agents make decisions independently   │
│     (Decision agent chooses without human input)           │
│                                                             │
│  4. ACTION      ──▶  Agents execute plans                  │
│     (Execution agent simulates trades)                     │
│                                                             │
│  5. LEARNING    ──▶  Agents improve over time              │
│     (ML models trained on historical data)                 │
│                                                             │
│  6. COLLABORATION ──▶ Agents work together                 │
│     (Orchestrator coordinates agent workflow)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Risk Management Flow

```
                    ┌──────────────┐
                    │ Opportunity  │
                    │   Detected   │
                    └───────┬──────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Risk Factors │
                    └───────┬──────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Spread Risk  │   │Prediction Conf│   │ Volatility   │
│              │   │               │   │              │
│ Net spread   │   │ ML confidence │   │ Price        │
│ > threshold? │   │ > minimum?    │   │ stability?   │
└──────┬───────┘   └──────┬────────┘   └──────┬───────┘
       │                  │                    │
       └──────────────────┼────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Risk Score   │
                  │   (0-100)     │
                  └───────┬───────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
    LOW (0-30)      MEDIUM (31-60)   HIGH (61-100)
          │               │               │
          ▼               ▼               ▼
      EXECUTE         CAUTION            HOLD
```

## 📊 Performance Tracking

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION AGENT                          │
│                  Portfolio Management                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Initial Capital:  $10,000.00                              │
│                                                             │
│  ┌─────────────────────────────────────────────┐          │
│  │ Trade History                               │          │
│  ├─────────────────────────────────────────────┤          │
│  │ Trade 1: +$12.45 (0.25% ROI)  ✓           │          │
│  │ Trade 2: +$18.32 (0.37% ROI)  ✓           │          │
│  │ Trade 3: -$5.20  (-0.10% ROI) ✗           │          │
│  │ Trade 4: +$22.10 (0.44% ROI)  ✓           │          │
│  └─────────────────────────────────────────────┘          │
│                                                             │
│  Current Capital:  $10,047.67                              │
│  Total Profit:     $47.67                                  │
│  Total Return:     0.48%                                   │
│  Win Rate:         75%                                     │
│  Trades:           4                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Modes

```
MODE 1: DEMO
┌────────────────┐
│ Single Check   │  Quick test, no loop
│ Safe to run    │  Shows one complete cycle
└────────────────┘

MODE 2: SINGLE CYCLE
┌────────────────┐
│ One-time scan  │  All pairs, one time
│ Full report    │  Detailed output
└────────────────┘

MODE 3: CONTINUOUS
┌────────────────┐
│ 24/7 monitoring│  Runs indefinitely
│ Auto-execute*  │  Can enable trading
│ (*if enabled)  │  Real-time alerts
└────────────────┘

MODE 4: ADVANCED (LangChain)
┌────────────────┐
│ AI reasoning   │  Natural language
│ LLM-powered    │  Autonomous decisions
│ Conversational │  Advanced planning
└────────────────┘
```

---

## 🎓 For Your Presentation

Use this diagram to explain:

1. **Agent Architecture** - Show the 5 specialized agents
2. **Data Flow** - Walk through a complete cycle
3. **Autonomy** - Explain how agents make decisions independently
4. **Risk Management** - Demonstrate comprehensive risk assessment
5. **Performance** - Show tracking and reporting capabilities

This visual representation helps explain the complexity and sophistication of your agentic AI system!
