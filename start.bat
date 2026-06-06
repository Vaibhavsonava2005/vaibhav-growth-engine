@echo off
echo ========================================================
echo       VAIBHAV GROWTH ENGINE - LOCAL LAUNCHER
echo ========================================================
echo.
echo Starting Python Backend API on port 8000...
start cmd /k "call venv\Scripts\activate 2>nul || echo Virtual env not found, using global python && cd api && uvicorn main:app --reload --port 8000"

echo Starting Next.js Dashboard on port 3000...
start cmd /k "cd dashboard && npm run dev"

echo.
echo Both servers are starting in separate windows!
echo Once they load, open your browser to:
echo http://localhost:3000
echo.
pause
