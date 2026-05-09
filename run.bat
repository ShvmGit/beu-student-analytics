@echo off
setlocal

:: ─── BEU Result Intelligence Assistant ───
:: Quick-start script for Windows: sets up venv, installs deps, and launches the server.

cd /d "%~dp0"

set VENV_DIR=.venv
if "%PORT%"=="" set PORT=8000
if "%HOST%"=="" set HOST=0.0.0.0

:: ── 1. Create virtual environment if missing ──
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [1/5] Creating virtual environment...
    python -m venv %VENV_DIR%
)

:: ── 2. Activate virtual environment ──
call %VENV_DIR%\Scripts\activate.bat

:: ── 3. Install / update dependencies ──
@REM echo [2/5] Installing dependencies...
@REM pip install -q --upgrade pip
@REM pip install -q -r requirements.txt

:: ── 4. Ensure .env exists ──
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [WARNING] Created .env from .env.example — please fill in your API keys before first use.
    ) else (
        echo [WARNING] No .env file found. The app may fail without required environment variables.
    )
)

:: ── 5. Launch the server ──
echo.
echo Starting BEU Result Intelligence Assistant on http://localhost:%PORT%
echo Press Ctrl+C to stop.
echo.
uvicorn app.main:app --host localhost --port %PORT% --reload

endlocal
