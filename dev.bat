@echo off
title Codenames Master DEV RUN
echo ============================================
echo   🚀 STARTING CODENAMES MASTER (DEV MODE)
echo   Watcher: watchdog (watchmedo)
echo ============================================

:: Перевірка чи встановлений watchdog
python -c "import watchdog" >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Library 'watchdog' not found. Installing...
    pip install watchdog
)

echo [OK] Watcher is ready. Monitoring for changes...
echo.

:: Запуск авто-рестарту
:: --recursive: стежити у всіх підпапках
:: --patterns="*.py": реагувати тільки на зміни в коді
:: --ignore-directories: ігнорувати системні папки
watchmedo auto-restart --directory=./ --recursive --patterns="*.py" --ignore-directories --python run.py

pause
