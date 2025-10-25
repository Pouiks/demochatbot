@echo off
REM ========================================
REM ECLA AI Search - Lancement en 1 clic
REM ========================================

echo.
echo ================================
echo   ECLA AI SEARCH - Demarrage
echo ================================
echo.

REM Lancer le script PowerShell avec execution policy bypass
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1"

REM Si le script echoue, garder la fenetre ouverte
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR : Le script a echoue
    echo.
    pause
)

