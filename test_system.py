"""
Comprehensive Test Suite for Agentic AI Arbitrage System
Run this to verify all components are working correctly
"""

import sys
# Print emoji/check marks safely on Windows consoles that default to cp1252
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import sys
import time
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {test_name}{Colors.RESET}")
    print(f"{'='*80}")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def test_imports():
    """Test if all required packages are installed"""
    print_test_header("Package Installation Check")
    
    packages = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('ccxt', 'ccxt'),
        ('sklearn', 'scikit-learn'),
        ('xgboost', 'xgboost'),
        ('tensorflow', 'tensorflow'),
        ('joblib', 'joblib'),
    ]
    
    all_ok = True
    
    for module, package_name in packages:
        try:
            __import__(module)
            print_success(f"{package_name} is installed")
        except ImportError:
            print_error(f"{package_name} is NOT installed")
            print(f"   Install with: pip install {package_name}")
            all_ok = False
    
    return all_ok


def test_config():
    """Test configuration file"""
    print_test_header("Configuration Check")
    
    try:
        from config import EXCHANGES, PAIRS
        print_success("config.py loaded successfully")
        
        print(f"\nConfigured Exchanges: {list(EXCHANGES.keys())}")
        print(f"Configured Pairs: {PAIRS}")
        
        return True
    except Exception as e:
        print_error(f"Failed to load config.py: {e}")
        return False


def test_perception_agent():
    """Test Perception Agent"""
    print_test_header("Perception Agent Test")
    
    try:
        from agents.perception import PerceptionAgent
        from config import EXCHANGES, PAIRS
        
        agent = PerceptionAgent(EXCHANGES, PAIRS[:1])  # Test with one pair
        print_success("Perception Agent initialized")
        
        # Test price fetching
        print("\nFetching live prices...")
        prices = agent.fetch_prices(PAIRS[0])
        
        if not prices.empty:
            print_success(f"Fetched prices from {len(prices)} exchanges")
            print("\nSample data:")
            print(prices.to_string(index=False))
            return True
        else:
            print_error("No price data received")
            return False
            
    except Exception as e:
        print_error(f"Perception Agent test failed: {e}")
        return False


def test_analysis_agent():
    """Test Analysis Agent"""
    print_test_header("Analysis Agent Test")
    
    try:
        from agents.analysis import AnalysisAgent
        import pandas as pd
        
        agent = AnalysisAgent(threshold=0.2)
        print_success("Analysis Agent initialized")
        
        # Create sample data
        sample_data = pd.DataFrame([
            {'exchange': 'binance', 'pair': 'BTC/USDT', 'price': 100000, 'timestamp': datetime.now()},
            {'exchange': 'coinbase', 'pair': 'BTC/USDT', 'price': 100500, 'timestamp': datetime.now()},
            {'exchange': 'kraken', 'pair': 'BTC/USDT', 'price': 100200, 'timestamp': datetime.now()},
        ])
        
        opportunity = agent.detect_arbitrage(sample_data)
        
        if opportunity:
            print_success("Arbitrage detection works")
            print(f"\nOpportunity: {opportunity['opportunity']}")
            if opportunity['opportunity']:
                print(f"Net Spread: {opportunity['net_spread_pct']:.3f}%")
            return True
        else:
            print_error("Arbitrage detection failed")
            return False
            
    except Exception as e:
        print_error(f"Analysis Agent test failed: {e}")
        return False


def test_prediction_agent():
    """Test Prediction Agent"""
    print_test_header("Prediction Agent Test")
    
    try:
        from agents.prediction import PredictionAgent
        
        agent = PredictionAgent()
        print_success("Prediction Agent initialized")
        
        print(f"\nModels loaded: {len(agent.models)}")
        
        if len(agent.models) > 0:
            print_success(f"{len(agent.models)} ML models available")
            print("\nAvailable models:")
            for model_name in list(agent.models.keys())[:5]:
                print(f"  - {model_name}")
            return True
        else:
            print_warning("No models found - run models/train_simplified.py first")
            return True  # Not a critical failure
            
    except Exception as e:
        print_error(f"Prediction Agent test failed: {e}")
        return False


def test_decision_agent():
    """Test Decision Agent"""
    print_test_header("Decision Agent Test")
    
    try:
        from agents.decision import DecisionAgent
        
        # Test all risk tolerance levels
        for tolerance in ['conservative', 'moderate', 'aggressive']:
            agent = DecisionAgent(risk_tolerance=tolerance)
            print_success(f"Decision Agent initialized with {tolerance} tolerance")
        
        # Test risk assessment
        sample_opportunity = {
            'opportunity': True,
            'pair': 'BTC/USDT',
            'buy_exchange': 'binance',
            'sell_exchange': 'coinbase',
            'buy_price': 100000,
            'sell_price': 100500,
            'net_spread_pct': 0.48
        }
        
        sample_prediction = {
            'predicted': True,
            'confidence': 0.85
        }
        
        agent = DecisionAgent()
        decision = agent.make_decision(sample_opportunity, sample_prediction)
        
        if decision:
            print_success("Decision making works")
            print(f"\nDecision: {decision['action']}")
            print(f"Reason: {decision['reason']}")
            return True
        else:
            print_error("Decision making failed")
            return False
            
    except Exception as e:
        print_error(f"Decision Agent test failed: {e}")
        return False


