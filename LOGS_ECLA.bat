@echo off
REM ========================================
REM ECLA AI Search - Logs en 1 clic
REM ========================================

echo.
echo ================================
echo   ECLA AI SEARCH - Logs
echo ================================
echo.
echo Appuyez sur Ctrl+C pour arreter
echo.

cd /d "%~dp0"

docker compose logs -f

