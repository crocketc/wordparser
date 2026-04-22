@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 wordparser 是否安装
python -c "import wordparser" >nul 2>&1
if errorlevel 1 (
    echo WordParser 未安装，正在尝试安装...
    pip install -e .
    if errorlevel 1 (
        echo 安装失败！请手动运行: pip install -e .
        pause
        exit /b 1
    )
    echo WordParser 安装成功！
    echo.
)

REM 如果没有传入参数，提示用户输入
if "%~1"=="" (
    echo ========================================
    echo  WordParser - Word文档转Markdown工具
    echo ========================================
    echo.
    echo 请输入Word文档路径，或直接拖拽文件到这个窗口：
    echo.
    set /p DOCX_PATH="文件路径: "

    REM 检查用户是否输入了内容
    if "!DOCX_PATH!"=="" (
        echo 未输入文件路径，退出。
        pause
        exit /b 0
    )

    REM 去除路径两端的引号（如果有）
    set "DOCX_PATH=!DOCX_PATH:"=!"
) else (
    REM 使用传入的参数
    set "DOCX_PATH=%~1"
)

REM 检查文件是否存在
if not exist "!DOCX_PATH!" (
    echo 错误: 文件不存在: !DOCX_PATH!
    pause
    exit /b 1
)

REM 检查文件扩展名
echo "!DOCX_PATH!" | findstr /i "\.docx$" >nul
if errorlevel 1 (
    echo 错误: 不支持的文件格式，请使用 .docx 文件
    pause
    exit /b 1
)

echo.
echo 正在解析: !DOCX_PATH!
echo.

REM 运行 WordParser CLI
python -m wordparser_cli.main parse "!DOCX_PATH!" %~2 %~3 %~4 %~5

if errorlevel 1 (
    echo.
    echo 解析失败！
    pause
) else (
    echo.
    echo 解析完成！
    pause
)

endlocal
