from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BlockType(Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    IMAGE = "image"
    FORMULA = "formula"
    TOC = "toc"
    TABLE_PENDING = "table_pending"
    IMAGE_PENDING = "image_pending"


@dataclass
class TitleNode:
    level: int
    text: str
    anchor: str
    children: list[TitleNode] = field(default_factory=list)


@dataclass
class ContentBlock:
    type: BlockType
    content: Any
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    metadata: dict = field(default_factory=dict)
    title_tree: list[TitleNode] = field(default_factory=list)
    content_blocks: list[ContentBlock] = field(default_factory=list)
