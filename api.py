"""
FastAPI Backend for Crypto Arbitrage AI System
Provides REST API endpoints for the frontend
"""

import sys
# Print emoji/check marks safely on Windows consoles that default to cp1252
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import List, Dict
import asyncio
import json
from datetime import datetime
import numpy as np
from pathlib import Path

# Import your agents
from agents.perception import PerceptionAgent
from agents.analysis import AnalysisAgent
from agents.prediction import PredictionAgent
from agents.decision import DecisionAgent
from agents.execution import ExecutionAgent
from config import EXCHANGES, PAIRS


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

app = FastAPI(
    title="Crypto Arbitrage AI API",
    description="Real-time crypto arbitrage detection using agentic AI",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
perception_agent = PerceptionAgent(EXCHANGES, PAIRS)
analysis_agent = AnalysisAgent(threshold=0.2)
prediction_agent = PredictionAgent()
decision_agent = DecisionAgent(risk_tolerance='moderate')
execution_agent = ExecutionAgent(initial_capital=10000.0)

# Store active connections for WebSocket
active_connections: List[WebSocket] = []


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "online",
        "service": "Crypto Arbitrage AI",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


@app.get("/api/pairs")
async def get_pairs():
    """Get list of monitored trading pairs"""
    return {
        "pairs": PAIRS,
        "count": len(PAIRS)
    }


@app.get("/api/exchanges")
async def get_exchanges():
    """Get list of connected exchanges"""
    return {
        "exchanges": list(EXCHANGES.keys()),
        "count": len(EXCHANGES)
    }


@app.get("/api/prices/all")
async def get_all_prices():
    """Get current prices for all pairs"""
    try:
        all_prices = {}
        
        for pair in PAIRS:
            price_data = perception_agent.fetch_prices(pair)
            if not price_data.empty:
                # Convert to dict and clean NaN values
                records = price_data.to_dict('records')
                # Replace NaN with None for JSON compatibility
                cleaned_records = []
                for record in records:
                    cleaned_record = {}
                    for key, value in record.items():
                        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                            cleaned_record[key] = None
                        else:
                            cleaned_record[key] = value
                    cleaned_records.append(cleaned_record)
                all_prices[pair] = cleaned_records
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data": all_prices
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/prices/{pair}")
async def get_prices(pair: str):
    """Get current prices for a specific pair"""
    try:
        price_data = perception_agent.fetch_prices(pair)
        
        if price_data.empty:
            return JSONResponse(
                status_code=404,
                content={"error": f"No data available for {pair}"}
            )
        
        return {
            "pair": pair,
            "timestamp": datetime.now().isoformat(),
            "prices": price_data.to_dict('records')
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/opportunities")
async def get_opportunities():
    """Scan all pairs for arbitrage opportunities"""
    # Expire old opportunities before scanning new ones
    print(f"🔍 Checking for expired opportunities... Active: {len(execution_agent.active_opportunities)}")
    execution_agent.expire_old_opportunities()
    print(f"✓ After expiration check. Active: {len(execution_agent.active_opportunities)}")
    
    opportunities = []
    
    for pair in PAIRS:
        try:
            # Fetch prices
            price_data = perception_agent.fetch_prices(pair)
            if price_data.empty:
                continue
            
            # Analyze for arbitrage
            opportunity = analysis_agent.detect_arbitrage(price_data)
            
            if opportunity['opportunity']:
                # Get ensemble prediction (uses multiple ML models)
                ensemble_prediction = prediction_agent.predict_with_ensemble(
                    pair=pair,
                    current_prices=price_data,
                    threshold=0.2,
                    horizon=1
                )
                
                # Also get individual XGBoost prediction for display
                xgb_prediction = prediction_agent.predict_opportunity(
                    pair=pair,
                    current_prices=price_data,
                    threshold=0.2,
                    horizon=1,
                    model_type='xgb'
                )
                
                # Use ensemble for decision making (more robust)
                prediction = ensemble_prediction if ensemble_prediction.get('predicted') is not None else xgb_prediction
                
                # Add individual model breakdowns for frontend display
                prediction['individual_models'] = ensemble_prediction.get('individual_predictions', [xgb_prediction])
                
                # Get decision
                decision = decision_agent.make_decision(
                    opportunity=opportunity,
                    prediction=prediction,
                    available_capital=execution_agent.portfolio['USDT']
                )
                
                # Register opportunity for expiration tracking
                if opportunity['opportunity']:  # True if opportunity exists
                    try:
                        execution_agent.register_opportunity(opportunity)
                        print(f"✓ Registered opportunity for {pair}: {opportunity.get('buy_exchange')} → {opportunity.get('sell_exchange')}")
                    except Exception as e:
                        print(f"✗ Error registering opportunity for {pair}: {e}")
                
                # Convert numpy types to Python native types
                opportunities.append({
                    "pair": pair,
                    "opportunity": convert_numpy_types(opportunity),
                    "prediction": convert_numpy_types(prediction),
                    "decision": convert_numpy_types(decision),
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"Error processing {pair}: {e}")
            continue
    
    return {
        "count": len(opportunities),
        "opportunities": opportunities,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    return {
        "portfolio": convert_numpy_types(execution_agent.portfolio),
        "initial_capital": float(execution_agent.initial_capital),
        "total_trades": int(execution_agent.total_trades),
        "successful_trades": int(execution_agent.successful_trades),
        "failed_trades": int(execution_agent.failed_trades),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/execute-trade")
async def execute_trade(trade_data: Dict):
    """Execute a paper trade"""
    try:
        # Validate trade data
        if 'opportunity' not in trade_data or 'pair' not in trade_data:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required fields"}
            )
        
        # Create decision for execution
        decision = {
            'action': 'EXECUTE',
            'position_size': trade_data.get('position_size', 0.01),  # Default to 0.01 BTC/ETH or equivalent
            'opportunity': trade_data['opportunity']
        }
        
        # Execute the trade
        result = execution_agent.simulate_trade(decision)
        
        if result['executed']:
            trade_record = result['trade_record']
            # Convert datetime to ISO string for JSON
            trade_record['timestamp'] = trade_record['timestamp'].isoformat()
            
            return {
                "success": True,
                "message": "Trade executed successfully!",
                "trade": convert_numpy_types(trade_record),
                "portfolio": convert_numpy_types(execution_agent.portfolio),
                "stats": {
                    "total_trades": int(execution_agent.total_trades),
                    "successful_trades": int(execution_agent.successful_trades),
                    "portfolio_value": float(sum(execution_agent.portfolio.values()))
                }
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result.get('reason', 'Trade not executed'),
                    "timestamp": result['timestamp'].isoformat()
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/trades")
async def get_trade_history():
    """Get trade history"""
    return {
        "trades": convert_numpy_types(execution_agent.trade_history),
        "count": len(execution_agent.trade_history),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    portfolio_value = float(sum(execution_agent.portfolio.values()))
    roi = float(((portfolio_value - execution_agent.initial_capital) / execution_agent.initial_capital) * 100)
    
    success_rate = 0.0
    if execution_agent.total_trades > 0:
        success_rate = float((execution_agent.successful_trades / execution_agent.total_trades) * 100)
    
    return {
        "portfolio_value": portfolio_value,
        "roi": roi,
        "total_trades": int(execution_agent.total_trades),
        "success_rate": success_rate,
        "opportunities_detected": len(analysis_agent.opportunity_history),
        "timestamp": datetime.now().isoformat()
    }


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send live updates every 5 seconds
            for pair in PAIRS:
                try:
                    price_data = perception_agent.fetch_prices(pair)
                    if not price_data.empty:
                        opportunity = analysis_agent.detect_arbitrage(price_data)
                        
                        data = {
                            "type": "price_update",
                            "pair": pair,
                            "prices": price_data.to_dict('records'),
                            "opportunity": opportunity,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await websocket.send_json(data)
                except Exception as e:
                    print(f"Error in WebSocket: {e}")
                
                await asyncio.sleep(5)
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/api/active-opportunities")
async def get_active_opportunities():
    """Get currently active (not yet executed/expired) opportunities"""
    try:
        active_opps = []
        for opp_id, opp_data in execution_agent.active_opportunities.items():
            age = (datetime.now() - opp_data['detected_at']).total_seconds()
            active_opps.append({
                'id': opp_id,
                'opportunity': opp_data['opportunity'],
                'detected_at': opp_data['detected_at'].isoformat(),
                'age_seconds': age
            })
        
        return {
            "success": True,
            "active_opportunities": active_opps,
            "count": len(active_opps),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/closed-opportunities")
async def get_closed_opportunities():
    """Get all closed opportunities"""
    try:
        # Expire old opportunities before returning
        execution_agent.expire_old_opportunities()
        
        closed_opps = execution_agent.closed_opportunities
        
        # Calculate statistics
        total = len(closed_opps)
        executed = sum(1 for opp in closed_opps if opp['status'] == 'executed')
        failed = sum(1 for opp in closed_opps if opp['status'] == 'failed')
        expired = sum(1 for opp in closed_opps if opp['status'] == 'expired')
        
        return {
            "success": True,
            "opportunities": closed_opps,
            "count": total,
            "stats": {
                "total": total,
                "executed": executed,
                "failed": failed,
                "expired": expired,
                "capture_rate": (executed / total * 100) if total > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Crypto Arbitrage AI - Backend Server")
    print("="*60)
    print(f"📡 API:       http://localhost:8000")
    print(f"📊 Dashboard: http://localhost:8000/dashboard")
    print(f"📚 API Docs:  http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