def test_execution_agent():
    """Test Execution Agent"""
    print_test_header("Execution Agent Test")
    
    try:
        from agents.execution import ExecutionAgent
        
        agent = ExecutionAgent(initial_capital=10000)
        print_success("Execution Agent initialized")
        
        # Test portfolio
        print(f"\nInitial Portfolio: ${agent.portfolio['USDT']:,.2f}")
        
        # Test trade simulation
        sample_decision = {
            'action': 'EXECUTE',
            'position_size': 0.01,
            'opportunity': {
                'pair': 'BTC/USDT',
                'buy_exchange': 'binance',
                'sell_exchange': 'coinbase',
                'buy_price': 100000,
                'sell_price': 100500
            }
        }
        
        result = agent.simulate_trade(sample_decision)
        
        if result['executed']:
            print_success("Trade simulation works")
            trade = result['trade_record']
            print(f"\nSimulated Trade:")
            print(f"  Net Profit: ${trade['net_profit']:.2f}")
            print(f"  ROI: {trade['roi_pct']:.3f}%")
            return True
        else:
            print_error("Trade simulation failed")
            return False
            
    except Exception as e:
        print_error(f"Execution Agent test failed: {e}")
        return False


def test_full_integration():
    """Test full system integration"""
    print_test_header("Full System Integration Test")
    
    try:
        from main import ArbitrageAgentOrchestrator
        from config import PAIRS
        
        orchestrator = ArbitrageAgentOrchestrator(
            threshold=0.2,
            risk_tolerance='moderate',
            initial_capital=10000.0,
            auto_execute=False
        )
        
        print_success("Orchestrator initialized")
        
        # Run single cycle
        print("\nRunning single arbitrage cycle...")
        result = orchestrator.run_single_cycle(PAIRS[0], verbose=False)
        
        if result.get('success'):
            print_success("Full cycle completed successfully")
            print(f"\nCycle Results:")
            print(f"  Stage: {result.get('stage')}")
            print(f"  Opportunity Found: {result.get('opportunity_found', False)}")
            return True
        else:
            print_error(f"Cycle failed at stage: {result.get('stage')}")
            return False
            
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_files():
    """Test if required data files exist"""
    print_test_header("Data Files Check")
    
    import os
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_to_check = [
        (os.path.join(script_dir, 'data/btc_usdt_features.csv'), 'BTC features'),
        (os.path.join(script_dir, 'data/eth_usdt_features.csv'), 'ETH features'),
        (os.path.join(script_dir, 'data/model_results.csv'), 'Model results'),
    ]
    
    all_ok = True
    
    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            print_success(f"{description} file exists")
        else:
            print_warning(f"{description} file not found: {filepath}")
            all_ok = False
    
    # Check for model files
    model_count = 0
    models_dir = os.path.join(script_dir, 'models')
    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith(('.pkl', '.keras')):
                model_count += 1
    
    if model_count > 0:
        print_success(f"Found {model_count} trained models")
    else:
        print_warning("No trained models found - run models/train_simplified.py")
    
    return all_ok


def run_all_tests():
    """Run all tests and generate report"""
    print(f"\n{'#'*80}")
    print(f"#{'AGENTIC AI ARBITRAGE SYSTEM - TEST SUITE'.center(78)}#")
    print(f"#{'Started: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(78)}#")
    print(f"{'#'*80}\n")
    
    tests = [
        ("Package Installation", test_imports),
        ("Configuration", test_config),
        ("Data Files", test_data_files),
        ("Perception Agent", test_perception_agent),
        ("Analysis Agent", test_analysis_agent),
        ("Prediction Agent", test_prediction_agent),
        ("Decision Agent", test_decision_agent),
        ("Execution Agent", test_execution_agent),
        ("Full Integration", test_full_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n\n{'='*80}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
    print(f"{'='*80}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{'='*80}")
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*80}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! System is ready to use.{Colors.RESET}\n")
        print("Next steps:")
        print("  1. Run: python main.py")
        print("  2. Select demo mode (option 3)")
        print("  3. See QUICKSTART.md for more info")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Some tests failed. Please fix issues before running.{Colors.RESET}\n")
        print("Common fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Train models: python models/train_simplified.py")
        print("  - Check config.py exists and is properly formatted")
    
    print()


if __name__ == "__main__":
    run_all_tests()
