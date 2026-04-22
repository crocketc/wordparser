@echo off
cd /d "%~dp0"

echo WordParser v1.0
echo.

set /p FILE=Drag docx file here or enter path: 

if "%FILE%"=="" exit /b

python -m wordparser_cli.main parse "%FILE%"

echo.
echo Press any key to exit...
pause
