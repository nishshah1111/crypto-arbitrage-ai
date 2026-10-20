"""
Advanced Agentic AI Orchestrator with LangChain Integration
This version uses LangChain for more sophisticated agent reasoning and autonomy
"""

import sys
# Print emoji/check marks safely on Windows consoles that default to cp1252
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import os
import warnings
from datetime import datetime
from typing import Dict, List, Optional

warnings.filterwarnings("ignore")

# Import agents
from agents.perception import PerceptionAgent
from agents.analysis import AnalysisAgent
from agents.prediction import PredictionAgent
from agents.decision import DecisionAgent
from agents.execution import ExecutionAgent
from config import EXCHANGES, PAIRS, _env

# LangChain imports (optional - gracefully degrade if not available)
try:
    from langchain.agents import Tool, AgentExecutor, create_react_agent
    from langchain.prompts import PromptTemplate
    from langchain.memory import ConversationBufferMemory
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("Warning: LangChain not available. Using basic orchestration.")
    LANGCHAIN_AVAILABLE = False


class AdvancedAgenticOrchestrator:
    """
    Advanced orchestrator using LangChain for autonomous agent reasoning.
    Agents can make decisions based on natural language reasoning.
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 threshold: float = 0.2,
                 risk_tolerance: str = 'moderate',
                 initial_capital: float = 10000.0):
        """
        Initialize advanced orchestrator with LangChain
        
        Args:
            openai_api_key: OpenAI API key (optional)
            threshold: Minimum arbitrage spread
            risk_tolerance: Risk level
            initial_capital: Starting capital
        """
        self.threshold = threshold
        self.risk_tolerance = risk_tolerance
        self.initial_capital = initial_capital
        
        print("\n" + "="*80)
        print("🧠 INITIALIZING ADVANCED AGENTIC AI SYSTEM WITH LANGCHAIN")
        print("="*80)
        
        # Initialize core agents
        self.perception_agent = PerceptionAgent(EXCHANGES, PAIRS)
        self.analysis_agent = AnalysisAgent(threshold=threshold)
        self.prediction_agent = PredictionAgent()
        self.decision_agent = DecisionAgent(risk_tolerance=risk_tolerance)
        self.execution_agent = ExecutionAgent(initial_capital=initial_capital)
        
        # Initialize LangChain components if available
        if LANGCHAIN_AVAILABLE and openai_api_key:
            self._init_langchain(openai_api_key)
        else:
            self.langchain_enabled = False
            print("\n⚠ LangChain disabled. Using basic orchestration.")
            if not openai_api_key:
                print("   Set OPENAI_API_KEY environment variable to enable.")
    
    def _init_langchain(self, api_key: str):
        """Initialize LangChain components"""
        print("\n🧠 Initializing LangChain components...")
        
        try:
            # Initialize LLM
            self.llm = ChatOpenAI(
                temperature=0.3,
                model="gpt-3.5-turbo",
                openai_api_key=api_key
            )
            
            # Create memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Define tools for the agent
            self.tools = self._create_langchain_tools()
            
            # Create agent prompt
            self.agent_prompt = self._create_agent_prompt()
            
            # Create agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.agent_prompt
            )
            
            # Create executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
            
            self.langchain_enabled = True
            print("✓ LangChain enabled successfully")
            
        except Exception as e:
            print(f"✗ Failed to initialize LangChain: {e}")
            self.langchain_enabled = False
    
    def _create_langchain_tools(self) -> List[Tool]:
        """Create LangChain tools from our agents"""
        
        tools = [
            Tool(
                name="FetchPrices",
                func=lambda pair: self._tool_fetch_prices(pair),
                description="""
                Fetch current cryptocurrency prices from multiple exchanges.
                Input: Trading pair like 'BTC/USDT' or 'ETH/USDT'.
                Returns: Current prices and spread information.
                Use this when you need to check current market prices.
                """
            ),
            Tool(
                name="DetectArbitrage",
                func=lambda pair: self._tool_detect_arbitrage(pair),
                description="""
                Detect arbitrage opportunities for a trading pair.
                Input: Trading pair like 'BTC/USDT'.
                Returns: Information about arbitrage opportunity including spread, exchanges, and profitability.
                Use this to find price discrepancies between exchanges.
                """
            ),
            Tool(
                name="PredictViability",
                func=lambda pair: self._tool_predict_viability(pair),
                description="""
                Use machine learning to predict if an arbitrage opportunity is viable.
                Input: Trading pair like 'BTC/USDT'.
                Returns: Prediction confidence and viability assessment.
                Use this after detecting an opportunity to forecast its persistence.
                """
            ),
            Tool(
                name="AssessRisk",
                func=lambda pair: self._tool_assess_risk(pair),
                description="""
                Perform comprehensive risk assessment for a trading opportunity.
                Input: Trading pair like 'BTC/USDT'.
                Returns: Risk score, risk level, and detailed risk factors.
                Use this before making a trading decision.
                """
            ),
            Tool(
                name="GetPortfolioStatus",
                func=lambda _: self._tool_portfolio_status(),
                description="""
                Get current portfolio status including balances and performance.
                Input: Any string (ignored).
                Returns: Current capital, positions, and P&L.
                Use this to check available capital before trading.
                """
            )
        ]
        
        return tools
    
    def _create_agent_prompt(self) -> PromptTemplate:
        """Create prompt template for the agent"""
        
        template = """You are an expert cryptocurrency arbitrage trading AI agent. Your goal is to identify and evaluate profitable arbitrage opportunities while managing risk.

