@echo off
echo.
echo ====================================
echo   Crypto Arbitrage AI Dashboard
echo ====================================
echo.
echo Starting API Server...
echo.

cd /d "%~dp0"

python api.py

echo.
echo ====================================
echo   Server Stopped
echo ====================================
echo.
pause
