"""WordParser主解析器"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wordparser.config import ParserConfig
from wordparser.core.formulas import FormulaProcessor
from wordparser.core.images import ImageExtractor
from wordparser.core.models import ParsedDocument
from wordparser.core.postprocess import PostProcessor
from wordparser.core.preprocessor import Preprocessor
from wordparser.core.report import ParseReport
from wordparser.core.structure import StructureParser
from wordparser.core.tables import TableProcessor
from wordparser.core.toc import TOCGenerator
from wordparser.exceptions import DocumentError, WordParserError


class WordParser:
    """Word文档转Markdown解析器"""

    def __init__(self, config: ParserConfig | None = None, output_dir: str | None = None) -> None:
        """
        初始化解析器

        Args:
            config: 解析器配置，默认使用默认配置
            output_dir: 图片输出目录，默认为None（不保存图片）
        """
        self.config = config or ParserConfig()
        self.output_dir = output_dir
        self._init_components()

    def _init_components(self) -> None:
        """初始化各个处理组件"""
        self.preprocessor = Preprocessor()
        self.structure_parser = StructureParser(self.config)
        self.table_processor = TableProcessor()
        self.formula_processor = FormulaProcessor()
        self.toc_generator = TOCGenerator()
        self.postprocessor = PostProcessor()

        # 初始化图片提取器（如果指定了输出目录）
        self.image_extractor = None
        if self.output_dir:
            from pathlib import Path
            images_dir = Path(self.output_dir) / "images"
            self.image_extractor = ImageExtractor(images_dir)

    def parse(self, docx_path: str | Path) -> str:
        """
        解析Word文档为Markdown文本

        Args:
            docx_path: Word文档路径

        Returns:
            Markdown文本

        Raises:
            DocumentError: 文档处理错误
            WordParserError: 其他处理错误
        """
        document = self._parse_document(docx_path)
        return document.metadata.get("markdown", "")

    def parse_with_report(self, docx_path: str | Path) -> tuple[str, ParseReport]:
        """
        解析Word文档为Markdown文本，并返回详细报告

        Args:
            docx_path: Word文档路径

        Returns:
            (Markdown文本, 解析报告)元组

        Raises:
            DocumentError: 文档处理错误
            WordParserError: 其他处理错误
        """
        document = self._parse_document(docx_path)
        report = self._generate_report(document)
        markdown = document.metadata.get("markdown", "")
        return markdown, report

    def _parse_document(self, docx_path: str | Path) -> ParsedDocument:
        """
        执行文档解析流程

        Args:
            docx_path: Word文档路径

        Returns:
            解析后的文档对象

        Raises:
            DocumentError: 文档处理错误
            WordParserError: 其他处理错误
        """
        docx_path = Path(docx_path)

        if not docx_path.exists():
            raise DocumentError(f"文件不存在: {docx_path}")

        if not docx_path.suffix.lower() == ".docx":
            raise DocumentError(f"不支持的文件格式: {docx_path.suffix}")

        try:
            # 1. 加载并预处理文档
            from docx import Document as DocxDocument
            doc = DocxDocument(str(docx_path))
            doc = self.preprocessor.clean(doc)

            # 2. 分析文档结构
            blocks = self.structure_parser.parse(doc)
            title_tree = self.structure_parser.get_title_tree()

            # 3. 提取图片（如果配置了图片提取器）
            images = []
            if self.image_extractor:
                images = self.image_extractor.extract(doc, image_prefix=f"{docx_path.stem}_image")

            # 4. 构建文档对象
            document = ParsedDocument(
                metadata={
                    "docx_path": str(docx_path),
                    "word_count": sum(len(p.text) for p in doc.paragraphs),
                    "paragraph_count": len(doc.paragraphs),
                    "image_count": len(images),
                    "images": images,
                },
                title_tree=title_tree,
                content_blocks=blocks,
            )

            # 5. 生成Markdown
            markdown_lines = []
            for block in blocks:
                if block.type.value == "heading":
                    node = block.content
                    level = node.level
                    markdown_lines.append(f"{'#' * level} {node.text}\n")
                elif block.type.value == "paragraph":
                    markdown_lines.append(f"{block.content}\n")
                elif block.type.value == "list":
                    markdown_lines.append(f"- {block.content}\n")

            # 6. 添加图片引用
            images = document.metadata.get("images", [])
            if images:
                markdown_lines.append("\n## 图片\n\n")
                for img in images:
                    rel_path = Path(img["path"]).relative_to(Path(self.output_dir))
                    markdown_lines.append(f"![图片{img['index']}]({rel_path})\n")

            markdown = "\n".join(markdown_lines)

            # 7. 后处理
            markdown = self.postprocessor.process(markdown)
            document.metadata["markdown"] = markdown

            return document

        except Exception as e:
            if isinstance(e, (DocumentError, WordParserError)):
                raise
            raise WordParserError(f"文档解析失败: {e}") from e

    def _generate_report(self, document: ParsedDocument) -> ParseReport:
        """
        生成解析报告

        Args:
            document: 解析后的文档对象

        Returns:
            解析报告
        """
        from wordparser.core.report import ParseStats

        metadata = document.metadata

        # 计算标题数量（从title_tree中递归计算）
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
            total_tables=0,  # 暂未实现
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
