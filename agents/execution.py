"""
Execution Agent - Trade Simulation and Order Management
Simulates trade execution and manages portfolio
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path


class ExecutionAgent:
    """
    Autonomous agent for executing trades (simulation mode).
    Tracks portfolio, simulates order execution, and calculates P&L.
    """
    
    def __init__(self, initial_capital: float = 10000.0,
                 fee_rate: float = 0.001,
                 slippage_rate: float = 0.0005,
                 persistence_file: str = 'portfolio_state.json'):
        """
        Initialize the Execution Agent
        
        Args:
            initial_capital: Starting capital in USDT
            fee_rate: Trading fee per transaction (0.1% = 0.001)
            slippage_rate: Estimated slippage per transaction
            persistence_file: JSON file to save/load portfolio state
        """
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.persistence_file = Path(__file__).parent.parent / persistence_file
        
        # Initialize default portfolio state first
        self.portfolio = {
            'USDT': initial_capital,
            'BTC': 0.0,
            'ETH': 0.0,
            'SOL': 0.0,
            'XRP': 0.0,
            'ADA': 0.0,
            'DOGE': 0.0,
            'MATIC': 0.0,
            'DOT': 0.0,
            'AVAX': 0.0,
            'LINK': 0.0,
            'UNI': 0.0,
            'ATOM': 0.0
        }
        
        # Trade history
        self.trade_history = []
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        
        # Closed opportunities tracking
        self.closed_opportunities = []
        
        # Active opportunities tracking (for expiration)
        self.active_opportunities = {}  # {opportunity_id: {opportunity_data, detected_at}}
        
        # Try to load existing portfolio (will override defaults if successful)
        if self.persistence_file.exists():
            self._load_state()
        else:
            # Save initial state
            self._save_state()
    
    def _save_state(self):
        """Save portfolio state to JSON file"""
        try:
            # Convert trade history to JSON-serializable format
            serializable_trades = []
            for trade in self.trade_history[-100:]:  # Keep last 100 trades
                trade_copy = trade.copy()
                # Convert datetime to ISO string
                if isinstance(trade_copy.get('timestamp'), datetime):
                    trade_copy['timestamp'] = trade_copy['timestamp'].isoformat()
                serializable_trades.append(trade_copy)
            
            # Convert closed opportunities to JSON-serializable format
            serializable_closed_opps = []
            for opp in self.closed_opportunities[-100:]:  # Keep last 100 closed opportunities
                opp_copy = opp.copy()
                # Convert datetime to ISO string
                if isinstance(opp_copy.get('detected_at'), datetime):
                    opp_copy['detected_at'] = opp_copy['detected_at'].isoformat()
                if isinstance(opp_copy.get('closed_at'), datetime):
                    opp_copy['closed_at'] = opp_copy['closed_at'].isoformat()
                serializable_closed_opps.append(opp_copy)
            
            state = {
                'portfolio': self.portfolio,
                'trade_history': serializable_trades,
                'closed_opportunities': serializable_closed_opps,
                'total_trades': self.total_trades,
                'successful_trades': self.successful_trades,
                'failed_trades': self.failed_trades,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.persistence_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def _load_state(self):
        """Load portfolio state from JSON file"""
        try:
            with open(self.persistence_file, 'r') as f:
                state = json.load(f)
            self.portfolio = state.get('portfolio', {})
            self.trade_history = state.get('trade_history', [])
            self.closed_opportunities = state.get('closed_opportunities', [])
            self.total_trades = state.get('total_trades', 0)
            self.successful_trades = state.get('successful_trades', 0)
            self.failed_trades = state.get('failed_trades', 0)
            print(f"✓ Loaded portfolio state: ${sum(self.portfolio.values()):.2f}, {self.total_trades} trades, {len(self.closed_opportunities)} closed opportunities")
        except Exception as e:
            print(f"No existing state found or error loading state: {e}")
            # Don't call __init__ again - just use defaults that are already set
    
    def close_opportunity(self, opportunity: Dict, status: str, trade_id: int = None, reason: str = None):
        """
        Mark an opportunity as closed
        
        Args:
            opportunity: The opportunity dictionary
            status: Status of closure ('executed', 'failed', 'expired')
            trade_id: ID of the trade if executed
            reason: Reason for closure if failed
        """
        closed_opp = {
            'opportunity_id': f"{opportunity.get('pair')}_{opportunity.get('buy_exchange')}_{opportunity.get('sell_exchange')}_{datetime.now().timestamp()}",
            'pair': opportunity.get('pair'),
            'buy_exchange': opportunity.get('buy_exchange'),
            'sell_exchange': opportunity.get('sell_exchange'),
            'spread_pct': opportunity.get('net_spread_pct'),
            'buy_price': opportunity.get('buy_price'),
            'sell_price': opportunity.get('sell_price'),
            'detected_at': datetime.now(),
            'closed_at': datetime.now(),
            'status': status,
            'trade_id': trade_id,
            'reason': reason
        }
        self.closed_opportunities.append(closed_opp)
        self._save_state()
    
    def register_opportunity(self, opportunity: Dict):
        """Register an active opportunity for expiration tracking"""
        opportunity_id = f"{opportunity.get('pair')}_{opportunity.get('buy_exchange')}_{opportunity.get('sell_exchange')}_{datetime.now().timestamp()}"
        self.active_opportunities[opportunity_id] = {
            'opportunity': opportunity,
            'detected_at': datetime.now()
        }
        # Clean old opportunities (expire after 60 seconds)
        self.expire_old_opportunities()
    
    def expire_old_opportunities(self, max_age_seconds: int = 60):
        """Mark opportunities older than max_age_seconds as expired"""
        current_time = datetime.now()
        expired_ids = []
        
        for opp_id, opp_data in self.active_opportunities.items():
            age = (current_time - opp_data['detected_at']).total_seconds()
            if age > max_age_seconds:
                print(f"⏱ Expiring opportunity: {opp_data['opportunity'].get('pair')} aged {age:.0f}s")
                # Mark as expired
                self.close_opportunity(
                    opp_data['opportunity'], 
                    'expired', 
                    None, 
                    f'Opportunity expired after {age:.0f} seconds without execution'
                )
                expired_ids.append(opp_id)
        
        # Remove expired opportunities from active list
        for opp_id in expired_ids:
            del self.active_opportunities[opp_id]
        
        if expired_ids:
            print(f"✓ Expired {len(expired_ids)} opportunities")
    
    def mark_opportunity_executed(self, opportunity: Dict):
        """Remove opportunity from active list when executed"""
        # Find and remove from active opportunities
        for opp_id, opp_data in list(self.active_opportunities.items()):
            if (opp_data['opportunity'].get('pair') == opportunity.get('pair') and
                opp_data['opportunity'].get('buy_exchange') == opportunity.get('buy_exchange') and
                opp_data['opportunity'].get('sell_exchange') == opportunity.get('sell_exchange')):
                del self.active_opportunities[opp_id]
                break
        
    def simulate_trade(self, decision: Dict) -> Dict:
        """
        Simulate executing a trade based on decision with realistic failure scenarios
        
        Args:
            decision: Decision dictionary from DecisionAgent
            
        Returns:
            Execution result dictionary
        """
        if decision['action'] != 'EXECUTE':
            return {
                'executed': False,
                'reason': 'Decision was HOLD',
                'timestamp': datetime.now()
            }
        
        opportunity = decision['opportunity']
        position_size = decision['position_size']
        
        # Extract details
        pair = opportunity['pair']
        base_currency = pair.split('/')[0]  # e.g., BTC
        quote_currency = pair.split('/')[1]  # e.g., USDT
        
        buy_exchange = opportunity['buy_exchange']
        sell_exchange = opportunity['sell_exchange']
        buy_price = opportunity['buy_price']
        sell_price = opportunity['sell_price']
        net_spread_pct = opportunity['net_spread_pct']
        
        # Check if we have enough capital (Paper trading - just warn but allow)
        required_capital = buy_price * position_size * (1 + self.fee_rate)
        if self.portfolio['USDT'] < required_capital:
            # In paper trading, we'll allow this but reduce position size
            affordable_position = (self.portfolio['USDT'] / (buy_price * (1 + self.fee_rate))) * 0.95
            if affordable_position < 0.0001:  # Too small to trade
                self.failed_trades += 1
                reason = f'Position size too small. Available: ${self.portfolio["USDT"]:.2f}'
                self.close_opportunity(opportunity, 'failed', None, reason)
                self._save_state()
                return {
                    'executed': False,
                    'reason': reason,
                    'timestamp': datetime.now()
                }
            position_size = affordable_position
            print(f"⚠️ Paper trade adjusted: ${required_capital:.2f} requested, ${self.portfolio['USDT']:.2f} available. Trading {position_size:.6f} instead.")
        
        # Realistic failure scenarios (simulate real exchange issues)
        # 1. Spread too small (< 0.3%) - high chance of failure due to price movement
        if net_spread_pct < 0.3:
            if np.random.random() < 0.4:  # 40% failure rate for small spreads
                self.total_trades += 1
                self.failed_trades += 1
                reason = f'Trade rejected: Spread too narrow ({net_spread_pct:.3f}%). Price moved during execution.'
                self.close_opportunity(opportunity, 'failed', None, reason)
                self._save_state()
                return {
                    'executed': False,
                    'reason': reason,
                    'timestamp': datetime.now()
                }
        
        # 2. Large position size - simulate liquidity issues
        position_value = buy_price * position_size
        if position_value > 1000:  # Positions > $1000
            if np.random.random() < 0.15:  # 15% failure rate for large orders
                self.total_trades += 1
                self.failed_trades += 1
                reason = f'Trade rejected: Insufficient liquidity for ${position_value:.2f} order'
                self.close_opportunity(opportunity, 'failed', None, reason)
                self._save_state()
                return {
                    'executed': False,
                    'reason': reason,
                    'timestamp': datetime.now()
                }
        
        # 3. Random execution failure (network issues, exchange downtime, etc.)
        if np.random.random() < 0.05:  # 5% random failure rate
            self.total_trades += 1
            self.failed_trades += 1
            reason = 'Trade rejected: Exchange timeout or network error'
            self.close_opportunity(opportunity, 'failed', None, reason)
            self._save_state()
            return {
                'executed': False,
                'reason': reason,
                'timestamp': datetime.now()
            }
        
        # Simulate slippage
        actual_buy_price = buy_price * (1 + self.slippage_rate)
        actual_sell_price = sell_price * (1 - self.slippage_rate)
        
        # Execute BUY
        buy_cost = position_size * actual_buy_price
        buy_fee = buy_cost * self.fee_rate
        total_buy_cost = buy_cost + buy_fee
        
        # Execute SELL
        sell_proceeds = position_size * actual_sell_price
        sell_fee = sell_proceeds * self.fee_rate
        net_sell_proceeds = sell_proceeds - sell_fee
        
        # Calculate profit
        gross_profit = sell_proceeds - buy_cost
        net_profit = net_sell_proceeds - total_buy_cost
        roi_pct = (net_profit / total_buy_cost) * 100
        
        # Update portfolio - ensure currency exists
        if base_currency not in self.portfolio:
            self.portfolio[base_currency] = 0.0
        
        self.portfolio['USDT'] -= total_buy_cost
        self.portfolio[base_currency] += position_size
        self.portfolio[base_currency] -= position_size
        self.portfolio['USDT'] += net_sell_proceeds
        
        # Record trade
        trade_record = {
            'trade_id': self.total_trades + 1,
            'timestamp': datetime.now(),
            'pair': pair,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'position_size': position_size,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'actual_buy_price': actual_buy_price,
            'actual_sell_price': actual_sell_price,
            'buy_cost': total_buy_cost,
            'sell_proceeds': net_sell_proceeds,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'roi_pct': roi_pct,
            'fees_paid': buy_fee + sell_fee,
            'slippage_cost': (actual_buy_price - buy_price) * position_size + 
                            (sell_price - actual_sell_price) * position_size,
            'portfolio_value': self.get_portfolio_value(),
            'success': net_profit > 0  # Trade is successful if net profit is positive
        }
        
        self.trade_history.append(trade_record)
        self.total_trades += 1
        
        if net_profit > 0:
            self.successful_trades += 1
        else:
            self.failed_trades += 1
        
        # Mark opportunity as executed
        self.close_opportunity(opportunity, 'executed', trade_record['trade_id'], f"Trade executed successfully with {roi_pct:.2f}% ROI")
        self.mark_opportunity_executed(opportunity)
        
        # Save state after each trade
        self._save_state()
        
        return {
            'executed': True,
            'trade_record': trade_record,
            'timestamp': datetime.now()
        }
    
    def get_portfolio_value(self, current_prices: Optional[Dict] = None) -> float:
        """
        Calculate total portfolio value in USDT
        
        Args:
            current_prices: Optional dict with current prices
            
        Returns:
            Total portfolio value in USDT
        """
        total_value = self.portfolio['USDT']
        
        # Add value of crypto holdings
        if current_prices:
            for currency, amount in self.portfolio.items():
                if currency != 'USDT' and amount > 0:
                    price = current_prices.get(f'{currency}/USDT', 0)
                    total_value += amount * price
        
        return total_value
    
    def get_performance_summary(self) -> Dict:
        """
        Get comprehensive performance summary
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'message': 'No trades executed yet'
            }
        
        df = pd.DataFrame(self.trade_history)
        
        current_value = self.portfolio['USDT']
        total_profit = current_value - self.initial_capital
        total_return_pct = (total_profit / self.initial_capital) * 100
        
        summary = {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'win_rate': (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            'initial_capital': self.initial_capital,
            'current_value': current_value,
            'total_profit': total_profit,
            'total_return_pct': total_return_pct,
            'avg_profit_per_trade': df['net_profit'].mean(),
            'total_fees_paid': df['fees_paid'].sum(),
            'total_slippage_cost': df['slippage_cost'].sum(),
            'best_trade_profit': df['net_profit'].max() if len(df) > 0 else 0,
            'worst_trade_profit': df['net_profit'].min() if len(df) > 0 else 0,
            'avg_roi_pct': df['roi_pct'].mean(),
            'portfolio': self.portfolio.copy()
        }
        
        return summary
    
    def generate_report(self) -> str:
        """
        Generate detailed execution report
        
        Returns:
            Formatted report string
        """
        summary = self.get_performance_summary()
        
        if summary.get('total_trades', 0) == 0:
            return "No trades executed yet."
        
        report = f"""
📊 EXECUTION AGENT PERFORMANCE REPORT
{'='*70}

TRADING SUMMARY:
- Total Trades: {summary['total_trades']}
- Successful: {summary['successful_trades']} ({summary['win_rate']:.1f}%)
- Failed: {summary['failed_trades']}

FINANCIAL PERFORMANCE:
- Initial Capital: ${summary['initial_capital']:,.2f}
- Current Value: ${summary['current_value']:,.2f}
- Total Profit/Loss: ${summary['total_profit']:,.2f} ({summary['total_return_pct']:.2f}%)
- Average Profit per Trade: ${summary['avg_profit_per_trade']:.2f}
- Average ROI: {summary['avg_roi_pct']:.3f}%

COSTS:
- Total Fees Paid: ${summary['total_fees_paid']:.2f}
- Total Slippage Cost: ${summary['total_slippage_cost']:.2f}
- Fee Rate: {self.fee_rate * 100:.2f}%
- Slippage Rate: {self.slippage_rate * 100:.2f}%

BEST/WORST TRADES:
- Best Trade Profit: ${summary['best_trade_profit']:.2f}
- Worst Trade Profit: ${summary['worst_trade_profit']:.2f}

CURRENT PORTFOLIO:
"""
        for currency, amount in summary['portfolio'].items():
            if currency == 'USDT':
                report += f"- {currency}: ${amount:,.2f}\n"
            elif amount > 0:
                report += f"- {currency}: {amount:.8f}\n"
        
        return report.strip()
    
    def export_trade_history(self, filepath: str = 'execution_history.csv'):
        """
        Export trade history to CSV
        
        Args:
            filepath: Path to save CSV file
        """
        if not self.trade_history:
            print("No trade history to export")
            return
        
        df = pd.DataFrame(self.trade_history)
        df.to_csv(filepath, index=False)
        print(f"Trade history exported to {filepath}")
    
    def reset_portfolio(self):
        """Reset portfolio to initial state"""
        self.portfolio = {
            'USDT': self.initial_capital,
            'BTC': 0.0,
            'ETH': 0.0
        }
        self.trade_history = []
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        print(f"Portfolio reset to ${self.initial_capital:,.2f}")


class BacktestEngine:
    """
    Backtesting engine for historical arbitrage strategy evaluation
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.results = []
    
    def run_backtest(self, historical_data: pd.DataFrame,
                    strategy_params: Dict) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            historical_data: DataFrame with historical prices and spreads
            strategy_params: Strategy parameters (thresholds, etc.)
            
        Returns:
            Backtest results dictionary
        """
        # This is a placeholder for a full backtesting implementation
        # Would need to integrate with agents and historical data
        
        print("Backtesting functionality - placeholder")
        print(f"Historical data: {len(historical_data)} rows")
        print(f"Strategy params: {strategy_params}")
        
        return {
            'total_trades': 0,
            'final_value': self.initial_capital,
            'message': 'Backtesting implementation in progress'
        }


# Test function
def test_execution_agent():
    """Test the Execution Agent"""
    print("\n" + "="*80)
    print("TEST: Execution Agent")
    print("="*80)
    
    agent = ExecutionAgent(initial_capital=10000)
    
    # Create sample decision for execution
    decision = {
        'action': 'EXECUTE',
        'position_size': 0.05,
        'opportunity': {
            'pair': 'BTC/USDT',
            'buy_exchange': 'binance',
            'sell_exchange': 'coinbase',
            'buy_price': 100000,
            'sell_price': 100500
        }
    }
    
    # Execute trade
    print("\nExecuting Trade 1:")
    result1 = agent.simulate_trade(decision)
    if result1['executed']:
        trade = result1['trade_record']
        print(f"✓ Trade executed successfully")
        print(f"  Net Profit: ${trade['net_profit']:.2f}")
        print(f"  ROI: {trade['roi_pct']:.3f}%")
    
    # Execute another trade
    print("\nExecuting Trade 2:")
    decision['opportunity']['buy_price'] = 99000
    decision['opportunity']['sell_price'] = 99300
    result2 = agent.simulate_trade(decision)
    
    # Show performance report
    print("\n" + "="*80)
    print("PERFORMANCE REPORT:")
    print("="*80)
    print(agent.generate_report())


if __name__ == "__main__":
    test_execution_agent()