You have access to the following tools:
{tools}

Your workflow should be:
1. Fetch current prices for the trading pair
2. Detect if there's an arbitrage opportunity
3. If opportunity exists, predict its viability using ML models
4. Assess the risk of the trade
5. Check portfolio status to ensure sufficient capital
6. Make a reasoned decision whether to trade

Always consider:
- Minimum spread threshold: {threshold}%
- Risk tolerance: {risk_tolerance}
- Trading fees and slippage
- Market volatility
- Prediction confidence

Current pair to analyze: {input}

{agent_scratchpad}"""
        
        return PromptTemplate(
            input_variables=["tools", "input", "agent_scratchpad"],
            template=template,
            partial_variables={
                "threshold": str(self.threshold),
                "risk_tolerance": self.risk_tolerance
            }
        )
    
    # Tool implementation methods
    def _tool_fetch_prices(self, pair: str) -> str:
        """Fetch prices tool"""
        try:
            df = self.perception_agent.fetch_prices(pair)
            if df.empty:
                return f"No price data available for {pair}"
            
            result = f"Prices for {pair}:\n"
            for _, row in df.iterrows():
                result += f"- {row['exchange']}: ${row['price']:,.2f}\n"
            
            spread = ((df['price'].max() - df['price'].min()) / df['price'].min()) * 100
            result += f"Spread: {spread:.3f}%"
            
            return result
        except Exception as e:
            return f"Error fetching prices: {str(e)}"
    
    def _tool_detect_arbitrage(self, pair: str) -> str:
        """Detect arbitrage tool"""
        try:
            df = self.perception_agent.fetch_prices(pair)
            opportunity = self.analysis_agent.detect_arbitrage(df)
            
            if not opportunity['opportunity']:
                return f"No arbitrage opportunity for {pair}. Spread {opportunity.get('gross_spread_pct', 0):.3f}% below threshold."
            
            return f"""Arbitrage opportunity detected for {pair}:
- Buy: {opportunity['buy_exchange']} at ${opportunity['buy_price']:,.2f}
- Sell: {opportunity['sell_exchange']} at ${opportunity['sell_price']:,.2f}
- Net spread: {opportunity['net_spread_pct']:.3f}%
- Potential profit: ${(opportunity['sell_price'] - opportunity['buy_price']):,.2f} per unit"""
            
        except Exception as e:
            return f"Error detecting arbitrage: {str(e)}"
    
    def _tool_predict_viability(self, pair: str) -> str:
        """Predict viability tool"""
        try:
            df = self.perception_agent.fetch_prices(pair)
            prediction = self.prediction_agent.predict_opportunity(
                pair, df, threshold=self.threshold, horizon=1
            )
            
            if prediction['predicted'] is None:
                return f"Unable to predict: {prediction.get('reason', 'Unknown')}"
            
            verdict = "VIABLE" if prediction['predicted'] else "NOT VIABLE"
            confidence = prediction['confidence'] * 100
            
            return f"""Prediction for {pair}:
- Verdict: {verdict}
- Confidence: {confidence:.1f}%
- Model: {prediction.get('model_type', 'Unknown')}
- Recommendation: {'Trade' if confidence > 70 else 'Hold'}"""
            
        except Exception as e:
            return f"Error predicting: {str(e)}"
    
    def _tool_assess_risk(self, pair: str) -> str:
        """Assess risk tool"""
        try:
            # Get current data
            df = self.perception_agent.fetch_prices(pair)
            opportunity = self.analysis_agent.detect_arbitrage(df)
            prediction = self.prediction_agent.predict_opportunity(pair, df)
            
            # Assess risk
            risk = self.decision_agent.assess_risk(opportunity, prediction)
            
            return f"""Risk assessment for {pair}:
