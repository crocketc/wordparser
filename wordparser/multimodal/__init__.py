"""多模态解析模块

提供与多模态AI模型交互的功能。
"""

from wordparser.multimodal.client import OpenAICompatibleVisionClient
from wordparser.multimodal.prompts import (
    TABLE_PROMPT,
    IMAGE_PROMPT,
    CHART_PROMPT,
    SMARTART_PROMPT,
    get_table_prompt,
    get_image_prompt,
    get_chart_prompt,
    get_smartart_prompt,
)

__all__ = [
    "OpenAICompatibleVisionClient",
    "TABLE_PROMPT",
    "IMAGE_PROMPT",
    "CHART_PROMPT",
    "SMARTART_PROMPT",
    "get_table_prompt",
    "get_image_prompt",
    "get_chart_prompt",
    "get_smartart_prompt",
]
