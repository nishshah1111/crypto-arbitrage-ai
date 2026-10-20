"""
Analysis Agent - Arbitrage Opportunity Detection
Analyzes price data to identify arbitrage opportunities
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class AnalysisAgent:
    """
    Autonomous agent for analyzing market data and detecting arbitrage opportunities.
    """
    
    def __init__(self, threshold: float = 0.5, fee_rate: float = 0.001):
        """
        Initialize the Analysis Agent
        
        Args:
            threshold: Minimum spread percentage to consider an opportunity (default: 0.5%)
            fee_rate: Trading fee rate per transaction (default: 0.1%)
        """
        self.threshold = threshold
        self.fee_rate = fee_rate
        self.opportunity_history = []
        self.closed_opportunities = []  # Track opportunities that were executed
        
    def detect_arbitrage(self, price_df: pd.DataFrame) -> Dict:
        """
        Detect arbitrage opportunities from price data
        
        Args:
            price_df: DataFrame with columns: exchange, price, pair, timestamp
            
        Returns:
            Dictionary with opportunity details or None
        """
        if price_df.empty or len(price_df) < 2:
            return {
                'opportunity': False,
                'reason': 'Insufficient data'
            }
        
        # Find min and max prices
        min_row = price_df.loc[price_df['price'].idxmin()]
        max_row = price_df.loc[price_df['price'].idxmax()]
        
        buy_price = min_row['price']
        sell_price = max_row['price']
        buy_exchange = min_row['exchange']
        sell_exchange = max_row['exchange']
        
        # Calculate gross spread
        gross_spread = ((sell_price - buy_price) / buy_price) * 100
        
        # Calculate net profit after fees (buy fee + sell fee)
        net_spread = gross_spread - (2 * self.fee_rate * 100)
        
        # Determine if this is an opportunity
        is_opportunity = net_spread >= self.threshold
        
        opportunity = {
            'opportunity': is_opportunity,
            'pair': price_df.iloc[0]['pair'],
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'gross_spread_pct': gross_spread,
            'net_spread_pct': net_spread,
            'fees_pct': 2 * self.fee_rate * 100,
            'threshold_pct': self.threshold,
            'timestamp': datetime.now(),
            'all_prices': price_df.set_index('exchange')['price'].to_dict()
        }
        
        if is_opportunity:
            self.opportunity_history.append(opportunity)
        
        return opportunity
    
    def calculate_spreads(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all pairwise spreads between exchanges
        
        Args:
            price_df: DataFrame with exchange prices
            
        Returns:
            DataFrame with spread matrix
        """
        exchanges = price_df['exchange'].unique()
        spreads = []
        
        for i, ex1 in enumerate(exchanges):
            for ex2 in exchanges[i+1:]:
                price1 = price_df[price_df['exchange'] == ex1]['price'].values[0]
                price2 = price_df[price_df['exchange'] == ex2]['price'].values[0]
                
                spread = ((price2 - price1) / price1) * 100
                
                spreads.append({
                    'exchange_1': ex1,
                    'exchange_2': ex2,
                    'price_1': price1,
                    'price_2': price2,
                    'spread_pct': abs(spread),
                    'direction': f"{ex1}→{ex2}" if spread > 0 else f"{ex2}→{ex1}"
                })
        
        return pd.DataFrame(spreads).sort_values('spread_pct', ascending=False)
    
    def analyze_opportunity(self, opportunity: Dict) -> str:
        """
        Generate natural language analysis of an opportunity
        
        Args:
            opportunity: Opportunity dictionary from detect_arbitrage
            
        Returns:
            String with detailed analysis
        """
        if not opportunity['opportunity']:
            return f"""
Analysis Result: No Arbitrage Opportunity
Pair: {opportunity.get('pair', 'Unknown')}
Reason: {opportunity.get('reason', 'Spread below threshold')}
Threshold: {self.threshold}%
"""
        
        profit_per_unit = opportunity['sell_price'] - opportunity['buy_price']
        roi_pct = (profit_per_unit / opportunity['buy_price']) * 100 - (2 * self.fee_rate * 100)
        
        analysis = f"""
✓ ARBITRAGE OPPORTUNITY DETECTED

Pair: {opportunity['pair']}
Timestamp: {opportunity['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

Trade Details:
- Buy from: {opportunity['buy_exchange']} at ${opportunity['buy_price']:,.2f}
- Sell to: {opportunity['sell_exchange']} at ${opportunity['sell_price']:,.2f}
- Gross Spread: {opportunity['gross_spread_pct']:.3f}%
- Trading Fees: {opportunity['fees_pct']:.3f}%
- Net Spread: {opportunity['net_spread_pct']:.3f}%

Profitability:
- Profit per unit: ${profit_per_unit:,.2f}
- ROI: {roi_pct:.3f}%
- Example (1 BTC): ${profit_per_unit:,.2f} profit

All Exchange Prices:
{self._format_all_prices(opportunity['all_prices'])}

Status: {'✓ ABOVE THRESHOLD' if opportunity['net_spread_pct'] >= self.threshold else '✗ BELOW THRESHOLD'}
"""
        return analysis.strip()
    
    def _format_all_prices(self, prices: Dict) -> str:
        """Format all exchange prices for display"""
        return '\n'.join([f"- {ex}: ${price:,.2f}" for ex, price in sorted(prices.items())])
    
    def get_opportunity_stats(self) -> Dict:
        """
        Get statistics about detected opportunities
        
        Returns:
            Dictionary with opportunity statistics
        """
        if not self.opportunity_history:
            return {
                'total_opportunities': 0,
                'message': 'No opportunities detected yet'
            }
        
        df = pd.DataFrame(self.opportunity_history)
        
        stats = {
            'total_opportunities': len(df),
            'avg_net_spread': df['net_spread_pct'].mean(),
            'max_net_spread': df['net_spread_pct'].max(),
            'min_net_spread': df['net_spread_pct'].min(),
            'most_common_buy_exchange': df['buy_exchange'].mode()[0] if len(df) > 0 else None,
            'most_common_sell_exchange': df['sell_exchange'].mode()[0] if len(df) > 0 else None,
            'pairs_analyzed': df['pair'].unique().tolist()
        }
        
        return stats
    
    def analyze_market(self, all_prices: Dict[str, pd.DataFrame]) -> str:
        """
        High-level market analysis for multiple pairs
        
        Args:
            all_prices: Dictionary mapping pair -> price DataFrame
            
        Returns:
            Natural language market analysis
        """
        results = []
        opportunities_found = 0
        
        for pair, df in all_prices.items():
            opp = self.detect_arbitrage(df)
            if opp['opportunity']:
                opportunities_found += 1
                results.append(f"✓ {pair}: {opp['net_spread_pct']:.3f}% spread")
            else:
                max_spread = ((df['price'].max() - df['price'].min()) / df['price'].min()) * 100
                results.append(f"✗ {pair}: {max_spread:.3f}% (below threshold)")
        
        analysis = f"""
Market Analysis Summary
=======================
Pairs Analyzed: {len(all_prices)}
Opportunities Found: {opportunities_found}
Threshold: {self.threshold}%

Details:
{chr(10).join(results)}
"""
        return analysis.strip()


