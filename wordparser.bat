@echo off
cd /d "%~dp0"

echo WordParser v1.0
echo.

set /p FILE=Drag docx file here or enter path: 

if "%FILE%"=="" exit /b

REM Get filename without extension and change to .md
for %%i in ("%FILE%") do (
    set OUTFILE=%%~dpni.md
)

echo.
echo Input: %FILE%
echo Output: %OUTFILE%
echo.
echo Parsing...
echo.

python -m wordparser_cli.main parse "%FILE%" -o "%OUTFILE%"

echo.
echo Done! Saved to: %OUTFILE%
echo.
pause
