"""Word文档转Markdown解析库"""

from pathlib import Path
from typing import Tuple

from wordparser.config import *
from wordparser.core.parser import WordParser
from wordparser.core.report import ParseReport
from wordparser.exceptions import *

__all__ = [
    "WordParser",
    "ParseReport",
    "ParserConfig",
    "MultimodalConfig",
    "VisionModelConfig",
    "TOCPosition",
    "parse_word_to_markdown",
] + [name for name in dir() if name.endswith("Error") or name.endswith("Exception")]


def parse_word_to_markdown(
    docx_path: str | Path,
    output_path: str | Path | None = None,
    *,
    config: ParserConfig | None = None,
) -> Tuple[str, ParseReport]:
    """
    将Word文档解析为Markdown

    这是wordparser的主入口函数，提供简单的编程接口。

    Args:
        docx_path: Word文档路径
        output_path: 可选的输出文件路径，如果指定则保存到文件
        config: 可选的解析器配置，默认使用默认配置

    Returns:
        (Markdown内容, 解析报告)元组

    Raises:
        DocumentError: 文档不存在、格式不支持或文档损坏
        WordParserError: 解析过程中的其他错误

    Example:
        >>> from wordparser import parse_word_to_markdown
        >>> md_content, report = parse_word_to_markdown("document.docx")
        >>> print(md_content)
        >>> print(f"解析成功: {report.success}")
    """
    from pathlib import Path

    docx_path = Path(docx_path)
    output_dir = None
    if output_path:
        output_path = Path(output_path)
        output_dir = str(output_path.parent)

    parser = WordParser(config, output_dir=output_dir)
    markdown, report = parser.parse_with_report(docx_path)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding=config.encoding if config else "utf-8")
        report.output_path = output_path

    return markdown, report
