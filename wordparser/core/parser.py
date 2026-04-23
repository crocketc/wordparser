"""WordParser主解析器"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from wordparser.config import ParserConfig
from wordparser.core.chart_extractor import ChartExtractor
from wordparser.core.formulas import FormulaProcessor
from wordparser.core.models import ParsedDocument
from wordparser.core.postprocess import PostProcessor
from wordparser.core.preprocessor import Preprocessor
from wordparser.core.renderer import DocumentRenderer
from wordparser.core.report import ParseReport
from wordparser.core.smartart_extractor import SmartArtExtractor
from wordparser.core.structure import StructureParser
from wordparser.core.tables import TableProcessor
from wordparser.core.toc import TOCGenerator
from wordparser.exceptions import DocumentError, WordParserError
from wordparser.multimodal.parser import MultimodalParser

logger = logging.getLogger(__name__)


class WordParser:
    """Word文档转Markdown解析器"""

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()
        self._init_components()

    def _init_components(self) -> None:
        self.preprocessor = Preprocessor()
        self.structure_parser = StructureParser(self.config)
        self.table_processor = TableProcessor()
        self.formula_processor = FormulaProcessor()
        self.toc_generator = TOCGenerator()
        self.postprocessor = PostProcessor()

        self.chart_extractor = ChartExtractor()
        self.smartart_extractor = SmartArtExtractor()

        self.renderer = DocumentRenderer(
            libreoffice_path=self.config.libreoffice_path,
        )

        self.vision_client = None
        if self.config.multimodal:
            from wordparser.multimodal.client import OpenAICompatibleVisionClient
            self.vision_client = OpenAICompatibleVisionClient(
                base_url=self.config.multimodal.model.base_url,
                model=self.config.multimodal.model.model,
                temperature=self.config.multimodal.model.temperature,
            )

        self.multimodal_parser = MultimodalParser(
            vision_client=self.vision_client,
            renderer=self.renderer,
            enable_render_fallback=self.config.enable_render_fallback,
        )

    def parse(self, docx_path: str | Path) -> str:
        document = self._parse_document(docx_path)
        return document.metadata.get("markdown", "")

    def parse_with_report(self, docx_path: str | Path) -> tuple[str, ParseReport]:
        document = self._parse_document(docx_path)
        report = self._generate_report(document)
        markdown = document.metadata.get("markdown", "")
        return markdown, report

    def _ensure_docx(self, input_path: Path) -> Path:
        """确保输入为 .docx 格式，.doc 自动转换"""
        if self.renderer.is_doc(input_path):
            if not self.renderer.is_available():
                raise DocumentError(
                    "解析 .doc 文件需要 LibreOffice，请安装 LibreOffice 或配置 libreoffice_path"
                )
            logger.info(f"检测到 .doc 文件，自动转换为 .docx: {input_path}")
            return self.renderer.convert_doc_to_docx(input_path)
        return input_path

    def _parse_document(self, docx_path: str | Path) -> ParsedDocument:
        docx_path = Path(docx_path)

        if not docx_path.exists():
            raise DocumentError(f"文件不存在: {docx_path}")

        # .doc 自动转换
        docx_path = self._ensure_docx(docx_path)

        supported = {".docx", ".doc"}
        if docx_path.suffix.lower() not in supported:
            raise DocumentError(f"不支持的文件格式: {docx_path.suffix}")

        try:
            # 1. 加载并预处理
            from docx import Document as DocxDocument
            doc = DocxDocument(str(docx_path))
            doc = self.preprocessor.clean(doc)

            # 2. 结构解析
            blocks = self.structure_parser.parse(doc)
            title_tree = self.structure_parser.get_title_tree()

            # 3. 嵌入图片解析（零持久化，自动检测）
            image_descriptions = self._parse_images(doc)

            # 4. Chart 图表解析
            chart_descriptions = self._parse_charts(docx_path)

            # 5. SmartArt 解析
            smartart_descriptions = self._parse_smartarts(docx_path)

            # 6. 复杂表格解析
            table_sections = self._parse_complex_tables(doc)

            # 7. 构建 Markdown
            markdown_lines = []
            for block in blocks:
                if block.type.value == "heading":
                    node = block.content
                    markdown_lines.append(f"{'#' * node.level} {node.text}\n")
                elif block.type.value == "paragraph":
                    markdown_lines.append(f"{block.content}\n")
                elif block.type.value == "list":
                    markdown_lines.append(f"- {block.content}\n")

            # 图片描述
            if image_descriptions:
                markdown_lines.append("\n## 图片内容\n\n")
                for i, desc in enumerate(image_descriptions):
                    markdown_lines.append(f"### 图片 {i + 1}\n\n{desc}\n\n")

            # 图表描述
            if chart_descriptions:
                markdown_lines.append("\n## 图表内容\n\n")
                for desc in chart_descriptions:
                    markdown_lines.append(f"{desc}\n\n")

            # SmartArt 描述
            if smartart_descriptions:
                markdown_lines.append("\n## SmartArt 内容\n\n")
                for desc in smartart_descriptions:
                    markdown_lines.append(f"{desc}\n\n")

            # 复杂表格
            if table_sections:
                markdown_lines.append("\n## 复杂表格\n\n")
                for table_md in table_sections:
                    markdown_lines.append(f"{table_md}\n\n")

            markdown = "\n".join(markdown_lines)

            # 8. 后处理
            markdown = self.postprocessor.process(markdown)

            document = ParsedDocument(
                metadata={
                    "docx_path": str(docx_path),
                    "word_count": sum(len(p.text) for p in doc.paragraphs),
                    "paragraph_count": len(doc.paragraphs),
                    "image_count": len(image_descriptions),
                    "chart_count": len(chart_descriptions),
                    "smartart_count": len(smartart_descriptions),
                    "complex_table_count": len(table_sections),
                    "image_descriptions": image_descriptions,
                    "chart_descriptions": chart_descriptions,
                    "smartart_descriptions": smartart_descriptions,
                    "markdown": markdown,
                },
                title_tree=title_tree,
                content_blocks=blocks,
            )

            return document

        except Exception as e:
            if isinstance(e, (DocumentError, WordParserError)):
                raise
            raise WordParserError(f"文档解析失败: {e}") from e

    def _parse_images(self, doc) -> list[str]:
        """解析嵌入图片（零持久化）"""
        descriptions = []

        has_images = any("image" in rel.target_ref for rel in doc.part.rels.values())

        if not has_images:
            return descriptions

        # 延迟初始化 vision_client
        if not self.vision_client:
            from wordparser.multimodal.client import OpenAICompatibleVisionClient
            self.vision_client = OpenAICompatibleVisionClient(
                base_url="http://localhost:1234/v1",
                model="qwen3.5-9b",
                temperature=0.0,
            )
            self.multimodal_parser.vision_client = self.vision_client

        from wordparser.multimodal.prompts import IMAGE_PROMPT

        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    image_bytes = rel.target_part.blob
                    description = self.vision_client.parse_from_bytes(image_bytes, IMAGE_PROMPT)
                    descriptions.append(description)
                except Exception as e:
                    descriptions.append(f"[图片解析失败: {e}]")

        return descriptions

    def _parse_charts(self, docx_path: Path) -> list[str]:
        """解析 Chart 图表"""
        if not self.vision_client:
            return []

        try:
            chart_data_list = self.chart_extractor.extract(docx_path)
        except Exception as e:
            logger.warning(f"Chart 提取失败: {e}")
            return []

        descriptions = []
        for chart_data in chart_data_list:
            result = self.multimodal_parser.parse_chart_with_data(chart_data, docx_path)
            descriptions.append(result.content)

        return descriptions

    def _parse_smartarts(self, docx_path: Path) -> list[str]:
        """解析 SmartArt"""
        if not self.vision_client:
            return []

        try:
            smartart_data_list = self.smartart_extractor.extract(docx_path)
        except Exception as e:
            logger.warning(f"SmartArt 提取失败: {e}")
            return []

        descriptions = []
        for sa_data in smartart_data_list:
            result = self.multimodal_parser.parse_smartart_with_data(sa_data, docx_path)
            descriptions.append(result.content)

        return descriptions

    def _parse_complex_tables(self, doc) -> list[str]:
        """检测并解析复杂表格"""
        if not self.vision_client:
            return []

        results = []
        for table in doc.tables:
            if self.table_processor.is_complex(table):
                table_data = self.table_processor.extract_table_data(table)
                result = self.multimodal_parser.parse_complex_table(table_data)
                results.append(result.content)

        return results

    def _generate_report(self, document: ParsedDocument) -> ParseReport:
        from wordparser.core.report import ParseStats

        metadata = document.metadata

        def count_titles(nodes):
            count = 0
            for node in nodes:
                count += 1
                count += count_titles(node.children)
            return count

        heading_count = count_titles(document.title_tree)

        stats = ParseStats(
            total_headings=heading_count,
            total_paragraphs=metadata.get("paragraph_count", 0),
            total_tables=metadata.get("complex_table_count", 0),
            total_images=metadata.get("image_count", 0),
            multimodal_calls=0,
            multimodal_failures=0,
            processing_time=0.0,
        )

        return ParseReport(
            success=True,
            output_path=None,
            errors=[],
            stats=stats,
        )
