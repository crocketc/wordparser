"""多模态内容解析器

支持两种模式：
1. XML + LLM：提取结构化数据，通过文本通道调用 LLM
2. 渲染 + 视觉：LibreOffice 渲染截图，通过图片通道调用视觉模型

降级链路：XML+LLM → 渲染+视觉 → 失败标记
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from wordparser.core.models import ChartData, SmartArtData
from wordparser.multimodal.prompts import (
    CHART_DATA_PROMPT,
    CHART_PROMPT,
    SMARTART_DATA_PROMPT,
    SMARTART_PROMPT,
    COMPLEX_TABLE_PROMPT,
    TABLE_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class MultimodalResult:
    """多模态解析结果"""
    content: str
    confidence: float
    metadata: dict[str, Any]

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"置信度必须在0-1之间，当前值: {self.confidence}")


class MultimodalParser:
    """多模态内容解析器（重构版）"""

    def __init__(
        self,
        vision_client=None,
        renderer=None,
        enable_render_fallback: bool = True,
    ):
        self.vision_client = vision_client
        self.renderer = renderer
        self.enable_render_fallback = enable_render_fallback

    def parse_chart_with_data(self, chart_data: ChartData, docx_path: Path | None = None) -> MultimodalResult:
        """解析 Chart，主路径 XML+LLM，降级渲染+视觉"""
        try:
            return self._parse_chart_via_llm(chart_data)
        except Exception as e:
            logger.warning(f"Chart LLM 解析失败: {e}")

        if self.enable_render_fallback and self.renderer and docx_path:
            try:
                return self._parse_chart_via_vision(docx_path)
            except Exception as e:
                logger.warning(f"Chart 视觉解析失败: {e}")

        return MultimodalResult(
            content=f"[图表解析失败: {chart_data.title or '未命名图表'}]",
            confidence=0.0,
            metadata={"type": "chart", "error": "all_methods_failed"},
        )

    def parse_smartart_with_data(self, smartart_data: SmartArtData, docx_path: Path | None = None) -> MultimodalResult:
        """解析 SmartArt，主路径 XML+LLM，降级渲染+视觉"""
        try:
            return self._parse_smartart_via_llm(smartart_data)
        except Exception as e:
            logger.warning(f"SmartArt LLM 解析失败: {e}")

        if self.enable_render_fallback and self.renderer and docx_path:
            try:
                return self._parse_smartart_via_vision(docx_path)
            except Exception as e:
                logger.warning(f"SmartArt 视觉解析失败: {e}")

        return MultimodalResult(
            content="[SmartArt 解析失败]",
            confidence=0.0,
            metadata={"type": "smartart", "error": "all_methods_failed"},
        )

    def parse_complex_table(self, table_data: str, docx_path: Path | None = None) -> MultimodalResult:
        """解析复杂表格，主路径 LLM，降级渲染+视觉"""
        try:
            return self._parse_table_via_llm(table_data)
        except Exception as e:
            logger.warning(f"复杂表格 LLM 解析失败: {e}")

        if self.enable_render_fallback and self.renderer and docx_path:
            try:
                return self._parse_table_via_vision(docx_path)
            except Exception as e:
                logger.warning(f"复杂表格视觉解析失败: {e}")

        return MultimodalResult(
            content="[复杂表格解析失败]",
            confidence=0.0,
            metadata={"type": "table", "error": "all_methods_failed"},
        )

    # --- 主路径：XML + LLM ---

    def _parse_chart_via_llm(self, chart_data: ChartData) -> MultimodalResult:
        from wordparser.core.chart_extractor import ChartExtractor
        extractor = ChartExtractor()
        formatted = extractor.format_for_llm(chart_data)
        prompt = CHART_DATA_PROMPT.format(chart_data=formatted)

        result = self.vision_client.parse_text(prompt)
        return MultimodalResult(
            content=result,
            confidence=0.9,
            metadata={"type": "chart", "method": "xml_llm"},
        )

    def _parse_smartart_via_llm(self, smartart_data: SmartArtData) -> MultimodalResult:
        from wordparser.core.smartart_extractor import SmartArtExtractor
        extractor = SmartArtExtractor()
        formatted = extractor.format_for_llm(smartart_data)
        prompt = SMARTART_DATA_PROMPT.format(smartart_data=formatted)

        result = self.vision_client.parse_text(prompt)
        return MultimodalResult(
            content=result,
            confidence=0.9,
            metadata={"type": "smartart", "method": "xml_llm"},
        )

    def _parse_table_via_llm(self, table_data: str) -> MultimodalResult:
        prompt = COMPLEX_TABLE_PROMPT.format(table_data=table_data)
        result = self.vision_client.parse_text(prompt)
        return MultimodalResult(
            content=result,
            confidence=0.85,
            metadata={"type": "table", "method": "xml_llm"},
        )

    # --- 降级路径：渲染 + 视觉 ---

    def _parse_chart_via_vision(self, docx_path: Path) -> MultimodalResult:
        image_bytes = self.renderer.render_page_to_image(docx_path)
        result = self.vision_client.parse_from_bytes(image_bytes, CHART_PROMPT)
        return MultimodalResult(
            content=result,
            confidence=0.8,
            metadata={"type": "chart", "method": "render_vision"},
        )

    def _parse_smartart_via_vision(self, docx_path: Path) -> MultimodalResult:
        image_bytes = self.renderer.render_page_to_image(docx_path)
        result = self.vision_client.parse_from_bytes(image_bytes, SMARTART_PROMPT)
        return MultimodalResult(
            content=result,
            confidence=0.8,
            metadata={"type": "smartart", "method": "render_vision"},
        )

    def _parse_table_via_vision(self, docx_path: Path) -> MultimodalResult:
        image_bytes = self.renderer.render_page_to_image(docx_path)
        result = self.vision_client.parse_from_bytes(image_bytes, TABLE_PROMPT)
        return MultimodalResult(
            content=result,
            confidence=0.8,
            metadata={"type": "table", "method": "render_vision"},
        )
