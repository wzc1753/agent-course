@echo off
echo ========================================
echo   PaperGuard Agent - Starting...
echo ========================================
echo.

cd /d "d:\agent course\paperguard_agent"

echo Checking dependencies...
pip show streamlit >/dev/null 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting Streamlit application...
echo Web interface will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run app.py

pause
