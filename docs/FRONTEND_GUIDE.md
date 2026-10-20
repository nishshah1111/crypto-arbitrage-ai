# 🚀 Crypto Arbitrage AI - Frontend Setup Guide

## Tech Stack

**Backend:** FastAPI (Python)  
**Frontend:** React (JavaScript)  
**Styling:** Custom CSS  
**API Communication:** Axios  
**Icons:** Lucide React  

---

## 📁 Project Structure

```
crypto-arbitrage-ai/
├── api.py                    # FastAPI backend
├── frontend/                 # React frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js           # Main React component
│   │   ├── App.css          # Styles
│   │   └── index.js         # Entry point
│   └── package.json
├── agents/                   # Your AI agents
├── models/                   # ML models
└── config.py                # Configuration
```

---

## 🛠️ Setup Instructions

### Step 1: Install Backend Dependencies

```bash
cd "crypto-arbitrage-ai"

# Install FastAPI and dependencies
pip install fastapi uvicorn[standard] python-multipart
```

### Step 2: Install Node.js (if not installed)

Download from: https://nodejs.org/ (LTS version recommended)

### Step 3: Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will install:
- React
- Axios (API calls)
- Recharts (charts)
- Lucide React (icons)

### Step 4: Start Backend API

```bash
# Go back to root directory
cd ..

# Start FastAPI server
python api.py
```

Backend will run on: http://localhost:8000

### Step 5: Start Frontend

```bash
# Open new terminal
cd frontend
npm start
```

Frontend will open automatically at: http://localhost:3000

---

## 🌐 API Endpoints

### Base URL: `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/pairs` | GET | List of trading pairs |
| `/api/exchanges` | GET | List of exchanges |
| `/api/prices/{pair}` | GET | Prices for specific pair |
| `/api/prices/all` | GET | Prices for all pairs |
| `/api/opportunities` | GET | Current arbitrage opportunities |
| `/api/portfolio` | GET | Portfolio status |
| `/api/trades` | GET | Trade history |
| `/api/stats` | GET | System statistics |
| `/ws/live` | WebSocket | Real-time updates |

---

## 🎨 Frontend Features

### 1. **Real-Time Dashboard**
- Live price updates every 30 seconds
- Auto-refresh capability
- Beautiful gradient design

### 2. **Statistics Cards**
- Portfolio value & ROI
- Total trades & success rate
- Active opportunities count
- Last update timestamp

### 3. **Opportunities Section**
- Shows active arbitrage opportunities
- Buy/Sell prices and exchanges
- Net spread percentage
- ML prediction confidence
- Risk assessment level
- Execute/Hold decision

### 4. **Price Table**
- All trading pairs (12 pairs)
- Prices from 4 exchanges
- Spread calculation
- Color-coded spreads

### 5. **Portfolio View**
- Current holdings
- Asset amounts
- Visual cards for each asset

---

## 🚢 Deployment Options

### Option 1: Vercel (Frontend) + Railway (Backend)

#### **Frontend on Vercel (FREE):**

1. Push frontend to GitHub
```bash
cd frontend
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/crypto-frontend.git
git push -u origin main
```

2. Go to https://vercel.com
3. Import your GitHub repo
4. Deploy! (automatic)
5. Get URL: `https://crypto-arbitrage.vercel.app`

#### **Backend on Railway (FREE):**

1. Push backend to GitHub (separate repo or same)
2. Go to https://railway.app
3. Deploy from GitHub
4. Add environment variables
5. Get URL: `https://your-api.railway.app`

6. **Update frontend API URL:**
```javascript
// In App.js, change:
const API_URL = 'https://your-api.railway.app';
```

---

### Option 2: Both on Railway

Deploy backend and frontend as separate services on Railway.

---

### Option 3: Netlify (Frontend) + Railway (Backend)

Similar to Vercel option, but using Netlify for frontend.

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

For production:
```env
REACT_APP_API_URL=https://your-api.railway.app
```

---

## 📱 Features Overview

### What the Frontend Does:

1. **Fetches Data from API**
   - Prices from all exchanges
   - Arbitrage opportunities
   - Portfolio status
   - Trading statistics

2. **Displays Real-Time Updates**
   - Auto-refresh every 30 seconds
   - Manual refresh button
   - Live timestamp

3. **Visualizes Opportunities**
   - Clear buy/sell indicators
   - Profit calculations
   - Risk levels
   - Confidence scores

4. **Shows Portfolio**
   - Current holdings
   - Total value
   - ROI calculation

5. **Responsive Design**
   - Works on desktop
   - Works on mobile
   - Works on tablet

---

## 🐛 Troubleshooting

### Frontend won't start?
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm start
```

### API connection error?
- Check if backend is running on port 8000
- Check CORS settings in api.py
- Verify API_URL in App.js

### No data showing?
- Check browser console for errors
- Verify API endpoints are working: http://localhost:8000/api/prices/all
- Check if exchanges are connected

---

## 🎯 Testing

### Test Backend:
```bash
# Visit in browser:
http://localhost:8000
http://localhost:8000/api/pairs
http://localhost:8000/api/prices/all
```

### Test Frontend:
```bash
# Should open automatically at:
http://localhost:3000
```

---

## 📊 Production Checklist

Before deploying to production:

- [ ] Add proper error handling
- [ ] Add loading states
- [ ] Add authentication (if needed)
- [ ] Set up proper CORS
- [ ] Add rate limiting to API
- [ ] Optimize API calls
- [ ] Add logging
- [ ] Set up monitoring
- [ ] Add SSL certificates
- [ ] Set up custom domain

---

## 💡 Next Steps

### Enhancements You Can Add:

1. **Real-Time WebSocket Updates**
   - Live price streaming
   - Instant notifications

2. **Charts & Graphs**
   - Price history charts
   - Spread trends
   - ROI over time

3. **Trade Execution**
   - Manual trade buttons
   - Auto-trading toggle
   - Trade confirmations

4. **Alerts & Notifications**
   - Email alerts
   - Push notifications
   - Sound alerts

5. **Advanced Filters**
   - Filter by exchange
   - Filter by risk level
   - Filter by spread size

---

## 🌟 Demo for Capstone

### Perfect Setup for Presentation:

1. **Run locally during presentation**
   - Terminal 1: `python api.py` (backend)
   - Terminal 2: `npm start` (frontend in `frontend/` folder)

2. **Show live in browser**
   - Open http://localhost:3000
   - Demonstrate auto-refresh
   - Show opportunities detection

3. **Deploy for online access**
   - Frontend on Vercel (free)
   - Backend on Railway (free)
   - Share public URL with professors

---

## 📞 Support

Need help? Check:
- FastAPI docs: https://fastapi.tiangolo.com/
- React docs: https://react.dev/
- Railway docs: https://docs.railway.app/
- Vercel docs: https://vercel.com/docs

---

**Ready to run your crypto arbitrage AI with a beautiful interface!** 🚀
