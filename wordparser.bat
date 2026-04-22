@echo off
cd /d "%~dp0"

echo WordParser v1.0
echo.

set /p FILE="拖入docx文件或输入路径: "

if "%FILE%"=="" exit /b

python -m wordparser_cli.main parse "%FILE%"

echo.
echo 按任意键退出...
pause >nul
