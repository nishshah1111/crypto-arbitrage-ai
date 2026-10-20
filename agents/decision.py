"""
Decision Agent - Risk Assessment and Trade Decision Making
Evaluates opportunities and makes informed trading decisions
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional


class DecisionAgent:
    """
    Autonomous agent for making trading decisions based on risk assessment.
    Considers multiple factors: profitability, risk, market conditions, and predictions.
    """
    
    def __init__(self, risk_tolerance: str = 'moderate', 
                 min_confidence: float = 0.6,
                 max_position_size: float = 1.0):
        """
        Initialize the Decision Agent
        
        Args:
            risk_tolerance: 'conservative', 'moderate', or 'aggressive'
            min_confidence: Minimum prediction confidence to act (0-1)
            max_position_size: Maximum position size (in base currency units)
        """
        self.risk_tolerance = risk_tolerance
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        
        # Risk tolerance parameters
        self.risk_params = {
            'conservative': {
                'min_spread': 0.5,
                'min_confidence': 0.75,
                'max_volatility': 0.02,
                'position_multiplier': 0.5
            },
            'moderate': {
                'min_spread': 0.3,
                'min_confidence': 0.60,
                'max_volatility': 0.05,
                'position_multiplier': 1.0
            },
            'aggressive': {
                'min_spread': 0.2,
                'min_confidence': 0.50,
                'max_volatility': 0.10,
                'position_multiplier': 1.5
            }
        }
        
        self.decision_history = []
        
    def assess_risk(self, opportunity: Dict, prediction: Dict, 
                   market_data: Optional[Dict] = None) -> Dict:
        """
        Comprehensive risk assessment
        
        Args:
            opportunity: Opportunity dict from AnalysisAgent
            prediction: Prediction dict from PredictionAgent
            market_data: Optional additional market data
            
        Returns:
            Risk assessment dictionary
        """
        risk_factors = {}
        risk_score = 0  # 0-100, lower is better
        
        # Get risk parameters for tolerance level
        params = self.risk_params.get(self.risk_tolerance, self.risk_params['moderate'])
        
        # 1. Spread Risk
        net_spread = opportunity.get('net_spread_pct', 0)
        if net_spread < params['min_spread']:
            risk_factors['spread'] = {
                'status': 'HIGH_RISK',
                'value': net_spread,
                'threshold': params['min_spread'],
                'reason': f'Spread {net_spread:.3f}% below minimum {params["min_spread"]}%'
            }
            risk_score += 30
        else:
            risk_factors['spread'] = {
                'status': 'LOW_RISK',
                'value': net_spread,
                'threshold': params['min_spread'],
                'reason': f'Spread {net_spread:.3f}% above minimum'
            }
            risk_score += 0
        
        # 2. Prediction Confidence Risk
        confidence = prediction.get('confidence', 0)
        if confidence < params['min_confidence']:
            risk_factors['prediction'] = {
                'status': 'HIGH_RISK',
                'value': confidence,
                'threshold': params['min_confidence'],
                'reason': f'Confidence {confidence:.2f} below minimum {params["min_confidence"]}'
            }
            risk_score += 40
        else:
            risk_factors['prediction'] = {
                'status': 'LOW_RISK',
                'value': confidence,
                'threshold': params['min_confidence'],
                'reason': f'High confidence prediction'
            }
            risk_score += max(0, (1 - confidence) * 20)
        
        # 3. Volatility Risk (if market data available)
        if market_data and 'volatility' in market_data:
            volatility = market_data['volatility']
            if volatility > params['max_volatility']:
                risk_factors['volatility'] = {
                    'status': 'HIGH_RISK',
                    'value': volatility,
                    'threshold': params['max_volatility'],
                    'reason': f'High volatility {volatility:.3f}'
                }
                risk_score += 20
            else:
                risk_factors['volatility'] = {
                    'status': 'LOW_RISK',
                    'value': volatility,
                    'threshold': params['max_volatility'],
                    'reason': 'Volatility within acceptable range'
                }
                risk_score += 5
        else:
            risk_factors['volatility'] = {
                'status': 'UNKNOWN',
                'reason': 'No volatility data available'
            }
            risk_score += 10  # Penalty for unknown
        
        # 4. Execution Risk (exchange reliability)
        # Simplified - in production, would check exchange status APIs
        buy_exchange = opportunity.get('buy_exchange', '')
        sell_exchange = opportunity.get('sell_exchange', '')
        
        if buy_exchange and sell_exchange:
            risk_factors['execution'] = {
                'status': 'LOW_RISK',
                'buy_exchange': buy_exchange,
                'sell_exchange': sell_exchange,
                'reason': 'Major exchanges with good liquidity'
            }
        else:
            risk_factors['execution'] = {
                'status': 'MEDIUM_RISK',
                'reason': 'Exchange information incomplete'
            }
            risk_score += 10
        
        # Overall risk level
        if risk_score <= 30:
            risk_level = 'LOW'
        elif risk_score <= 60:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'risk_tolerance': self.risk_tolerance,
            'assessment_time': datetime.now()
        }
    
    def calculate_position_size(self, opportunity: Dict, risk_assessment: Dict,
                               available_capital: float = 10000) -> float:
        """
        Calculate optimal position size based on risk
        
        Args:
            opportunity: Opportunity dictionary
            risk_assessment: Risk assessment dictionary
            available_capital: Available capital in USDT
            
        Returns:
            Position size in base currency (e.g., BTC)
        """
        params = self.risk_params.get(self.risk_tolerance, self.risk_params['moderate'])
        
        # Base position size (e.g., 0.1 BTC for moderate risk)
        base_position = self.max_position_size
        
        # Adjust for risk score
        risk_multiplier = max(0.1, 1 - (risk_assessment['risk_score'] / 100))
        
        # Adjust for risk tolerance
        tolerance_multiplier = params['position_multiplier']
        
        # Adjust for available capital
        buy_price = opportunity.get('buy_price', 100000)
        max_affordable = available_capital / buy_price
        
        # Calculate final position
        position_size = min(
            base_position * risk_multiplier * tolerance_multiplier,
            max_affordable,
            self.max_position_size
        )
        
        return round(position_size, 8)  # Round to 8 decimals for crypto
    
    def make_decision(self, opportunity: Dict, prediction: Dict,
                     market_data: Optional[Dict] = None,
                     available_capital: float = 10000) -> Dict:
        """
        Make final trading decision
        
        Args:
            opportunity: Opportunity from AnalysisAgent
            prediction: Prediction from PredictionAgent
            market_data: Optional market data
            available_capital: Available capital in USDT
            
        Returns:
            Decision dictionary with action and reasoning
        """
        # Check if there's an opportunity at all
        if not opportunity.get('opportunity', False):
            return {
                'action': 'HOLD',
                'reason': 'No arbitrage opportunity detected',
                'confidence': 0.0,
                'timestamp': datetime.now()
            }
        
        # Check prediction
        if prediction.get('predicted') is None:
            return {
                'action': 'HOLD',
                'reason': 'Unable to make prediction',
                'confidence': 0.0,
                'timestamp': datetime.now()
            }
        
        if not prediction.get('predicted', False):
            return {
                'action': 'HOLD',
                'reason': 'ML model predicts opportunity will not persist',
                'confidence': prediction.get('confidence', 0),
                'timestamp': datetime.now()
            }
        
        # Assess risk
        risk = self.assess_risk(opportunity, prediction, market_data)
        
        # Make decision based on risk level
        if risk['risk_level'] == 'HIGH':
            action = 'HOLD'
            reason = f"Risk too high (score: {risk['risk_score']})"
        elif risk['risk_level'] == 'MEDIUM':
            # Only proceed if confidence is very high
            if prediction.get('confidence', 0) >= 0.75:
                action = 'EXECUTE'
                reason = 'Medium risk but high confidence - cautious entry'
            else:
                action = 'HOLD'
                reason = 'Medium risk with insufficient confidence'
        else:  # LOW risk
            action = 'EXECUTE'
            reason = 'Low risk with favorable conditions'
        
        # Calculate position size if executing
        position_size = 0
        if action == 'EXECUTE':
            position_size = self.calculate_position_size(opportunity, risk, available_capital)
            
            # Double-check position size is viable
            if position_size < 0.001:  # Minimum viable position
                action = 'HOLD'
                reason = 'Position size too small to be profitable'
        
        # Build decision
        decision = {
            'action': action,
            'reason': reason,
            'confidence': prediction.get('confidence', 0),
            'risk_assessment': risk,
            'opportunity': opportunity,
            'prediction': prediction,
            'position_size': position_size,
            'timestamp': datetime.now(),
            'pair': opportunity.get('pair'),
            'expected_profit': opportunity.get('net_spread_pct', 0) * position_size * opportunity.get('buy_price', 0) / 100
        }
        
        # Record decision
        self.decision_history.append(decision)
        
        return decision
    
    def explain_decision(self, decision: Dict) -> str:
        """
        Generate natural language explanation of decision
        
        Args:
            decision: Decision dictionary
            
        Returns:
            String with decision explanation
        """
        action = decision['action']
        emoji = '🟢' if action == 'EXECUTE' else '🔴'
        
        explanation = f"""
{emoji} TRADING DECISION: {action}
{'='*60}

