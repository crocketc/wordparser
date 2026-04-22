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

REM 检查是否传入了文件参数（拖拽或命令行参数）
if "%~1"=="" (
    echo ========================================
    echo  WordParser - Word文档转Markdown工具
    echo ========================================
    echo.
    echo 使用方法:
    echo   1. 拖拽Word文档到这个图标上
    echo   2. 或者在命令行中运行: wordparser.bat 文档.docx
    echo.
    echo 示例:
    echo   wordparser.bat document.docx
    echo   wordparser.bat document.docx -o output.md
    echo.
    pause
    exit /b 0
)

REM 检查文件是否存在
if not exist "%~1" (
    echo 错误: 文件不存在: %~1
    pause
    exit /b 1
)

REM 检查文件扩展名
echo "%~1" | findstr /i "\.docx$" >nul
if errorlevel 1 (
    echo 错误: 不支持的文件格式，请使用 .docx 文件
    pause
    exit /b 1
)

echo 正在解析: %~1
echo.

REM 运行 WordParser CLI，传递所有参数
python -m wordparser_cli.main parse %*

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
