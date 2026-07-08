@echo off
setlocal EnableDelayedExpansion

title CareerCraft AI Launcher

echo.
echo  ============================================================
echo    CareerCraft AI ^| IBM watsonx.ai Powered
echo  ============================================================
echo.

:: ── Check Python ────────────────────────────────────────────────
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.11+ from https://www.python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo        Python %PYVER% found.

:: ── Virtual environment ──────────────────────────────────────────
echo.
echo [2/7] Setting up virtual environment...
if not exist "venv\" (
    echo        Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo        Virtual environment created.
) else (
    echo        Virtual environment already exists.
)

:: ── Activate venv ────────────────────────────────────────────────
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo        Virtual environment activated.

:: ── Upgrade pip ──────────────────────────────────────────────────
echo.
echo [3/7] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARN]  pip upgrade failed - continuing with existing version.
) else (
    echo        pip upgraded successfully.
)

:: ── Install wheel/setuptools first ──────────────────────────────
echo.
echo [4/7] Installing build tools...
python -m pip install --upgrade wheel setuptools --quiet
echo        Build tools ready.

:: ── Install core dependencies in order ──────────────────────────
echo.
echo [5/7] Installing dependencies (this may take a minute)...

:: Install in careful order to avoid conflicts
python -m pip install "numpy>=1.24.0" --quiet
if errorlevel 1 (
    echo [WARN]  numpy install failed - non-critical, continuing...
)

python -m pip install "Flask==3.0.3" "Werkzeug==3.0.3" "Jinja2==3.1.4" --quiet
python -m pip install "python-dotenv==1.0.1" "requests>=2.32.0" --quiet
python -m pip install "PyPDF2==3.0.1" "docx2txt==0.8" --quiet
python -m pip install "ibm-watsonx-ai>=1.0.0" --quiet
if errorlevel 1 (
    echo [WARN]  ibm-watsonx-ai install failed. AI features will use demo mode.
)

:: Install remaining from requirements.txt
python -m pip install -r requirements.txt --quiet
echo        Dependencies installed.

:: ── Verify critical imports ───────────────────────────────────────
echo.
echo [6/7] Verifying critical imports...
python -c "import flask; print('   [OK] Flask', flask.__version__)"
if errorlevel 1 ( echo [ERROR] Flask import failed. & pause & exit /b 1 )

python -c "import dotenv; print('   [OK] python-dotenv')"
if errorlevel 1 ( echo [ERROR] python-dotenv import failed. & pause & exit /b 1 )

python -c "import requests; print('   [OK] requests', requests.__version__)"
if errorlevel 1 ( echo [ERROR] requests import failed. & pause & exit /b 1 )

python -c "import numpy; print('   [OK] numpy', numpy.__version__)"
if errorlevel 1 ( echo [WARN]  numpy import failed - non-critical. )

python -c "import PyPDF2; print('   [OK] PyPDF2')" 2>nul || echo    [WARN] PyPDF2 not available - PDF upload disabled.
python -c "import docx2txt; print('   [OK] docx2txt')" 2>nul || echo    [WARN] docx2txt not available - DOCX upload disabled.

echo.
echo        All critical imports verified!

:: ── Create .env if missing ────────────────────────────────────────
echo.
echo [7/7] Checking configuration...
if not exist ".env" (
    xcopy /Y ".env.example" ".env*" >nul 2>&1
    echo.
    echo  ============================================================
    echo   [ACTION REQUIRED] .env file created from template.
    echo.
    echo   To connect IBM Granite AI:
    echo     1. Open .env in a text editor
    echo     2. Set IBM_API_KEY=your_actual_key
    echo     3. Set WATSONX_PROJECT_ID=your_project_id
    echo     4. Save and restart this script
    echo.
    echo   The app works in Demo Mode without IBM credentials.
    echo  ============================================================
    echo.
) else (
    :: Check if credentials are configured
    findstr /c:"IBM_API_KEY=your_ibm_api_key_here" .env >nul 2>&1
    if not errorlevel 1 (
        echo.
        echo  [INFO] IBM credentials not yet configured (.env has placeholder values).
        echo         App will run in Demo Mode. Edit .env to add real credentials.
        echo.
    ) else (
        echo        .env configuration found.
    )
)

:: ── Launch application ────────────────────────────────────────────
echo.
echo  ============================================================
echo    Starting CareerCraft AI on http://localhost:5000
echo  ============================================================
echo.
echo    Press CTRL+C to stop the server.
echo.

:: Check if port 5000 is in use and try to free it
netstat -ano | findstr ":5000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN]  Port 5000 is in use. Trying port 5001...
    set PORT=5001
    echo    Starting on http://localhost:5001
    echo.
) else (
    set PORT=5000
)

python app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start.
    echo         Check the error messages above.
    echo.
    pause
)

pause
