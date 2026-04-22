from __future__ import annotations

import re
from docx.document import Document

from wordparser.core.models import BlockType, ContentBlock, TitleNode
from wordparser.config import ParserConfig

_HEADING_NUMBER_RE = re.compile(
    r"^(\d+(\.\d+)*[\.\s、])+[\s]*"
)


class StructureParser:
    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()
        self._title_tree: list[TitleNode] = []

    def parse(self, doc: Document) -> list[ContentBlock]:
        blocks = []
        for para in doc.paragraphs:
            style_name = para.style.name if para.style else ""

            if style_name.startswith("Heading"):
                block = self._parse_heading(para, style_name)
                blocks.append(block)
            else:
                block = self._parse_paragraph(para)
                if block:
                    blocks.append(block)

        return blocks

    def get_title_tree(self) -> list[TitleNode]:
        return self._title_tree

    def _parse_heading(self, para, style_name: str) -> ContentBlock:
        level = self._extract_heading_level(style_name)
        text = para.text.strip()
        text = self._strip_heading_number(text)
        anchor = self._generate_anchor(text)

        node = TitleNode(level=level, text=text, anchor=anchor)
        self._add_to_title_tree(node)

        return ContentBlock(type=BlockType.HEADING, content=node)

    def _extract_heading_level(self, style_name: str) -> int:
        match = re.search(r"\d+", style_name)
        level = int(match.group()) if match else 1
        return min(level, self.config.max_heading_level)

    def _strip_heading_number(self, text: str) -> str:
        return _HEADING_NUMBER_RE.sub("", text).strip()

    def _generate_anchor(self, text: str) -> str:
        return re.sub(r"[^\w一-鿿]+", "", text)

    def _add_to_title_tree(self, node: TitleNode) -> None:
        self._insert_into_tree(self._title_tree, node)

    def _insert_into_tree(self, siblings: list[TitleNode], node: TitleNode) -> None:
        if not siblings:
            siblings.append(node)
            return

        last = siblings[-1]
        if node.level > last.level:
            self._insert_into_tree(last.children, node)
        else:
            siblings.append(node)

    def _parse_paragraph(self, para) -> ContentBlock | None:
        text = para.text.strip()
        if not text:
            return None

        style_name = para.style.name if para.style else ""

        if style_name.startswith("List"):
            return ContentBlock(type=BlockType.LIST, content=text)

        return ContentBlock(type=BlockType.PARAGRAPH, content=text)
