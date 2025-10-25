@echo off
REM ========================================
REM ECLA AI Search - Arret en 1 clic
REM ========================================

echo.
echo ================================
echo   ECLA AI SEARCH - Arret
echo ================================
echo.

cd /d "%~dp0"

echo [1/2] Arret des conteneurs Docker...
docker compose down

if %ERRORLEVEL% EQU 0 (
    echo   OK Tous les services sont arretes !
) else (
    echo   ERREUR lors de l'arret
)

echo.
echo [2/2] Arret des processus Python...
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
echo   OK Processus Python arretes

echo.
echo ================================
echo   Tous les services sont arretes
echo ================================
echo.

pause

