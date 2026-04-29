"""ELK日志配置模块

输出JSON格式结构化日志，便于Elasticsearch索引和Kibana分析。
标准字段：@timestamp, level, message, logger_name, context
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class ELKJsonFormatter(logging.Formatter):
    """ELK标准JSON格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化为JSON"""
        log_entry = {
            "@timestamp": datetime.now().isoformat(timespec="microseconds") + "+08:00",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 添加自定义上下文
        if hasattr(record, "context"):
            log_entry["context"] = record.context

        return json.dumps(log_entry, ensure_ascii=False)


def setup_elk_logging(
    level: int | str = logging.INFO,
    log_file: str | Path | None = None,
    enable_console: bool = True,
) -> None:
    """配置ELK日志系统

    Args:
        level: 日志级别 (默认: INFO)
        log_file: 日志文件路径 (可选)
        enable_console: 是否输出到控制台 (默认: True)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除现有handlers
    root_logger.handlers.clear()

    formatter = ELKJsonFormatter()

    # 控制台输出
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def configure_logging(logging_config) -> None:
    """根据 LoggingConfig 统一配置日志系统

    将相对路径 log_dir 基于 wordparser 包根目录解析为绝对路径，
    确保 CLI 和库调用日志文件落在同一目录。

    Args:
        logging_config: LoggingConfig 实例
    """
    if not logging_config.enabled:
        return

    level = getattr(logging, logging_config.level.upper(), logging.INFO)
    log_file = None
    if logging_config.log_file:
        log_file = logging_config.log_file
    elif logging_config.log_dir:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d")
        log_dir = Path(logging_config.log_dir)
        if not log_dir.is_absolute():
            log_dir = Path(__file__).parent.parent / log_dir
        log_file = str(log_dir / f"wordparser_{timestamp}.log")

    setup_elk_logging(level=level, log_file=log_file)


def get_logger(name: str) -> logging.Logger:
    """获取logger实例

    Args:
        name: logger名称 (通常使用 __name__)

    Returns:
        Logger实例
    """
    return logging.getLogger(name)


# 便捷方法：添加上下文信息
class LoggerAdapter:
    """带上下文的Logger适配器"""

    def __init__(self, logger: logging.Logger, context: dict[str, Any]):
        self.logger = logger
        self.context = context

    def _log_with_context(
        self,
        level: int,
        msg: str,
        extra_context: dict[str, Any] | None = None,
        *args,
        **kwargs,
    ):
        """带上下文记录日志"""
        context = self.context.copy()
        if extra_context:
            context.update(extra_context)

        extra = {"context": context} if context else {}
        self.logger.log(level, msg, extra=extra, *args, **kwargs)

    def info(self, msg: str, extra_context: dict[str, Any] | None = None, *args, **kwargs):
        self._log_with_context(logging.INFO, msg, extra_context, *args, **kwargs)

    def warning(self, msg: str, extra_context: dict[str, Any] | None = None, *args, **kwargs):
        self._log_with_context(logging.WARNING, msg, extra_context, *args, **kwargs)

    def error(self, msg: str, extra_context: dict[str, Any] | None = None, *args, **kwargs):
        self._log_with_context(logging.ERROR, msg, extra_context, *args, **kwargs)

    def debug(self, msg: str, extra_context: dict[str, Any] | None = None, *args, **kwargs):
        self._log_with_context(logging.DEBUG, msg, extra_context, *args, **kwargs)


def get_context_logger(name: str, context: dict[str, Any]) -> LoggerAdapter:
    """获取带上下文的logger

    Args:
        name: logger名称
        context: 上下文信息 (如 document_id, user_id 等)

    Example:
        logger = get_context_logger(__name__, {"document_id": "doc123"})
        logger.info("开始解析文档")
    """
    return LoggerAdapter(get_logger(name), context)
