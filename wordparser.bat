@echo off
setlocal

REM 工作目录切换到脚本所在位置
cd /d "%~dp0"

echo ========================================
echo  WordParser - Word文档转Markdown工具
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未找到 Python
    echo 请先安装 Python 3.8 或更高版本
    echo.
    pause
    exit /b 1
)

REM 检查 wordparser
python -c "import wordparser" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [提示] WordParser 未安装，正在安装...
    echo.
    pip install -e .
    echo.
    if errorlevel 1 (
        echo [错误] 安装失败
        pause
        exit /b 1
    )
)

echo.
echo ┌─────────────────────────────────────┐
echo │  请选择操作方式:                     │
echo │  1. 拖拽 .docx 文件到这个窗口        │
echo │  2. 直接输入文件路径后回车           │
echo └─────────────────────────────────────┘
echo.

REM 使用 call 确保即使出错也继续
set /p DOCX_PATH="> 文件路径: "

REM 检查输入
if not defined DOCX_PATH (
    echo.
    echo [提示] 未输入文件路径，退出
    pause
    exit /b 0
)

REM 去除可能的引号
set "DOCX_PATH=%DOCX_PATH:"=%"

REM 检查文件
if not exist "%DOCX_PATH%" (
    echo.
    echo [错误] 文件不存在: %DOCX_PATH%
    pause
    exit /b 1
)

echo.
echo [开始] 正在解析...
echo.

REM 执行解析
python -m wordparser_cli.main parse "%DOCX_PATH%"

echo.
echo ───────────────────────────────────────
echo [完成] 解析结束
echo ───────────────────────────────────────
echo.
pause