Decision Time: {decision['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
Pair: {decision.get('pair', 'Unknown')}

REASONING:
{decision['reason']}

OPPORTUNITY DETAILS:
- Net Spread: {decision['opportunity'].get('net_spread_pct', 0):.3f}%
- Buy: {decision['opportunity'].get('buy_exchange')} @ ${decision['opportunity'].get('buy_price', 0):,.2f}
- Sell: {decision['opportunity'].get('sell_exchange')} @ ${decision['opportunity'].get('sell_price', 0):,.2f}

PREDICTION:
- Model: {decision['prediction'].get('model_type', 'Unknown')}
- Confidence: {decision['confidence']*100:.1f}%
- Predicted Viable: {decision['prediction'].get('predicted', False)}

RISK ASSESSMENT:
- Risk Level: {decision['risk_assessment']['risk_level']}
- Risk Score: {decision['risk_assessment']['risk_score']}/100
- Risk Tolerance: {decision['risk_assessment']['risk_tolerance'].upper()}
"""
        
        if action == 'EXECUTE':
            explanation += f"""
EXECUTION PLAN:
- Position Size: {decision['position_size']:.8f} {decision.get('pair', '').split('/')[0]}
- Expected Profit: ${decision['expected_profit']:.2f}
- Buy from: {decision['opportunity'].get('buy_exchange')}
- Sell to: {decision['opportunity'].get('sell_exchange')}
"""
        
        # Add risk factor details
        explanation += "\nRISK FACTORS:\n"
        for factor, details in decision['risk_assessment']['risk_factors'].items():
            status = details.get('status', 'UNKNOWN')
            reason = details.get('reason', 'No details')
            explanation += f"- {factor.upper()}: {status} - {reason}\n"
        
        return explanation.strip()
    
    def get_decision_stats(self) -> Dict:
        """Get statistics about past decisions"""
        if not self.decision_history:
            return {'message': 'No decisions made yet'}
        
        df = pd.DataFrame(self.decision_history)
        
        stats = {
            'total_decisions': len(df),
            'execute_count': len(df[df['action'] == 'EXECUTE']),
            'hold_count': len(df[df['action'] == 'HOLD']),
            'execute_rate': len(df[df['action'] == 'EXECUTE']) / len(df) * 100,
            'avg_confidence': df['confidence'].mean(),
            'avg_risk_score': df.apply(lambda x: x['risk_assessment']['risk_score'], axis=1).mean()
        }
        
        return stats


# Test function
def test_decision_agent():
    """Test the Decision Agent"""
    print("\n" + "="*80)
    print("TEST: Decision Agent")
    print("="*80)
    
    # Create sample opportunity and prediction
    opportunity = {
        'opportunity': True,
        'pair': 'BTC/USDT',
        'buy_exchange': 'binance',
        'sell_exchange': 'coinbase',
        'buy_price': 100000,
        'sell_price': 100500,
        'net_spread_pct': 0.48,
        'timestamp': datetime.now()
    }
    
    prediction = {
        'predicted': True,
        'confidence': 0.85,
        'model_type': 'XGBoost'
    }
    
    # Test different risk tolerances
    for tolerance in ['conservative', 'moderate', 'aggressive']:
        print(f"\n{'='*60}")
        print(f"Testing with {tolerance.upper()} risk tolerance:")
        print(f"{'='*60}")
        
        agent = DecisionAgent(risk_tolerance=tolerance)
        decision = agent.make_decision(opportunity, prediction)
        
        print(agent.explain_decision(decision))


if __name__ == "__main__":
    test_decision_agent()
