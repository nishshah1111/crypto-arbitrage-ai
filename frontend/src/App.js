import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, TrendingUp, DollarSign, AlertCircle, RefreshCw } from 'lucide-react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [prices, setPrices] = useState({});
  const [opportunities, setOpportunities] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Fetch all data
  const fetchData = async () => {
    try {
      const [pricesRes, oppsRes, portfolioRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/prices/all`),
        axios.get(`${API_URL}/api/opportunities`),
        axios.get(`${API_URL}/api/portfolio`),
        axios.get(`${API_URL}/api/stats`)
      ]);

      setPrices(pricesRes.data.data);
      setOpportunities(oppsRes.data.opportunities);
      setPortfolio(portfolioRes.data);
      setStats(statsRes.data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading Crypto Arbitrage AI...</p>
      </div>
    );
  }

  return (
    <div className="App">
      {/* Header */}
      <header className="header">
        <div className="container">
          <h1>🧠 Crypto Arbitrage AI</h1>
          <p>Real-time Arbitrage Detection Using Agentic AI</p>
          <button onClick={fetchData} className="refresh-btn">
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </header>

      <div className="container">
        {/* Stats Cards */}
        <div className="stats-grid">
          <StatCard
            icon={<DollarSign />}
            title="Portfolio Value"
            value={`$${stats?.portfolio_value.toFixed(2)}`}
            subtitle={`ROI: ${stats?.roi.toFixed(2)}%`}
            trend={stats?.roi >= 0}
          />
          <StatCard
            icon={<Activity />}
            title="Total Trades"
            value={stats?.total_trades}
            subtitle={`Success Rate: ${stats?.success_rate.toFixed(1)}%`}
            trend={stats?.success_rate >= 50}
          />
          <StatCard
            icon={<TrendingUp />}
            title="Opportunities"
            value={opportunities.length}
            subtitle={`Active now`}
            trend={opportunities.length > 0}
          />
          <StatCard
            icon={<AlertCircle />}
            title="Last Update"
            value={lastUpdate.toLocaleTimeString()}
            subtitle={lastUpdate.toLocaleDateString()}
          />
        </div>

        {/* Opportunities Section */}
        <section className="section">
          <h2>🎯 Active Opportunities</h2>
          {opportunities.length === 0 ? (
            <div className="no-data">
              <AlertCircle size={48} />
              <p>No arbitrage opportunities detected</p>
              <small>Market is efficient right now. Opportunities will appear during volatility.</small>
            </div>
          ) : (
            <div className="opportunities-grid">
              {opportunities.map((opp, idx) => (
                <OpportunityCard key={idx} opportunity={opp} />
              ))}
            </div>
          )}
        </section>

        {/* Price Table */}
        <section className="section">
          <h2>📊 Real-Time Prices</h2>
          <div className="price-grid">
            {Object.entries(prices).map(([pair, priceData]) => (
              <PriceCard key={pair} pair={pair} prices={priceData} />
            ))}
          </div>
        </section>

        {/* Portfolio Section */}
        <section className="section">
          <h2>💰 Portfolio</h2>
          <div className="portfolio-grid">
            {portfolio && Object.entries(portfolio.portfolio).map(([asset, amount]) => (
              amount > 0 && (
                <div key={asset} className="portfolio-item">
                  <div className="asset-name">{asset}</div>
                  <div className="asset-amount">{amount.toFixed(8)}</div>
                </div>
              )
            ))}
          </div>
        </section>
      </div>

      <footer className="footer">
        <p>Built with React + FastAPI • Agentic AI System</p>
        <p>© 2025 Crypto Arbitrage AI</p>
      </footer>
    </div>
  );
}

// Stat Card Component
function StatCard({ icon, title, value, subtitle, trend }) {
  return (
    <div className={`stat-card ${trend ? 'positive' : 'negative'}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <h3>{title}</h3>
        <div className="stat-value">{value}</div>
        <div className="stat-subtitle">{subtitle}</div>
      </div>
    </div>
  );
}

// Opportunity Card Component
function OpportunityCard({ opportunity }) {
  const { pair, opportunity: opp, prediction, decision } = opportunity;
  
  return (
    <div className="opportunity-card">
      <div className="opp-header">
        <h3>{pair}</h3>
        <span className={`badge ${decision.action === 'EXECUTE' ? 'success' : 'warning'}`}>
          {decision.action}
        </span>
      </div>
      <div className="opp-details">
        <div className="opp-row">
          <span>Buy:</span>
          <span>{opp.buy_exchange} @ ${opp.buy_price.toFixed(2)}</span>
        </div>
        <div className="opp-row">
          <span>Sell:</span>
          <span>{opp.sell_exchange} @ ${opp.sell_price.toFixed(2)}</span>
        </div>
        <div className="opp-row highlight">
          <span>Net Spread:</span>
          <span className="profit">{opp.net_spread_pct.toFixed(3)}%</span>
        </div>
        <div className="opp-row">
          <span>Confidence:</span>
          <span>{(prediction.confidence * 100).toFixed(1)}%</span>
        </div>
        <div className="opp-row">
          <span>Risk Level:</span>
          <span className={`risk-${decision.risk_assessment.risk_level.toLowerCase()}`}>
            {decision.risk_assessment.risk_level}
          </span>
        </div>
      </div>
    </div>
  );
}

// Price Card Component
function PriceCard({ pair, prices }) {
  const minPrice = Math.min(...prices.map(p => p.price));
  const maxPrice = Math.max(...prices.map(p => p.price));
  const spread = ((maxPrice - minPrice) / minPrice) * 100;
  
  return (
    <div className="price-card">
      <h3>{pair}</h3>
      <div className="price-list">
        {prices.map((p, idx) => (
          <div key={idx} className="price-row">
            <span className="exchange-name">{p.exchange}</span>
            <span className="price-value">${p.price.toLocaleString()}</span>
          </div>
        ))}
      </div>
      <div className="spread-info">
        Spread: <span className={spread > 0.2 ? 'high-spread' : 'low-spread'}>
          {spread.toFixed(3)}%
        </span>
      </div>
    </div>
  );
}

export default App;
