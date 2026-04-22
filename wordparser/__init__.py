"""Word文档转Markdown解析库"""

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
] + [name for name in dir() if name.endswith("Error") or name.endswith("Exception")]