- Risk Level: {risk['risk_level']}
- Risk Score: {risk['risk_score']}/100
- Risk Tolerance: {risk['risk_tolerance'].upper()}

Key Factors:
{self._format_risk_factors(risk['risk_factors'])}"""
            
        except Exception as e:
            return f"Error assessing risk: {str(e)}"
    
    def _tool_portfolio_status(self) -> str:
        """Portfolio status tool"""
        try:
            summary = self.execution_agent.get_performance_summary()
            
            if summary.get('total_trades', 0) == 0:
                return f"""Portfolio Status:
- Capital: ${summary.get('initial_capital', 0):,.2f}
- No trades executed yet"""
            
            return f"""Portfolio Status:
- Current Value: ${summary['current_value']:,.2f}
- Total P&L: ${summary['total_profit']:,.2f} ({summary['total_return_pct']:.2f}%)
- Trades: {summary['total_trades']}
- Win Rate: {summary['win_rate']:.1f}%
- Average Profit: ${summary['avg_profit_per_trade']:.2f}"""
            
        except Exception as e:
            return f"Error getting portfolio: {str(e)}"
    
    def _format_risk_factors(self, factors: Dict) -> str:
        """Format risk factors for display"""
        result = ""
        for factor, details in factors.items():
            status = details.get('status', 'UNKNOWN')
            reason = details.get('reason', 'No details')
            result += f"- {factor.upper()}: {status} - {reason}\n"
        return result.strip()
    
    def run_with_langchain(self, pair: str) -> str:
        """Run analysis using LangChain agent"""
        if not self.langchain_enabled:
            return "LangChain not enabled. Use basic orchestration instead."
        
        print(f"\n{'='*80}")
        print(f"🧠 LANGCHAIN AGENT ANALYSIS: {pair}")
        print(f"{'='*80}\n")
        
        try:
            result = self.agent_executor.invoke({
                "input": f"Analyze the arbitrage opportunity for {pair} and make a trading recommendation."
            })
            
            return result['output']
            
        except Exception as e:
            return f"Error running LangChain agent: {str(e)}"
    
    def run_basic(self, pair: str) -> Dict:
        """Run basic orchestration (without LangChain)"""
        print(f"\n{'='*80}")
        print(f"🤖 BASIC AGENT ANALYSIS: {pair}")
        print(f"{'='*80}\n")
        
        # Standard workflow
        prices = self.perception_agent.fetch_prices(pair)
        opportunity = self.analysis_agent.detect_arbitrage(prices)
        
        if not opportunity['opportunity']:
            return {
                'pair': pair,
                'opportunity': False,
                'reason': 'No arbitrage opportunity'
            }
        
        prediction = self.prediction_agent.predict_opportunity(pair, prices)
        decision = self.decision_agent.make_decision(opportunity, prediction)
        
        return {
            'pair': pair,
            'opportunity': opportunity,
            'prediction': prediction,
            'decision': decision
        }


def main():
    """Main function to demonstrate advanced orchestrator"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║           🧠 ADVANCED AGENTIC AI ARBITRAGE SYSTEM 🧠                         ║
║                    With LangChain Integration                                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Check for OpenAI API key
    api_key = _env('OPENAI_API_KEY') or None
    
    # Initialize orchestrator
    orchestrator = AdvancedAgenticOrchestrator(
        openai_api_key=api_key,
        threshold=0.2,
        risk_tolerance='moderate',
        initial_capital=10000.0
    )
    
    # Run analysis
    pair = PAIRS[0]  # BTC/USDT
    
    if orchestrator.langchain_enabled:
        print("\n🧠 Running LangChain-powered agent...")
        result = orchestrator.run_with_langchain(pair)
        print("\n" + "="*80)
        print("LANGCHAIN AGENT OUTPUT:")
        print("="*80)
        print(result)
    else:
        print("\n🤖 Running basic orchestration...")
        result = orchestrator.run_basic(pair)
        print("\n" + "="*80)
        print("BASIC ORCHESTRATION OUTPUT:")
        print("="*80)
        print(f"Decision: {result.get('decision', {}).get('action', 'N/A')}")
        print(f"Reason: {result.get('decision', {}).get('reason', 'N/A')}")


if __name__ == "__main__":
    main()
