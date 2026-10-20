"""
Main Orchestrator - Agentic AI Arbitrage System
Coordinates all agents using LangChain for autonomous operation
"""

import sys
# Print emoji/check marks safely on Windows consoles that default to cp1252
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
import warnings

warnings.filterwarnings("ignore")

# Import configuration
from config import EXCHANGES, PAIRS

# Import agents
from agents.perception import PerceptionAgent
from agents.analysis import AnalysisAgent
from agents.prediction import PredictionAgent
from agents.decision import DecisionAgent
from agents.execution import ExecutionAgent


class ArbitrageAgentOrchestrator:
    """
    Master orchestrator for the multi-agent arbitrage system.
    Coordinates autonomous agents to identify and execute arbitrage opportunities.
    """
    
    def __init__(self, 
                 threshold: float = 0.2,
                 risk_tolerance: str = 'moderate',
                 initial_capital: float = 10000.0,
                 auto_execute: bool = False):
        """
        Initialize the orchestrator with all agents
        
        Args:
            threshold: Minimum arbitrage spread threshold (%)
            risk_tolerance: 'conservative', 'moderate', or 'aggressive'
            initial_capital: Starting capital for trading simulation
            auto_execute: Whether to automatically execute trades (default: False for safety)
        """
        self.threshold = threshold
        self.risk_tolerance = risk_tolerance
        self.initial_capital = initial_capital
        self.auto_execute = auto_execute
        
        print("\n" + "="*80)
        print("🤖 INITIALIZING AGENTIC AI ARBITRAGE SYSTEM")
        print("="*80)
        
        # Initialize all agents
        print("\n1️⃣ Initializing Perception Agent...")
        self.perception_agent = PerceptionAgent(EXCHANGES, PAIRS)
        
        print("\n2️⃣ Initializing Analysis Agent...")
        self.analysis_agent = AnalysisAgent(threshold=threshold)
        
        print("\n3️⃣ Initializing Prediction Agent...")
        self.prediction_agent = PredictionAgent()
        
        print("\n4️⃣ Initializing Decision Agent...")
        self.decision_agent = DecisionAgent(
            risk_tolerance=risk_tolerance,
            max_position_size=1.0
        )
        
        print("\n5️⃣ Initializing Execution Agent...")
        self.execution_agent = ExecutionAgent(
            initial_capital=initial_capital
        )
        
        print("\n✓ All agents initialized successfully!")
        print("="*80)
        
        # Track opportunities
        self.opportunities_found = 0
        self.trades_executed = 0
        
    def run_single_cycle(self, pair: str, verbose: bool = True) -> Dict:
        """
        Run a single arbitrage detection cycle for one pair
        
        Args:
            pair: Trading pair to analyze (e.g., 'BTC/USDT')
            verbose: Whether to print detailed output
            
        Returns:
            Dictionary with cycle results
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"🔄 ARBITRAGE CYCLE: {pair}")
            print(f"{'='*80}")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: PERCEPTION - Fetch current prices
        if verbose:
            print("\n1️⃣ PERCEPTION: Fetching market data...")
        
        try:
            price_data = self.perception_agent.fetch_prices(pair)
            
            if price_data.empty:
                return {
                    'success': False,
                    'stage': 'perception',
                    'reason': 'No price data available'
                }
            
            if verbose:
                print(f"   ✓ Fetched prices from {len(price_data)} exchanges")
        
        except Exception as e:
            print(f"   ✗ Error in perception: {e}")
            return {'success': False, 'stage': 'perception', 'error': str(e)}
        
        # Step 2: ANALYSIS - Detect arbitrage opportunity
        if verbose:
            print("\n2️⃣ ANALYSIS: Detecting arbitrage opportunities...")
        
        try:
            opportunity = self.analysis_agent.detect_arbitrage(price_data)
            
            if not opportunity['opportunity']:
                if verbose:
                    gross = opportunity.get('gross_spread_pct', 0)
                    net = opportunity.get('net_spread_pct', 0)
                    print(f"   ✗ No opportunity")
                    print(f"      Gross spread: {gross:.3f}% | Net after fees: {net:.3f}% | Threshold: {self.threshold}%")
                return {
                    'success': True,
                    'stage': 'analysis',
                    'opportunity_found': False,
                    'opportunity': opportunity
                }
            
            self.opportunities_found += 1
            
            if verbose:
                print(f"   ✓ OPPORTUNITY DETECTED!")
                print(f"     Buy: {opportunity['buy_exchange']} @ ${opportunity['buy_price']:,.2f}")
                print(f"     Sell: {opportunity['sell_exchange']} @ ${opportunity['sell_price']:,.2f}")
                print(f"     Net Spread: {opportunity['net_spread_pct']:.3f}%")
        
        except Exception as e:
            print(f"   ✗ Error in analysis: {e}")
            return {'success': False, 'stage': 'analysis', 'error': str(e)}
        
        # Step 3: PREDICTION - Use ML to predict viability
        if verbose:
            print("\n3️⃣ PREDICTION: Forecasting opportunity persistence...")
        
        try:
            prediction = self.prediction_agent.predict_opportunity(
                pair=pair,
                current_prices=price_data,
                threshold=self.threshold,
                horizon=1,
                model_type='xgb'
            )
            
            if prediction['predicted'] is None:
                if verbose:
                    print(f"   ⚠ Prediction unavailable: {prediction.get('reason', 'Unknown')}")
                # Continue anyway with low confidence
                prediction['predicted'] = True
                prediction['confidence'] = 0.5
            elif verbose:
                verdict = "VIABLE ✓" if prediction['predicted'] else "NOT VIABLE ✗"
                print(f"   {verdict}")
                print(f"     Model: {prediction.get('model_type', 'N/A')}")
                print(f"     Confidence: {prediction.get('confidence', 0)*100:.1f}%")
        
        except Exception as e:
            print(f"   ✗ Error in prediction: {e}")
            prediction = {'predicted': True, 'confidence': 0.5, 'reason': f'Error: {e}'}
        
        # Step 4: DECISION - Risk assessment and trade decision
        if verbose:
            print("\n4️⃣ DECISION: Risk assessment and trade decision...")
        
        try:
            decision = self.decision_agent.make_decision(
                opportunity=opportunity,
                prediction=prediction,
                available_capital=self.execution_agent.portfolio['USDT']
            )
            
            if verbose:
                action_emoji = "🟢" if decision['action'] == 'EXECUTE' else "🔴"
                print(f"   {action_emoji} DECISION: {decision['action']}")
                print(f"     Reason: {decision['reason']}")
                print(f"     Risk Level: {decision['risk_assessment']['risk_level']}")
                
                if decision['action'] == 'EXECUTE':
                    print(f"     Position Size: {decision['position_size']:.8f} {pair.split('/')[0]}")
                    print(f"     Expected Profit: ${decision['expected_profit']:.2f}")
        
        except Exception as e:
            print(f"   ✗ Error in decision: {e}")
            return {'success': False, 'stage': 'decision', 'error': str(e)}
        
        # Step 5: EXECUTION - Simulate trade if decision is EXECUTE
        execution_result = None
        
        if decision['action'] == 'EXECUTE':
            if verbose:
                print("\n5️⃣ EXECUTION: Simulating trade...")
            
            try:
                if self.auto_execute:
                    execution_result = self.execution_agent.simulate_trade(decision)
                    
                    if execution_result['executed']:
                        self.trades_executed += 1
                        trade = execution_result['trade_record']
                        
                        if verbose:
                            print(f"   ✓ TRADE EXECUTED!")
                            print(f"     Trade ID: {trade['trade_id']}")
                            print(f"     Net Profit: ${trade['net_profit']:.2f}")
                            print(f"     ROI: {trade['roi_pct']:.3f}%")
                            print(f"     Portfolio Value: ${trade['portfolio_value']:,.2f}")
                    else:
                        if verbose:
                            print(f"   ✗ Trade failed: {execution_result['reason']}")
                else:
                    if verbose:
                        print(f"   ⚠ Auto-execute disabled - trade NOT executed")
                        print(f"     Set auto_execute=True to enable automatic trading")
            
            except Exception as e:
                print(f"   ✗ Error in execution: {e}")
                execution_result = {'executed': False, 'error': str(e)}
        
        return {
            'success': True,
            'timestamp': datetime.now(),
            'pair': pair,
            'opportunity_found': True,
            'opportunity': opportunity,
            'prediction': prediction,
            'decision': decision,
            'execution': execution_result,
            'stage': 'complete'
        }
    
    def run_continuous_monitoring(self, interval: int = 30, max_cycles: Optional[int] = None):
        """
        Run continuous monitoring and arbitrage detection
        
        Args:
            interval: Seconds between cycles
            max_cycles: Maximum number of cycles (None = infinite)
        """
        print("\n" + "="*80)
        print("🚀 STARTING CONTINUOUS ARBITRAGE MONITORING")
        print("="*80)
        print(f"Configuration:")
        print(f"  Pairs: {', '.join(PAIRS)}")
        print(f"  Threshold: {self.threshold}%")
        print(f"  Risk Tolerance: {self.risk_tolerance}")
        print(f"  Interval: {interval}s")
        print(f"  Auto-Execute: {self.auto_execute}")
        print(f"  Initial Capital: ${self.initial_capital:,.2f}")
        print("\nPress Ctrl+C to stop\n")
        print("="*80)
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                if max_cycles and cycle_count > max_cycles:
                    print(f"\n✓ Reached maximum cycles ({max_cycles})")
                    break
                
                print(f"\n\n{'#'*80}")
                print(f"# CYCLE {cycle_count}")
                print(f"{'#'*80}")
                
                # Run cycle for each pair
                for pair in PAIRS:
                    result = self.run_single_cycle(pair, verbose=True)
                    time.sleep(2)  # Small delay between pairs
                
                # Show summary
                self._print_session_summary()
                
                # Wait for next cycle
                print(f"\n⏳ Waiting {interval}s until next cycle...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹ Monitoring stopped by user")
        
        finally:
            self._print_final_report()
    
    def _print_session_summary(self):
        """Print current session summary"""
        print(f"\n{'─'*80}")
        print("📊 SESSION SUMMARY")
        print(f"{'─'*80}")
        print(f"Opportunities Found: {self.opportunities_found}")
        print(f"Trades Executed: {self.trades_executed}")
        
        if self.auto_execute and self.execution_agent.total_trades > 0:
            summary = self.execution_agent.get_performance_summary()
            print(f"Portfolio Value: ${summary['current_value']:,.2f}")
            print(f"Total P&L: ${summary['total_profit']:,.2f} ({summary['total_return_pct']:.2f}%)")
            print(f"Win Rate: {summary['win_rate']:.1f}%")
    
    def _print_final_report(self):
        """Print final report at end of session"""
        print("\n\n" + "="*80)
        print("📊 FINAL SESSION REPORT")
        print("="*80)
        
        print(f"\nOVERALL STATISTICS:")
        print(f"  Total Opportunities: {self.opportunities_found}")
        print(f"  Total Trades: {self.trades_executed}")
        
        if self.auto_execute and self.execution_agent.total_trades > 0:
            print("\n" + self.execution_agent.generate_report())
        else:
            print("\n  Note: Auto-execute was disabled. No trades were executed.")
        
        print("\n" + "="*80)
        print("Session ended at " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*80)


def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║              🤖 CRYPTO ARBITRAGE AGENTIC AI SYSTEM 🤖                        ║
║                                                                               ║
║              Autonomous Multi-Agent Arbitrage Detection                       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
    
    print("\nSelect Mode:")
    print("1. Single Cycle (one-time check)")
    print("2. Continuous Monitoring")
    print("3. Demo Mode (single cycle with sample data)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
    except:
        choice = "3"  # Default to demo
    
    # Configuration
    threshold = 0.2  # 0.2% minimum spread
    risk_tolerance = 'moderate'
    initial_capital = 10000.0
    
    # Initialize orchestrator
    orchestrator = ArbitrageAgentOrchestrator(
        threshold=threshold,
        risk_tolerance=risk_tolerance,
        initial_capital=initial_capital,
        auto_execute=False  # Set to True to actually execute trades
    )
    
    if choice == "1":
        # Single cycle
        print("\nRunning single cycle for all pairs...")
        for pair in PAIRS:
            orchestrator.run_single_cycle(pair, verbose=True)
        orchestrator._print_final_report()
    
    elif choice == "2":
        # Continuous monitoring
        print("\nStarting continuous monitoring...")
        orchestrator.run_continuous_monitoring(interval=30)
    
    else:
        # Demo mode
        print("\n🎬 DEMO MODE: Running single cycle...")
        for pair in PAIRS[:1]:  # Just first pair for demo
            result = orchestrator.run_single_cycle(pair, verbose=True)
        
        print("\n\n" + "="*80)
        print("Demo complete! To run in production:")
        print("  1. Set auto_execute=True to enable real trades")
        print("  2. Use mode 2 for continuous monitoring")
        print("  3. Adjust threshold and risk_tolerance as needed")
        print("="*80)


if __name__ == "__main__":
    main()
