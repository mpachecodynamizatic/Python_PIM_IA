@echo off
echo ========================================
echo   Arrancando Frontend PIM
echo ========================================
echo.

cd frontend

echo [1/1] Arrancando servidor de desarrollo Vite...
echo.
echo Frontend estara disponible en: http://localhost:5173
echo.
echo IMPORTANTE: Asegurate de que el backend este corriendo en http://localhost:8000
echo.
echo Credenciales de login:
echo   Email: admin@pim.local
echo   Password: admin
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

npm run dev

pause