class TriangularArbitrageAnalyzer:
    """
    Advanced analyzer for triangular arbitrage opportunities
    Example: BTC/USDT → ETH/BTC → ETH/USDT → USDT
    """
    
    def __init__(self, fee_rate: float = 0.001):
        self.fee_rate = fee_rate
    
    def detect_triangular(self, prices: Dict[str, float]) -> Optional[Dict]:
        """
        Detect triangular arbitrage between BTC, ETH, and USDT
        
        Args:
            prices: Dict with keys like 'BTC/USDT', 'ETH/USDT', 'ETH/BTC'
            
        Returns:
            Triangular opportunity details or None
        """
        # This is a simplified version - full implementation would need order book data
        # Placeholder for future enhancement
        return None


# Test function
def test_analysis_agent():
    """Test the Analysis Agent"""
    import pandas as pd
    
    # Sample price data
    sample_data = pd.DataFrame([
        {'exchange': 'binance', 'pair': 'BTC/USDT', 'price': 100000, 'timestamp': datetime.now()},
        {'exchange': 'coinbase', 'pair': 'BTC/USDT', 'price': 100500, 'timestamp': datetime.now()},
        {'exchange': 'kraken', 'pair': 'BTC/USDT', 'price': 100200, 'timestamp': datetime.now()},
    ])
    
    print("\n" + "="*80)
    print("TEST: Analysis Agent")
    print("="*80)
    
    agent = AnalysisAgent(threshold=0.2)
    
    # Test arbitrage detection
    opportunity = agent.detect_arbitrage(sample_data)
    print("\nOpportunity Detection:")
    print(opportunity)
    
    # Test analysis
    analysis = agent.analyze_opportunity(opportunity)
    print("\n" + analysis)
    
    # Test spread calculation
    spreads = agent.calculate_spreads(sample_data)
    print("\nAll Spreads:")
    print(spreads.to_string(index=False))


if __name__ == "__main__":
    test_analysis_agent()
