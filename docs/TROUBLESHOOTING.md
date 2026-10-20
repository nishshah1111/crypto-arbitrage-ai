# 🔧 Troubleshooting Guide

## Issue: Frontend Shows "Network Error" or "Cannot connect"

### **Root Cause:**
The React frontend couldn't connect to the API backend because of a **numpy serialization bug** in the API.

### **Fix Applied:** ✅
1. Added `convert_numpy_types()` function to convert numpy bool/int/float to Python native types
2. Updated all API endpoints to use this converter
3. Restarted API server

---

## How to Start the System

### **Step 1: Start API Backend**
```powershell
cd "crypto-arbitrage-ai"
python api.py
```

**Wait for this message:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### **Step 2: Start React Frontend** (new terminal window)
```powershell
cd "crypto-arbitrage-ai\frontend"
npm start
```

**Opens automatically at:** http://localhost:3000

---

## Common Issues

### 1. **API Won't Start**

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:**
```powershell
pip install fastapi uvicorn[standard] python-multipart websockets
```

### 2. **React Won't Start**

**Error:** `'npm' is not recognized`

**Fix:** Install Node.js from https://nodejs.org/

**Error:** `Cannot find module 'react'`

**Fix:**
```powershell
cd frontend
npm install
```

### 3. **Port Already in Use**

**Error:** `OSError: [WinError 10048] Only one usage of each socket address`

**Fix:**
```powershell
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

### 4. **CORS Errors in Browser**

**Symptom:** Console shows `CORS policy: No 'Access-Control-Allow-Origin' header`

**Fix:** API already has CORS enabled. Make sure:
- API is running on port 8000
- React is running on port 3000
- No browser extensions blocking requests

### 5. **No Opportunities Showing**

**This is NORMAL!** 
- Current market spreads: 0.02% - 0.35%
- After fees (0.2%): Net spreads are negative or below threshold
- System is working correctly
- During high volatility, opportunities will appear

---

## Testing API Manually

### **Test Health Check:**
```powershell
curl http://localhost:8000
```

**Expected Response:**
```json
{
  "status": "online",
  "service": "Crypto Arbitrage AI",
  "version": "1.0.0"
}
```

### **Test Stats Endpoint:**
```powershell
curl http://localhost:8000/api/stats
```

### **Test Opportunities:**
```powershell
curl http://localhost:8000/api/opportunities
```

### **View API Documentation:**
Open in browser: http://localhost:8000/docs

---

## Quick Restart Commands

### **Restart API Only:**
1. Press `CTRL+C` in API terminal
2. Run: `python api.py`

### **Restart React Only:**
1. Press `CTRL+C` in React terminal
2. Run: `npm start`

### **Full System Restart:**
1. Close all terminals
2. Open new terminal:
   ```powershell
   cd "crypto-arbitrage-ai"
   python api.py
   ```
3. Open another terminal:
   ```powershell
   cd "crypto-arbitrage-ai\frontend"
   npm start
   ```

---

## Alternative: Use HTML Dashboard Instead

If React is giving issues, use the **zero-build HTML dashboard**:

1. **Start API:**
   ```powershell
   python api.py
   ```

2. **Open Dashboard:**
   - Double-click `dashboard.html` in project folder
   - OR open in browser: `http://localhost:8000/dashboard`

3. **Done!** No npm, no build, no hassle! ✨

---

## Verification Checklist

Before presenting/deploying, verify:

- [ ] API starts without errors
- [ ] All 81 ML models load successfully
- [ ] React app opens at http://localhost:3000
- [ ] Dashboard shows stats cards
- [ ] Prices are updating (click refresh)
- [ ] No console errors in browser (F12)
- [ ] Portfolio shows $10,000 USDT
- [ ] API docs work at http://localhost:8000/docs

---

## Still Having Issues?

### Check Python Version:
```powershell
python --version
```
Should be: **Python 3.13.x** (or 3.8+)

### Check Node Version:
```powershell
node --version
npm --version
```
Should be: **Node 18+**, **npm 9+**

### Check Installed Packages:
```powershell
pip list | findstr fastapi
pip list | findstr uvicorn
```

### View Full API Logs:
The terminal running `python api.py` shows all activity including:
- Price fetching
- Opportunities detected
- API requests
- Errors

---

## Success Indicators

**API Working:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✓ Connected to binance
✓ Connected to coinbase
✓ Connected to kraken
Total models loaded: 81
```

**React Working:**
```
Compiled successfully!
webpack compiled with 0 warnings

You can now view frontend in the browser.
  Local:            http://localhost:3000
```

**Dashboard Working:**
- Stats cards show numbers
- Prices table populated
- No red errors in console
- Refresh button works

---

## Need Help?

1. Check browser console (F12 → Console tab)
2. Check API terminal output
3. Read error messages carefully
4. Verify both servers are running
5. Try the HTML dashboard as backup

**Remember:** The system is working correctly even without opportunities. Low spreads = efficient market! ✅

