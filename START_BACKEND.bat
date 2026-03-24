@echo off
echo ========================================
echo   Arrancando Backend PIM
echo ========================================
echo.

cd backend

echo [1/2] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo [2/2] Arrancando servidor FastAPI en puerto 8000...
echo.
echo Backend estara disponible en: http://localhost:8000
echo API Docs en: http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

python -m uvicorn app.main:app --reload --port 8000

pause
