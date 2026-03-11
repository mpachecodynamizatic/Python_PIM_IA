@echo off
title PIM - Arrancando servicios
echo ============================================
echo   PIM - Product Information Management
echo ============================================
echo.

:: --- BACKEND ---
echo [1/2] Preparando Backend...
cd /d "%~dp0backend"

if not exist ".venv\Scripts\activate.bat" (
    echo     Creando entorno virtual...
    python -m venv .venv
)

start "PIM Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && pip install -r requirements.txt -q && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: --- FRONTEND ---
echo [2/2] Preparando Frontend...
cd /d "%~dp0frontend"
start "PIM Frontend" cmd /k "cd /d "%~dp0frontend" && npm install --silent && npm run dev"

echo.
echo ============================================
echo   Backend:  http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo   Login:    admin@pim.local / admin
echo ============================================
echo.
echo Pulsa cualquier tecla para cerrar esta ventana.
pause >nul
