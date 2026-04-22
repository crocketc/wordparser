@echo off
REM WordParser 启动脚本
REM 用于在 Windows 系统上便捷地运行 WordParser CLI

setlocal enabledelayedexpansion

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 wordparser 是否安装，未安装则自动安装
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
)

REM 运行 WordParser CLI，传递所有参数
python -m wordparser_cli.main %*

REM 如果出错则暂停
if errorlevel 1 (
    echo.
    echo 程序执行出错
    pause
)

endlocal
