# Word文档转Markdown解析器 - 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个Python库，将Word文档(.docx)解析为结构化Markdown，支持多模态内容识别，提供编程接口和CLI工具。

**Architecture:** 模块化管道架构，文档依次经过预处理→结构解析→富内容处理→目录生成→后处理。多模态内容通过OpenAI兼容接口调用视觉模型，支持并行处理。

**Tech Stack:** Python 3.10+, python-docx, httpx, lxml, Pillow, pdf2image, pydantic, typer, rich

---

## 文件结构总览

```
Document_Parsing/
├── wordparser/
│   ├── __init__.py                  # 导出公开API
│   ├── config.py                    # ParserConfig, VisionModelConfig, MultimodalConfig, TOCPosition
│   ├── exceptions.py                # 异常体系
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py                # BlockType, TitleNode, ContentBlock, ParsedDocument
│   │   ├── report.py                # ParseReport, ParseError, ParseStats
│   │   ├── parser.py                # WordParser 主解析器
│   │   ├── preprocessor.py          # 文档预处理
│   │   ├── structure.py             # 标题/段落/列表解析
│   │   ├── tables.py                # 表格处理
│   │   ├── images.py                # 图片处理
│   │   ├── formulas.py              # OMML→LaTeX
│   │   ├── renderer.py              # LibreOffice渲染
│   │   ├── toc.py                   # 目录生成
│   │   └── postprocess.py           # 后处理
│   └── multimodal/
│       ├── __init__.py
│       ├── client.py                # OpenAI兼容HTTP客户端
│       ├── parser.py                # 多模态解析器
│       ├── parallel.py              # 并行处理器
│       └── prompts.py               # Prompt模板
├── wordparser_cli/
│   ├── __init__.py
│   ├── main.py                      # typer app入口
│   └── commands/
│       ├── __init__.py
│       ├── parse_cmd.py
│       ├── multimodal_cmd.py
│       └── config_cmd.py
├── wordparser.bat
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # 共享fixtures
│   ├── test_models.py
│   ├── test_preprocessor.py
│   ├── test_structure.py
│   ├── test_tables.py
│   ├── test_images.py
│   ├── test_formulas.py
│   ├── test_toc.py
│   ├── test_postprocess.py
│   ├── test_parser.py
│   ├── test_client.py
│   ├── test_multimodal.py
│   └── fixtures/
│       └── samples/
├── docs/
│   ├── 2026-04-22-word-parser-design.md
│   └── 2026-04-22-word-parser-plan.md
├── examples/
│   ├── basic_usage.py
│   └── advanced_config.py
├── pyproject.toml
└── README.md
```

---

## Phase 1: 项目骨架与核心模型

### Task 1: 初始化项目结构

**Files:**
- Create: `pyproject.toml`
- Create: `wordparser/__init__.py`
- Create: `wordparser/core/__init__.py`
- Create: `wordparser/multimodal/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "wordparser"
version = "0.1.0"
description = "Word文档转Markdown解析库"
requires-python = ">=3.10"

dependencies = [
    "python-docx>=1.0",
    "httpx>=0.24",
    "pydantic>=2.0",
    "pdf2image>=1.16",
    "lxml>=4.9",
    "Pillow>=10.0",
]

[project.optional-dependencies]
cli = [
    "typer>=0.9",
    "rich>=13.0",
]
dev = [
    "pytest>=7.0",
    "pytest-cov",
]

[project.scripts]
wordparser = "wordparser_cli.main:app"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 创建目录结构**

```bash
mkdir -p wordparser/core wordparser/multimodal wordparser_cli/commands tests/fixtures/samples examples docs
```

- [ ] **Step 3: 创建 __init__.py 文件**

`wordparser/__init__.py`:
```python
"""Word文档转Markdown解析库"""
```

`wordparser/core/__init__.py`:
```python
```

`wordparser/multimodal/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

- [ ] **Step 4: 创建 tests/conftest.py**

```python
"""共享测试fixtures"""
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "samples"

@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR
```

- [ ] **Step 5: 安装依赖并验证**

```bash
pip install -e ".[dev,cli]"
pytest --co -q
```

Expected: 无错误，0 tests collected

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "feat: init project structure with pyproject.toml"
```

---

### Task 2: 数据模型（models.py）

**Files:**
- Create: `wordparser/core/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: 写测试**

`tests/test_models.py`:
```python
from wordparser.core.models import (
    BlockType, TitleNode, ContentBlock, ParsedDocument
)


def test_block_type_values():
    assert BlockType.HEADING.value == "heading"
    assert BlockType.PARAGRAPH.value == "paragraph"
    assert BlockType.TABLE.value == "table"
    assert BlockType.IMAGE.value == "image"
    assert BlockType.FORMULA.value == "formula"
    assert BlockType.LIST.value == "list"
    assert BlockType.TOC.value == "toc"
    assert BlockType.TABLE_PENDING.value == "table_pending"
    assert BlockType.IMAGE_PENDING.value == "image_pending"


def test_title_node_defaults():
    node = TitleNode(level=1, text="Hello", anchor="hello")
    assert node.level == 1
    assert node.text == "Hello"
    assert node.anchor == "hello"
    assert node.children == []


def test_title_node_tree():
    child = TitleNode(level=2, text="Child", anchor="child")
    parent = TitleNode(level=1, text="Parent", anchor="parent", children=[child])
    assert len(parent.children) == 1
    assert parent.children[0].text == "Child"


def test_content_block():
    block = ContentBlock(type=BlockType.PARAGRAPH, content="Hello world")
    assert block.type == BlockType.PARAGRAPH
    assert block.content == "Hello world"
    assert block.metadata == {}


def test_content_block_with_metadata():
    block = ContentBlock(
        type=BlockType.TABLE,
        content="| a | b |",
        metadata={"rows": 2, "cols": 2}
    )
    assert block.metadata["rows"] == 2


def test_parsed_document_defaults():
    doc = ParsedDocument()
    assert doc.metadata == {}
    assert doc.title_tree == []
    assert doc.content_blocks == []


def test_parsed_document_with_data():
    heading = TitleNode(level=1, text="Title", anchor="title")
    block = ContentBlock(type=BlockType.HEADING, content=heading)
    doc = ParsedDocument(
        title_tree=[heading],
        content_blocks=[block]
    )
    assert len(doc.title_tree) == 1
    assert len(doc.content_blocks) == 1
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 models.py**

`wordparser/core/models.py`:
```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_models.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/models.py tests/test_models.py
git commit -m "feat: add core data models (BlockType, TitleNode, ContentBlock, ParsedDocument)"
```

---

### Task 3: 异常体系与配置类

**Files:**
- Create: `wordparser/exceptions.py`
- Create: `wordparser/config.py`
- Create: `tests/test_exceptions.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 写测试**

`tests/test_exceptions.py`:
```python
import pytest
from wordparser.exceptions import (
    WordParserError,
    DocumentError,
    DocumentEncryptedError,
    DocumentCorruptedError,
    UnsupportedFormatError,
    ContentProcessError,
    TableProcessError,
    ImageProcessError,
    MultimodalAPIError,
)


def test_exception_hierarchy():
    assert issubclass(DocumentError, WordParserError)
    assert issubclass(DocumentEncryptedError, DocumentError)
    assert issubclass(DocumentCorruptedError, DocumentError)
    assert issubclass(UnsupportedFormatError, DocumentError)
    assert issubclass(ContentProcessError, WordParserError)
    assert issubclass(TableProcessError, ContentProcessError)
    assert issubclass(ImageProcessError, ContentProcessError)
    assert issubclass(MultimodalAPIError, ContentProcessError)


def test_document_encrypted_is_fatal():
    with pytest.raises(DocumentEncryptedError):
        raise DocumentEncryptedError("test.docx")
```

`tests/test_config.py`:
```python
from wordparser.config import (
    ParserConfig,
    VisionModelConfig,
    MultimodalConfig,
    TOCPosition,
)


def test_parser_config_defaults():
    config = ParserConfig()
    assert config.max_heading_level == 6
    assert config.encoding == "utf-8"
    assert config.multimodal is None
    assert config.libreoffice_path is None
    assert config.generate_toc is True
    assert config.toc_position == TOCPosition.AFTER_TITLE
    assert config.include_header_footer is False
    assert config.include_comments is False


def test_vision_model_config_defaults():
    config = VisionModelConfig()
    assert config.base_url == "http://localhost:1234/v1"
    assert config.api_key is None
    assert config.model == "qwen2-vl-7b"
    assert config.timeout == 60
    assert config.temperature == 0.0


def test_multimodal_config_defaults():
    config = MultimodalConfig()
    assert config.max_concurrent == 4
    assert config.batch_delay == 0.1
    assert config.retry_on_failure is True
    assert isinstance(config.model, VisionModelConfig)


def test_parser_config_with_multimodal():
    config = ParserConfig(
        multimodal=MultimodalConfig(
            model=VisionModelConfig(base_url="http://custom:8080/v1")
        )
    )
    assert config.multimodal.model.base_url == "http://custom:8080/v1"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_exceptions.py tests/test_config.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 exceptions.py**

`wordparser/exceptions.py`:
```python
class WordParserError(Exception):
    pass


class DocumentError(WordParserError):
    pass


class DocumentEncryptedError(DocumentError):
    pass


class DocumentCorruptedError(DocumentError):
    pass


class UnsupportedFormatError(DocumentError):
    pass


class ContentProcessError(WordParserError):
    pass


class TableProcessError(ContentProcessError):
    pass


class ImageProcessError(ContentProcessError):
    pass


class MultimodalAPIError(ContentProcessError):
    pass
```

- [ ] **Step 4: 实现 config.py**

`wordparser/config.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TOCPosition(Enum):
    BEFORE_TITLE = "before_title"
    AFTER_TITLE = "after_title"


@dataclass
class VisionModelConfig:
    base_url: str = "http://localhost:1234/v1"
    api_key: str | None = None
    model: str = "qwen2-vl-7b"
    timeout: int = 60
    temperature: float = 0.0


@dataclass
class MultimodalConfig:
    max_concurrent: int = 4
    batch_delay: float = 0.1
    retry_on_failure: bool = True
    model: VisionModelConfig = field(default_factory=VisionModelConfig)


@dataclass
class ParserConfig:
    max_heading_level: int = 6
    encoding: str = "utf-8"
    multimodal: MultimodalConfig | None = None
    libreoffice_path: str | None = None
    generate_toc: bool = True
    toc_position: TOCPosition = TOCPosition.AFTER_TITLE
    include_header_footer: bool = False
    include_comments: bool = False
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_exceptions.py tests/test_config.py -v
```

Expected: 全部通过

- [ ] **Step 6: Commit**

```bash
git add wordparser/exceptions.py wordparser/config.py tests/test_exceptions.py tests/test_config.py
git commit -m "feat: add exception hierarchy and configuration classes"
```

---

### Task 4: 解析报告模型

**Files:**
- Create: `wordparser/core/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: 写测试**

`tests/test_report.py`:
```python
from wordparser.core.report import ParseReport, ParseError, ParseStats


def test_parse_stats_defaults():
    stats = ParseStats()
    assert stats.total_headings == 0
    assert stats.total_paragraphs == 0
    assert stats.total_tables == 0
    assert stats.total_images == 0
    assert stats.multimodal_calls == 0
    assert stats.multimodal_failures == 0
    assert stats.processing_time == 0.0


def test_parse_error():
    err = ParseError(type="table", message="合并单元格过多")
    assert err.type == "table"
    assert err.message == "合并单元格过多"
    assert err.fatal is False
    assert err.location is None


def test_parse_report_no_errors():
    report = ParseReport(success=True, output_path=None, errors=[], stats=ParseStats())
    assert report.has_errors() is False
    assert report.has_fatal_errors() is False


def test_parse_report_with_errors():
    errors = [
        ParseError(type="image", message="解析失败", fatal=False),
        ParseError(type="document", message="损坏", fatal=True),
    ]
    report = ParseReport(success=False, output_path=None, errors=errors, stats=ParseStats())
    assert report.has_errors() is True
    assert report.has_fatal_errors() is True
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_report.py -v
```

- [ ] **Step 3: 实现 report.py**

`wordparser/core/report.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseStats:
    total_headings: int = 0
    total_paragraphs: int = 0
    total_tables: int = 0
    total_images: int = 0
    multimodal_calls: int = 0
    multimodal_failures: int = 0
    processing_time: float = 0.0


@dataclass
class ParseError:
    type: str
    message: str
    fatal: bool = False
    location: str | None = None


@dataclass
class ParseReport:
    success: bool
    output_path: Path | None
    errors: list[ParseError]
    stats: ParseStats

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_fatal_errors(self) -> bool:
        return any(e.fatal for e in self.errors)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_report.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/report.py tests/test_report.py
git commit -m "feat: add ParseReport, ParseError, ParseStats models"
```

---

## Phase 2: 核心解析流程

### Task 5: 预处理模块

**Files:**
- Create: `wordparser/core/preprocessor.py`
- Create: `tests/test_preprocessor.py`
- Create: `tests/fixtures/samples/simple.docx` (用python-docx生成)

- [ ] **Step 1: 创建测试用Word文档的fixture**

在 `tests/conftest.py` 末尾追加:

```python
from docx import Document
from docx.shared import Pt
import tempfile


@pytest.fixture
def simple_docx(tmp_path):
    """创建一个简单的测试用Word文档"""
    doc = Document()
    doc.add_heading("测试标题", level=1)
    doc.add_paragraph("这是第一个段落。")
    doc.add_paragraph("这是第二个段落。")
    path = tmp_path / "simple.docx"
    doc.save(str(path))
    return path


@pytest.fixture
def docx_with_blank_paragraphs(tmp_path):
    """创建含空白段落的Word文档"""
    doc = Document()
    doc.add_paragraph("有内容")
    doc.add_paragraph("")
    doc.add_paragraph("   ")
    doc.add_paragraph("\t")
    doc.add_paragraph("也有内容")
    path = tmp_path / "blanks.docx"
    doc.save(str(path))
    return path
```

- [ ] **Step 2: 写测试**

`tests/test_preprocessor.py`:
```python
from docx import Document
from wordparser.core.preprocessor import Preprocessor


def test_remove_blank_paragraphs(docx_with_blank_paragraphs):
    doc = Document(str(docx_with_blank_paragraphs))
    proc = Preprocessor()
    result = proc.clean(doc)
    texts = [p.text for p in result.paragraphs if p.text.strip()]
    assert texts == ["有内容", "也有内容"]


def test_clean_control_characters(tmp_path):
    from docx import Document
    doc = Document()
    doc.add_paragraph("Hello\x00World\x0c")
    doc.add_paragraph("正常文本")
    path = tmp_path / "control.docx"
    doc.save(str(path))

    loaded = Document(str(path))
    proc = Preprocessor()
    result = proc.clean(loaded)
    texts = [p.text for p in result.paragraphs]
    assert "\x00" not in texts[0]
    assert "\x0c" not in texts[0]


def test_normalize_whitespace(tmp_path):
    from docx import Document
    doc = Document()
    doc.add_paragraph("  多余空格  ")
    doc.add_paragraph("正常")
    path = tmp_path / "whitespace.docx"
    doc.save(str(path))

    loaded = Document(str(path))
    proc = Preprocessor()
    result = proc.clean(loaded)
    text = result.paragraphs[0].text
    assert text == "多余空格"
```

- [ ] **Step 3: 运行测试确认失败**

```bash
pytest tests/test_preprocessor.py -v
```

- [ ] **Step 4: 实现 preprocessor.py**

`wordparser/core/preprocessor.py`:
```python
from __future__ import annotations

import re
from docx.document import Document


class Preprocessor:
    CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

    def clean(self, doc: Document) -> Document:
        self._remove_blank_paragraphs(doc)
        self._clean_control_characters(doc)
        self._normalize_whitespace(doc)
        return doc

    def _remove_blank_paragraphs(self, doc: Document) -> None:
        for para in list(doc.paragraphs):
            if not para.text.strip():
                parent = para._element.getparent()
                if parent is not None:
                    parent.remove(para._element)

    def _clean_control_characters(self, doc: Document) -> None:
        for para in doc.paragraphs:
            if self.CONTROL_CHARS_RE.search(para.text):
                for run in para.runs:
                    run.text = self.CONTROL_CHARS_RE.sub("", run.text)

    def _normalize_whitespace(self, doc: Document) -> None:
        for para in doc.paragraphs:
            for run in para.runs:
                run.text = run.text.strip()
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_preprocessor.py -v
```

- [ ] **Step 6: Commit**

```bash
git add wordparser/core/preprocessor.py tests/test_preprocessor.py tests/conftest.py
git commit -m "feat: add Preprocessor - clean blank paragraphs, control chars, whitespace"
```

---

### Task 6: 结构解析模块（标题 + 段落 + 列表）

**Files:**
- Create: `wordparser/core/structure.py`
- Create: `tests/test_structure.py`

- [ ] **Step 1: 在 conftest.py 追加fixtures**

```python
@pytest.fixture
def docx_with_headings(tmp_path):
    """多级标题文档"""
    doc = Document()
    doc.add_heading("一级标题", level=1)
    doc.add_paragraph("正文段落1")
    doc.add_heading("二级标题", level=2)
    doc.add_paragraph("正文段落2")
    doc.add_heading("三级标题", level=3)
    doc.add_paragraph("正文段落3")
    path = tmp_path / "headings.docx"
    doc.save(str(path))
    return path


@pytest.fixture
def docx_with_numbered_headings(tmp_path):
    """带序号的标题"""
    doc = Document()
    doc.add_heading("1. 项目背景", level=1)
    doc.add_heading("1.1 技术方案", level=2)
    doc.add_heading("1.1.1 详细设计", level=3)
    path = tmp_path / "numbered.docx"
    doc.save(str(path))
    return path
```

- [ ] **Step 2: 写测试**

`tests/test_structure.py`:
```python
from docx import Document
from wordparser.core.structure import StructureParser
from wordparser.core.models import BlockType


def test_parse_headings(docx_with_headings):
    doc = Document(str(docx_with_headings))
    parser = StructureParser()
    blocks = parser.parse(doc)

    headings = [b for b in blocks if b.type == BlockType.HEADING]
    assert len(headings) == 3
    assert headings[0].content.level == 1
    assert headings[0].content.text == "一级标题"
    assert headings[1].content.level == 2
    assert headings[2].content.level == 3


def test_parse_paragraphs(docx_with_headings):
    doc = Document(str(docx_with_headings))
    parser = StructureParser()
    blocks = parser.parse(doc)

    paras = [b for b in blocks if b.type == BlockType.PARAGRAPH]
    assert len(paras) == 3
    assert paras[0].content == "正文段落1"


def test_strip_heading_numbers(docx_with_numbered_headings):
    doc = Document(str(docx_with_numbered_headings))
    parser = StructureParser()
    blocks = parser.parse(doc)

    headings = [b for b in blocks if b.type == BlockType.HEADING]
    assert headings[0].content.text == "项目背景"
    assert headings[1].content.text == "技术方案"
    assert headings[2].content.text == "详细设计"


def test_title_tree_built(docx_with_headings):
    doc = Document(str(docx_with_headings))
    parser = StructureParser()
    blocks = parser.parse(doc)

    tree = parser.get_title_tree()
    assert len(tree) == 1
    assert tree[0].level == 1
    assert tree[0].text == "一级标题"
    assert len(tree[0].children) == 1
    assert tree[0].children[0].level == 2


def test_heading_anchor_generation(docx_with_headings):
    doc = Document(str(docx_with_headings))
    parser = StructureParser()
    blocks = parser.parse(doc)

    headings = [b for b in blocks if b.type == BlockType.HEADING]
    assert headings[0].content.anchor == "一级标题"
    assert headings[1].content.anchor == "二级标题"
```

- [ ] **Step 3: 运行测试确认失败**

```bash
pytest tests/test_structure.py -v
```

- [ ] **Step 4: 实现 structure.py**

`wordparser/core/structure.py`:
```python
from __future__ import annotations

import re
from docx.document import Document
from docx.enum.text import WD_PARAGRAPH_STYLE

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
        if not self._title_tree:
            self._title_tree.append(node)
            return

        self._insert_into_tree(self._title_tree, node)

    def _insert_into_tree(self, siblings: list[TitleNode], node: TitleNode) -> None:
        last = siblings[-1]
        if node.level > last.level:
            last.children.append(node)
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
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_structure.py -v
```

- [ ] **Step 6: Commit**

```bash
git add wordparser/core/structure.py tests/test_structure.py tests/conftest.py
git commit -m "feat: add StructureParser - headings with number stripping, paragraphs, lists"
```

---

### Task 7: 后处理模块

**Files:**
- Create: `wordparser/core/postprocess.py`
- Create: `tests/test_postprocess.py`

- [ ] **Step 1: 写测试**

`tests/test_postprocess.py`:
```python
from wordparser.core.postprocess import PostProcessor


def test_normalize_line_breaks():
    proc = PostProcessor()
    result = proc.process("段落1\n\n\n\n段落2")
    assert result == "段落1\n\n段落2"


def test_trim_lines():
    proc = PostProcessor()
    result = proc.process("  行1  \n  行2  ")
    assert "行1" in result
    assert "行2" in result


def test_remove_trailing_whitespace():
    proc = PostProcessor()
    result = proc.process("内容  \n\n  ")
    assert result.strip() == "内容"


def test_ensure_blank_line_before_heading():
    proc = PostProcessor()
    result = proc.process("段落内容\n# 标题")
    assert result == "段落内容\n\n# 标题"


def test_ensure_blank_line_after_heading():
    proc = PostProcessor()
    result = proc.process("# 标题\n段落内容")
    assert result == "# 标题\n\n段落内容"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_postprocess.py -v
```

- [ ] **Step 3: 实现 postprocess.py**

`wordparser/core/postprocess.py`:
```python
from __future__ import annotations

import re


class PostProcessor:
    MULTIPLE_BLANKS_RE = re.compile(r"\n{3,}")
    HEADING_RE = re.compile(r"^(#{1,6}\s)", re.MULTILINE)

    def process(self, markdown: str) -> str:
        markdown = self._normalize_blank_lines(markdown)
        markdown = self._trim_lines(markdown)
        markdown = self._ensure_heading_spacing(markdown)
        markdown = markdown.strip() + "\n"
        return markdown

    def _normalize_blank_lines(self, text: str) -> str:
        return self.MULTIPLE_BLANKS_RE.sub("\n\n", text)

    def _trim_lines(self, text: str) -> str:
        lines = text.split("\n")
        return "\n".join(line.strip() for line in lines)

    def _ensure_heading_spacing(self, text: str) -> str:
        text = re.sub(r"([^\n])\n(#{1,6}\s)", r"\1\n\n\2", text)
        text = re.sub(r"(#{1,6}\s[^\n]+)\n([^\n#])", r"\1\n\n\2", text)
        return text
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_postprocess.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/postprocess.py tests/test_postprocess.py
git commit -m "feat: add PostProcessor - normalize line breaks, heading spacing, trim"
```

---

## Phase 3: 表格与图片处理

### Task 8: 表格处理器

**Files:**
- Create: `wordparser/core/tables.py`
- Create: `tests/test_tables.py`

- [ ] **Step 1: 在 conftest.py 追加fixture**

```python
@pytest.fixture
def docx_with_table(tmp_path):
    """含简单表格的文档"""
    doc = Document()
    doc.add_heading("表格测试", level=1)
    table = doc.add_table(rows=3, cols=3)
    for i, row in enumerate(table.rows):
        for j, cell in enumerate(row.cells):
            cell.text = f"R{i}C{j}"
    path = tmp_path / "table.docx"
    doc.save(str(path))
    return path
```

- [ ] **Step 2: 写测试**

`tests/test_tables.py`:
```python
from docx import Document
from wordparser.core.tables import TableProcessor
from wordparser.core.models import BlockType


def test_simple_table_to_markdown(docx_with_table):
    doc = Document(str(docx_with_table))
    table = doc.tables[0]
    processor = TableProcessor()
    result = processor.process_simple(table)

    lines = result.strip().split("\n")
    assert len(lines) == 4  # header + separator + 2 data rows
    assert "|" in lines[0]
    assert "---" in lines[1]


def test_table_cell_content(docx_with_table):
    doc = Document(str(docx_with_table))
    table = doc.tables[0]
    processor = TableProcessor()
    result = processor.process_simple(table)

    assert "R0C0" in result
    assert "R2C2" in result


def test_is_complex_table_returns_false_for_simple(docx_with_table):
    doc = Document(str(docx_with_table))
    table = doc.tables[0]
    processor = TableProcessor()
    assert processor.is_complex(table) is False


def test_empty_table():
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    processor = TableProcessor()
    result = processor.process_simple(table)
    assert "|" in result
```

- [ ] **Step 3: 运行测试确认失败**

```bash
pytest tests/test_tables.py -v
```

- [ ] **Step 4: 实现 tables.py**

`wordparser/core/tables.py`:
```python
from __future__ import annotations

from docx.table import Table


class TableProcessor:
    COMPLEX_ROW_THRESHOLD = 20
    COMPLEX_MERGE_THRESHOLD = 5

    def process_simple(self, table: Table) -> str:
        rows_data = []
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            rows_data.append(cells)

        if not rows_data:
            return ""

        col_count = max(len(r) for r in rows_data)
        for row in rows_data:
            while len(row) < col_count:
                row.append("")

        header = "| " + " | ".join(rows_data[0]) + " |"
        separator = "| " + " | ".join("---" for _ in range(col_count)) + " |"
        data_rows = []
        for row in rows_data[1:]:
            data_rows.append("| " + " | ".join(row) + " |")

        return "\n".join([header, separator] + data_rows)

    def is_complex(self, table: Table) -> bool:
        if len(table.rows) > self.COMPLEX_ROW_THRESHOLD:
            return True

        merge_count = 0
        for row in table.rows:
            for cell in row.cells:
                if cell._element.xpath(".//w:gridSpan"):
                    merge_count += 1
                if cell._element.xpath(".//w:vMerge"):
                    merge_count += 1

        return merge_count > self.COMPLEX_MERGE_THRESHOLD
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_tables.py -v
```

- [ ] **Step 6: Commit**

```bash
git add wordparser/core/tables.py tests/test_tables.py tests/conftest.py
git commit -m "feat: add TableProcessor - simple table to markdown, complexity detection"
```

---

### Task 9: 图片处理器

**Files:**
- Create: `wordparser/core/images.py`
- Create: `tests/test_images.py`

- [ ] **Step 1: 写测试**

`tests/test_images.py`:
```python
from wordparser.core.images import ImageExtractor
from docx import Document


def test_extract_images_from_simple_doc(simple_docx):
    doc = Document(str(simple_docx))
    extractor = ImageExtractor()
    images = extractor.extract(doc)
    assert isinstance(images, list)


def test_image_data_is_bytes(tmp_path):
    """创建含图片的文档并验证提取"""
    from docx import Document
    from docx.shared import Inches
    from PIL import Image
    import io

    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    doc = Document()
    doc.add_picture(buf, width=Inches(1))
    path = tmp_path / "with_image.docx"
    doc.save(str(path))

    loaded = Document(str(path))
    extractor = ImageExtractor()
    images = extractor.extract(loaded)

    assert len(images) > 0
    assert isinstance(images[0], bytes)
    assert len(images[0]) > 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_images.py -v
```

- [ ] **Step 3: 实现 images.py**

`wordparser/core/images.py`:
```python
from __future__ import annotations

from docx.document import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT


class ImageExtractor:
    def extract(self, doc: Document) -> list[bytes]:
        images: list[bytes] = []
        for rel in doc.part.rels.values():
            if "image" in rel.reltype:
                try:
                    images.append(rel.target_part.blob)
                except Exception:
                    continue
        return images
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_images.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/images.py tests/test_images.py
git commit -m "feat: add ImageExtractor - extract image bytes from docx"
```

---

## Phase 4: 多模态集成

### Task 10: OpenAI兼容客户端

**Files:**
- Create: `wordparser/multimodal/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: 写测试**

`tests/test_client.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from wordparser.multimodal.client import OpenAICompatibleVisionClient
from wordparser.config import VisionModelConfig


@pytest.fixture
def mock_config():
    return VisionModelConfig(
        base_url="http://localhost:1234/v1",
        model="test-model"
    )


@pytest.fixture
def mock_response():
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "choices": [{
            "message": {"content": "图片描述"}
        }]
    }
    resp.raise_for_status = MagicMock()
    return resp


def test_parse_from_bytes(mock_config, mock_response):
    client = OpenAICompatibleVisionClient(mock_config)

    with patch.object(client._client, "post", return_value=mock_response) as mock_post:
        result = client.parse_from_bytes(b"fake_image_data", "描述图片")

    assert result["choices"][0]["message"]["content"] == "图片描述"
    mock_post.assert_called_once()

    call_args = mock_post.call_args
    payload = call_args.kwargs["json"]
    assert payload["model"] == "test-model"
    assert len(payload["messages"]) == 1
    assert payload["messages"][0]["role"] == "user"


def test_parse_from_bytes_with_json_mode(mock_config, mock_response):
    client = OpenAICompatibleVisionClient(mock_config)

    with patch.object(client._client, "post", return_value=mock_response):
        result = client.parse_from_bytes(b"data", "prompt", json_mode=True)

    call_args = client._client.post.call_args
    payload = call_args.kwargs["json"]
    assert payload.get("response_format") == {"type": "json_object"}


def test_api_key_in_headers():
    config = VisionModelConfig(
        base_url="http://localhost:1234/v1",
        api_key="sk-test123"
    )
    client = OpenAICompatibleVisionClient(config)
    assert client.headers["Authorization"] == "Bearer sk-test123"


def test_no_api_key():
    config = VisionModelConfig(base_url="http://localhost:1234/v1")
    client = OpenAICompatibleVisionClient(config)
    assert "Authorization" not in client.headers
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_client.py -v
```

- [ ] **Step 3: 实现 client.py**

`wordparser/multimodal/client.py`:
```python
from __future__ import annotations

import base64

import httpx

from wordparser.config import VisionModelConfig


class OpenAICompatibleVisionClient:
    def __init__(self, config: VisionModelConfig):
        self.config = config
        self._client = httpx.Client(timeout=config.timeout)
        self.headers = {"Content-Type": "application/json"}
        if config.api_key:
            self.headers["Authorization"] = f"Bearer {config.api_key}"

    def parse_from_bytes(
        self,
        image_data: bytes,
        prompt: str,
        json_mode: bool = False,
    ) -> dict:
        b64 = base64.b64encode(image_data).decode("utf-8")
        return self._call(b64, prompt, json_mode)

    def parse_from_file(
        self,
        image_path,
        prompt: str,
        json_mode: bool = False,
    ) -> dict:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return self._call(b64, prompt, json_mode)

    def _call(self, base64_image: str, prompt: str, json_mode: bool) -> dict:
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            },
        ]

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": self.config.temperature,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = self._client.post(
            f"{self.config.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_client.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/multimodal/client.py tests/test_client.py
git commit -m "feat: add OpenAICompatibleVisionClient - base64 image API calls"
```

---

### Task 11: Prompt模板

**Files:**
- Create: `wordparser/multimodal/prompts.py`

- [ ] **Step 1: 实现 prompts.py**

`wordparser/multimodal/prompts.py`:
```python
from __future__ import annotations

TABLE_PROMPT = """\
分析这个表格，返回JSON格式：
{
  "rows": 行数,
  "cols": 列数,
  "cells": [{"row": 0, "col": 0, "text": "内容"}]
}
仅输出JSON，不要其他内容。"""

IMAGE_PROMPT = "描述这张图片的内容，并提取其中的所有文字信息。"

CHART_PROMPT = """\
分析这个图表，返回JSON格式：
{
  "chart_type": "图表类型",
  "title": "图表标题",
  "data_summary": "数据概要"
}
仅输出JSON，不要其他内容。"""

SMARTART_PROMPT = """\
分析这个SmartArt图形，返回JSON格式：
{
  "layout_type": "布局类型",
  "nodes": [{"id": 1, "text": "内容", "level": 0}],
  "summary": "结构描述"
}
仅输出JSON，不要其他内容。"""
```

- [ ] **Step 2: Commit**

```bash
git add wordparser/multimodal/prompts.py
git commit -m "feat: add multimodal prompt templates for table/image/chart/smartart"
```

---

### Task 12: 多模态解析器

**Files:**
- Create: `wordparser/multimodal/parser.py`
- Create: `tests/test_multimodal.py`

- [ ] **Step 1: 写测试**

`tests/test_multimodal.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from wordparser.multimodal.parser import MultimodalParser
from wordparser.multimodal.client import OpenAICompatibleVisionClient
from wordparser.config import VisionModelConfig


@pytest.fixture
def mock_client():
    config = VisionModelConfig(base_url="http://localhost:1234/v1")
    client = OpenAICompatibleVisionClient(config)

    mock_resp = {
        "choices": [{"message": {"content": '{"rows": 2, "cols": 3, "cells": []}'}}]
    }
    with patch.object(client, "parse_from_bytes", return_value=mock_resp):
        yield client


def test_parse_table(mock_client):
    parser = MultimodalParser(mock_client)
    result = parser.parse_table(b"fake_image")
    assert result.content_type == "complex_table"
    assert "cells" in result.data


def test_parse_image(mock_client):
    image_resp = {
        "choices": [{"message": {"content": "这是一张风景图"}}]
    }
    with patch.object(mock_client, "parse_from_bytes", return_value=image_resp):
        parser = MultimodalParser(mock_client)
        result = parser.parse_image(b"fake_image")
        assert result.content_type == "image"
        assert "风景图" in result.description
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_multimodal.py -v
```

- [ ] **Step 3: 实现 parser.py**

`wordparser/multimodal/parser.py`:
```python
from __future__ import annotations

import json
from dataclasses import dataclass, field

from wordparser.multimodal.client import OpenAICompatibleVisionClient
from wordparser.multimodal.prompts import (
    TABLE_PROMPT,
    IMAGE_PROMPT,
    CHART_PROMPT,
    SMARTART_PROMPT,
)


@dataclass
class MultimodalResult:
    content_type: str
    data: dict = field(default_factory=dict)
    description: str = ""


class MultimodalParser:
    def __init__(self, client: OpenAICompatibleVisionClient):
        self.client = client

    def parse_table(self, image_data: bytes) -> MultimodalResult:
        resp = self.client.parse_from_bytes(
            image_data, TABLE_PROMPT, json_mode=True
        )
        content = resp["choices"][0]["message"]["content"]
        data = json.loads(content)
        return MultimodalResult(content_type="complex_table", data=data)

    def parse_image(self, image_data: bytes) -> MultimodalResult:
        resp = self.client.parse_from_bytes(image_data, IMAGE_PROMPT)
        content = resp["choices"][0]["message"]["content"]
        return MultimodalResult(content_type="image", description=content)

    def parse_chart(self, image_data: bytes) -> MultimodalResult:
        resp = self.client.parse_from_bytes(
            image_data, CHART_PROMPT, json_mode=True
        )
        content = resp["choices"][0]["message"]["content"]
        data = json.loads(content)
        return MultimodalResult(content_type="chart", data=data)

    def parse_smartart(self, image_data: bytes) -> MultimodalResult:
        resp = self.client.parse_from_bytes(
            image_data, SMARTART_PROMPT, json_mode=True
        )
        content = resp["choices"][0]["message"]["content"]
        data = json.loads(content)
        return MultimodalResult(content_type="smartart", data=data)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_multimodal.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/multimodal/parser.py tests/test_multimodal.py
git commit -m "feat: add MultimodalParser - table/image/chart/smartart parsing"
```

---

### Task 13: 并行处理器

**Files:**
- Create: `wordparser/multimodal/parallel.py`

- [ ] **Step 1: 写测试（追加到 test_multimodal.py）**

在 `tests/test_multimodal.py` 追加:

```python
from wordparser.multimodal.parallel import ParallelMultimodalProcessor
from wordparser.multimodal.parser import MultimodalParser
from wordparser.config import MultimodalConfig, VisionModelConfig


def test_parallel_process_batch():
    config = VisionModelConfig(base_url="http://localhost:1234/v1")
    client = OpenAICompatibleVisionClient(config)

    mock_resp = {
        "choices": [{"message": {"content": "描述结果"}}]
    }
    with patch.object(client, "parse_from_bytes", return_value=mock_resp):
        parser = MultimodalParser(client)
        parallel = ParallelMultimodalProcessor(
            parser, MultimodalConfig(max_concurrent=2, model=config)
        )

        tasks = [
            ("image", b"img1"),
            ("image", b"img2"),
            ("image", b"img3"),
        ]
        results = parallel.process_batch(tasks)
        assert len(results) == 3
        for r in results:
            assert r.content_type == "image"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_multimodal.py::test_parallel_process_batch -v
```

- [ ] **Step 3: 实现 parallel.py**

`wordparser/multimodal/parallel.py`:
```python
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from wordparser.config import MultimodalConfig
from wordparser.multimodal.parser import MultimodalParser, MultimodalResult


@dataclass
class MultimodalTask:
    task_type: str       # "table", "image", "chart", "smartart"
    image_data: bytes


class ParallelMultimodalProcessor:
    def __init__(
        self,
        parser: MultimodalParser,
        config: MultimodalConfig,
    ):
        self.parser = parser
        self.config = config

    def process_batch(
        self,
        tasks: list[tuple[str, bytes]],
    ) -> list[MultimodalResult]:
        results: list[MultimodalResult | None] = [None] * len(tasks)

        with ThreadPoolExecutor(max_workers=self.config.max_concurrent) as executor:
            futures = {
                executor.submit(self._process_single, task_type, data): idx
                for idx, (task_type, data) in enumerate(tasks)
            }

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = MultimodalResult(
                        content_type="error",
                        description=str(e),
                    )

        return [r or MultimodalResult(content_type="error") for r in results]

    def _process_single(
        self, task_type: str, image_data: bytes
    ) -> MultimodalResult:
        handlers = {
            "table": self.parser.parse_table,
            "image": self.parser.parse_image,
            "chart": self.parser.parse_chart,
            "smartart": self.parser.parse_smartart,
        }
        handler = handlers.get(task_type, self.parser.parse_image)
        return handler(image_data)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_multimodal.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/multimodal/parallel.py tests/test_multimodal.py
git commit -m "feat: add ParallelMultimodalProcessor - concurrent image analysis"
```

---

## Phase 5: 目录与公式

### Task 14: 目录生成器

**Files:**
- Create: `wordparser/core/toc.py`
- Create: `tests/test_toc.py`

- [ ] **Step 1: 写测试**

`tests/test_toc.py`:
```python
from wordparser.core.toc import TOCGenerator
from wordparser.core.models import TitleNode


def test_generate_toc():
    tree = [
        TitleNode(
            level=1, text="项目背景", anchor="项目背景",
            children=[
                TitleNode(level=2, text="技术方案", anchor="技术方案"),
                TitleNode(level=2, text="实施计划", anchor="实施计划"),
            ]
        ),
        TitleNode(level=1, text="总结", anchor="总结"),
    ]
    gen = TOCGenerator()
    result = gen.generate(tree)

    assert "[项目背景](#项目背景)" in result
    assert "[技术方案](#技术方案)" in result
    assert "[总结](#总结)" in result


def test_toc_indent_levels():
    tree = [
        TitleNode(
            level=1, text="一级", anchor="一级",
            children=[
                TitleNode(
                    level=2, text="二级", anchor="二级",
                    children=[
                        TitleNode(level=3, text="三级", anchor="三级"),
                    ]
                ),
            ]
        ),
    ]
    gen = TOCGenerator()
    result = gen.generate(tree)
    lines = [l for l in result.split("\n") if l.strip()]

    assert lines[0].startswith("- ")
    assert "  " in lines[1]
    assert "    " in lines[2]
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_toc.py -v
```

- [ ] **Step 3: 实现 toc.py**

`wordparser/core/toc.py`:
```python
from __future__ import annotations

from wordparser.core.models import TitleNode


class TOCGenerator:
    def generate(self, title_tree: list[TitleNode]) -> str:
        lines = ["## 目录\n"]
        self._render_nodes(title_tree, lines, indent=0)
        return "\n".join(lines)

    def _render_nodes(
        self, nodes: list[TitleNode], lines: list[str], indent: int
    ) -> None:
        for node in nodes:
            prefix = "  " * indent + "- "
            lines.append(f"{prefix}[{node.text}](#{node.anchor})")
            if node.children:
                self._render_nodes(node.children, lines, indent + 1)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_toc.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/toc.py tests/test_toc.py
git commit -m "feat: add TOCGenerator - markdown TOC with anchor links"
```

---

### Task 15: 公式处理器（OMML → LaTeX）

**Files:**
- Create: `wordparser/core/formulas.py`
- Create: `tests/test_formulas.py`

- [ ] **Step 1: 写测试**

`tests/test_formulas.py`:
```python
import lxml.etree as ET
from wordparser.core.formulas import FormulaProcessor


NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _make_omml(tag: str, children: list = None, text: str = "") -> ET.Element:
    el = ET.Element(f"{{{NS}}}{tag}")
    if text:
        t = ET.SubElement(el, f"{{{W_NS}}}t")
        t.text = text
    for child in (children or []):
        el.append(child)
    return el


def test_fraction():
    proc = FormulaProcessor()
    num = _make_omml("num", text="a")
    den = _make_omml("den", text="b")
    frac = _make_omml("f", [num, den])

    result = proc.omml_to_latex(frac)
    assert result == r"\frac{a}{b}"


def test_radical_sqrt():
    proc = FormulaProcessor()
    e = _make_omml("e", text="x")
    rad = _make_omml("rad", [e])

    result = proc.omml_to_latex(rad)
    assert result == r"\sqrt{x}"


def test_superscript():
    proc = FormulaProcessor()
    sup = _make_omml("sup", text="2")
    base = _make_omml("e", text="x")
    s = ET.Element(f"{{{NS}}}sSup")
    s.append(base)
    s.append(sup)

    result = proc.omml_to_latex(s)
    assert result == "x^{2}"


def test_subscript():
    proc = FormulaProcessor()
    sub = _make_omml("sub", text="i")
    base = _make_omml("e", text="x")
    s = ET.Element(f"{{{NS}}}sSub")
    s.append(base)
    s.append(sub)

    result = proc.omml_to_latex(s)
    assert result == "x_{i}"


def test_delimiter():
    proc = FormulaProcessor()
    e = _make_omml("e", text="a+b")
    d = _make_omml("d", [e])

    result = proc.omml_to_latex(d)
    assert result == r"\left(a+b\right)"


def test_inline_formula_wrapping():
    proc = FormulaProcessor()
    frac = _make_omml("f", [
        _make_omml("num", text="1"),
        _make_omml("den", text="2"),
    ])
    result = proc.wrap_formula(frac, inline=True)
    assert result.startswith("$")
    assert result.endswith("$")


def test_block_formula_wrapping():
    proc = FormulaProcessor()
    frac = _make_omml("f", [
        _make_omml("num", text="1"),
        _make_omml("den", text="2"),
    ])
    result = proc.wrap_formula(frac, inline=False)
    assert result.startswith("$$")
    assert result.endswith("$$")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_formulas.py -v
```

- [ ] **Step 3: 实现 formulas.py**

`wordparser/core/formulas.py`:
```python
from __future__ import annotations

import lxml.etree as ET

OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class FormulaProcessor:
    def omml_to_latex(self, element: ET.Element) -> str:
        return self._convert_node(element)

    def wrap_formula(self, element: ET.Element, inline: bool = True) -> str:
        latex = self.omml_to_latex(element)
        if inline:
            return f"${latex}$"
        return f"$${latex}$$"

    def _convert_node(self, node: ET.Element) -> str:
        tag = self._local_tag(node)

        converters = {
            "f": self._convert_fraction,
            "rad": self._convert_radical,
            "sSup": self._convert_ssup,
            "sSub": self._convert_ssub,
            "d": self._convert_delimiter,
            "r": self._convert_run,
            "e": self._convert_e,
        }
        converter = converters.get(tag, self._convert_default)
        return converter(node)

    def _convert_children(self, parent: ET.Element | None) -> str:
        if parent is None:
            return ""
        parts = []
        for child in parent:
            parts.append(self._convert_node(child))
        return "".join(parts)

    def _convert_fraction(self, node: ET.Element) -> str:
        num = node.find(f"{{{OMML_NS}}}num")
        den = node.find(f"{{{OMML_NS}}}den")
        n = self._convert_children(num) if num is not None else ""
        d = self._convert_children(den) if den is not None else ""
        return f"\\frac{{{n}}}{{{d}}}"

    def _convert_radical(self, node: ET.Element) -> str:
        e = node.find(f"{{{OMML_NS}}}e")
        content = self._convert_children(e) if e is not None else ""
        deg = node.find(f"{{{OMML_NS}}}deg")
        if deg is not None:
            index = self._convert_children(deg)
            if index.strip():
                return f"\\sqrt[{index}]{{{content}}}"
        return f"\\sqrt{{{content}}}"

    def _convert_ssup(self, node: ET.Element) -> str:
        e = node.find(f"{{{OMML_NS}}}e")
        sup = node.find(f"{{{OMML_NS}}}sup")
        base = self._convert_children(e) if e is not None else ""
        upper = self._convert_children(sup) if sup is not None else ""
        return f"{base}^{{{upper}}}"

    def _convert_ssub(self, node: ET.Element) -> str:
        e = node.find(f"{{{OMML_NS}}}e")
        sub = node.find(f"{{{OMML_NS}}}sub")
        base = self._convert_children(e) if e is not None else ""
        lower = self._convert_children(sub) if sub is not None else ""
        return f"{base}_{{{lower}}}"

    def _convert_delimiter(self, node: ET.Element) -> str:
        e = node.find(f"{{{OMML_NS}}}e")
        content = self._convert_children(e) if e is not None else ""
        return f"\\left({content}\\right)"

    def _convert_run(self, node: ET.Element) -> str:
        t = node.find(f"{{{W_NS}}}t")
        return t.text if t is not None and t.text else ""

    def _convert_e(self, node: ET.Element) -> str:
        return self._convert_children(node)

    def _convert_default(self, node: ET.Element) -> str:
        return self._convert_children(node)

    def _local_tag(self, node: ET.Element) -> str:
        tag = node.tag
        if "}" in tag:
            return tag.split("}")[1]
        return tag
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_formulas.py -v
```

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/formulas.py tests/test_formulas.py
git commit -m "feat: add FormulaProcessor - OMML to LaTeX conversion"
```

---

## Phase 6: 主解析器组装

### Task 16: WordParser 主解析器

**Files:**
- Create: `wordparser/core/parser.py`
- Create: `tests/test_parser.py`
- Update: `wordparser/__init__.py`

- [ ] **Step 1: 写测试**

`tests/test_parser.py`:
```python
from docx import Document
from wordparser.core.parser import WordParser
from wordparser.config import ParserConfig


def test_parse_simple_document(simple_docx):
    config = ParserConfig(generate_toc=False)
    parser = WordParser(config)
    result = parser.parse(str(simple_docx))

    assert "测试标题" in result
    assert "第一个段落" in result
    assert "第二个段落" in result
    assert result.startswith("# ")


def test_parse_with_toc(docx_with_headings):
    config = ParserConfig(generate_toc=True)
    parser = WordParser(config)
    result = parser.parse(str(docx_with_headings))

    assert "目录" in result
    assert "一级标题" in result


def test_parse_with_table(docx_with_table):
    config = ParserConfig(generate_toc=False)
    parser = WordParser(config)
    result = parser.parse(str(docx_with_table))

    assert "|" in result
    assert "R0C0" in result


def test_parse_returns_report(simple_docx):
    config = ParserConfig(generate_toc=False)
    parser = WordParser(config)
    md, report = parser.parse_with_report(str(simple_docx))

    assert isinstance(md, str)
    assert report.success is True
    assert report.stats.total_headings >= 1
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_parser.py -v
```

- [ ] **Step 3: 实现 parser.py**

`wordparser/core/parser.py`:
```python
from __future__ import annotations

import time
from pathlib import Path

from docx import Document as DocxDocument

from wordparser.config import ParserConfig
from wordparser.core.models import BlockType, ContentBlock
from wordparser.core.preprocessor import Preprocessor
from wordparser.core.structure import StructureParser
from wordparser.core.tables import TableProcessor
from wordparser.core.toc import TOCGenerator
from wordparser.core.postprocess import PostProcessor
from wordparser.core.report import ParseReport, ParseError, ParseStats
from wordparser.exceptions import DocumentCorruptedError


class WordParser:
    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()
        self.preprocessor = Preprocessor()
        self.structure_parser = StructureParser(self.config)
        self.table_processor = TableProcessor()
        self.toc_generator = TOCGenerator()
        self.postprocessor = PostProcessor()
        self._errors: list[ParseError] = []
        self._stats = ParseStats()

    def parse(self, docx_path: str) -> str:
        md, _ = self.parse_with_report(docx_path)
        return md

    def parse_with_report(self, docx_path: str) -> tuple[str, ParseReport]:
        start_time = time.time()
        self._errors = []
        self._stats = ParseStats()

        try:
            doc = self._load_document(docx_path)
        except Exception as e:
            report = ParseReport(
                success=False, output_path=None,
                errors=[ParseError("document", str(e), fatal=True)],
                stats=ParseStats()
            )
            return "", report

        doc = self.preprocessor.clean(doc)
        blocks = self.structure_parser.parse(doc)

        table_blocks = self._process_tables(doc, blocks)
        title_tree = self.structure_parser.get_title_tree()
        self._stats.total_headings = self._count_type(blocks, BlockType.HEADING)
        self._stats.total_paragraphs = self._count_type(blocks, BlockType.PARAGRAPH)
        self._stats.total_tables = len(doc.tables)

        md = self._render_blocks(table_blocks)

        if self.config.generate_toc and title_tree:
            toc_md = self.toc_generator.generate(title_tree)
            md = toc_md + "\n\n" + md

        md = self.postprocessor.process(md)

        self._stats.processing_time = time.time() - start_time
        report = ParseReport(
            success=not any(e.fatal for e in self._errors),
            output_path=None,
            errors=self._errors,
            stats=self._stats,
        )
        return md, report

    def _load_document(self, path: str) -> DocxDocument:
        p = Path(path)
        if not p.exists():
            raise DocumentCorruptedError(f"文件不存在: {path}")
        if not p.suffix.lower() == ".docx":
            raise DocumentCorruptedError(f"不支持的格式: {p.suffix}")
        return DocxDocument(str(p))

    def _process_tables(
        self, doc: DocxDocument, blocks: list[ContentBlock]
    ) -> list[ContentBlock]:
        result = []
        table_idx = 0
        for block in blocks:
            if block.type == BlockType.HEADING:
                level = block.content.level
                if level <= self.config.max_heading_level:
                    md_heading = "#" * level + " " + block.content.text
                    result.append(ContentBlock(
                        type=BlockType.HEADING, content=md_heading
                    ))
                else:
                    result.append(ContentBlock(
                        type=BlockType.PARAGRAPH,
                        content=f"**{block.content.text}**"
                    ))
            else:
                result.append(block)

        for i, table in enumerate(doc.tables):
            try:
                md_table = self.table_processor.process_simple(table)
                result.append(ContentBlock(
                    type=BlockType.TABLE, content=md_table
                ))
            except Exception as e:
                self._errors.append(
                    ParseError("table", f"表格{i}处理失败: {e}")
                )

        return result

    def _render_blocks(self, blocks: list[ContentBlock]) -> str:
        parts = []
        for block in blocks:
            if block.type == BlockType.HEADING:
                parts.append(block.content)
            elif block.type == BlockType.PARAGRAPH:
                parts.append(block.content)
            elif block.type == BlockType.TABLE:
                parts.append(block.content)
            elif block.type == BlockType.LIST:
                parts.append(block.content)
            elif block.type == BlockType.FORMULA:
                parts.append(block.content)
            else:
                parts.append(str(block.content))
        return "\n\n".join(parts)

    def _count_type(self, blocks: list[ContentBlock], btype: BlockType) -> int:
        return sum(1 for b in blocks if b.type == btype)
```

- [ ] **Step 4: 更新 __init__.py**

`wordparser/__init__.py`:
```python
"""Word文档转Markdown解析库"""

from wordparser.config import ParserConfig, VisionModelConfig, MultimodalConfig
from wordparser.core.parser import WordParser


def parse_word_to_markdown(
    docx_path: str,
    output_path: str | None = None,
    *,
    config: ParserConfig | None = None,
) -> tuple[str, "ParseReport"]:
    from wordparser.core.report import ParseReport

    parser = WordParser(config)
    md, report = parser.parse_with_report(docx_path)

    if output_path:
        from pathlib import Path
        Path(output_path).write_text(md, encoding=config.encoding if config else "utf-8")
        report.output_path = Path(output_path)

    return md, report
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/test_parser.py -v
```

- [ ] **Step 6: Commit**

```bash
git add wordparser/core/parser.py wordparser/__init__.py tests/test_parser.py
git commit -m "feat: add WordParser main parser with pipeline assembly and report"
```

---

## Phase 7: CLI与BAT

### Task 17: CLI工具

**Files:**
- Create: `wordparser_cli/__init__.py`
- Create: `wordparser_cli/main.py`
- Create: `wordparser_cli/commands/__init__.py`
- Create: `wordparser_cli/commands/parse_cmd.py`

- [ ] **Step 1: 实现 CLI**

`wordparser_cli/__init__.py`:
```python
```

`wordparser_cli/main.py`:
```python
from __future__ import annotations

import typer

app = typer.Typer(name="wordparser", help="Word文档转Markdown解析器")


@app.command()
def parse(
    input: str = typer.Argument(..., help="输入.docx文件路径"),
    output: str | None = typer.Option(None, "-o", "--output", help="输出.md路径"),
    vision_url: str | None = typer.Option(None, "--vision-url", help="视觉模型API地址"),
    vision_model: str | None = typer.Option(None, "--vision-model", help="模型名称"),
    max_concurrent: int = typer.Option(4, "--max-concurrent", help="最大并行数"),
    toc: bool = typer.Option(True, "--toc/--no-toc", help="是否生成目录"),
    max_heading: int = typer.Option(6, "--max-heading", help="最大标题层级"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="详细输出"),
):
    from pathlib import Path
    from wordparser import parse_word_to_markdown
    from wordparser.config import (
        ParserConfig, MultimodalConfig, VisionModelConfig,
    )

    multimodal = None
    if vision_url:
        multimodal = MultimodalConfig(
            max_concurrent=max_concurrent,
            model=VisionModelConfig(
                base_url=vision_url,
                model=vision_model or "qwen2-vl-7b",
            ),
        )

    config = ParserConfig(
        max_heading_level=max_heading,
        generate_toc=toc,
        multimodal=multimodal,
    )

    md, report = parse_word_to_markdown(input, output, config=config)

    if output is None:
        typer.echo(md)
    else:
        typer.echo(f"输出已保存到: {output}")

    if verbose or report.has_errors():
        typer.echo(f"\n解析统计:")
        typer.echo(f"  标题: {report.stats.total_headings}")
        typer.echo(f"  段落: {report.stats.total_paragraphs}")
        typer.echo(f"  表格: {report.stats.total_tables}")
        typer.echo(f"  耗时: {report.stats.processing_time:.2f}秒")

        if report.has_errors():
            typer.echo(f"\n错误 ({len(report.errors)}):")
            for err in report.errors:
                typer.echo(f"  [{err.type}] {err.message}")

    if report.has_fatal_errors():
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: 验证CLI运行**

```bash
python -m wordparser_cli --help
```

预期输出: 显示帮助信息

- [ ] **Step 3: Commit**

```bash
git add wordparser_cli/
git commit -m "feat: add CLI tool with typer - parse command"
```

---

### Task 18: BAT启动脚本

**Files:**
- Create: `wordparser.bat`

- [ ] **Step 1: 创建 wordparser.bat**

```batch
@echo off
REM WordParser - Word文档转Markdown解析器
REM 使用方式: wordparser.bat parse doc.docx -o out.md

python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

python -m wordparser_cli %*

if errorlevel 1 (
    echo.
    echo 解析过程中出现错误
    pause
)
```

- [ ] **Step 2: 验证BAT运行**

```bash
cmd.exe /c "wordparser.bat --help"
```

预期输出: 显示帮助信息

- [ ] **Step 3: Commit**

```bash
git add wordparser.bat
git commit -m "feat: add wordparser.bat - Windows user entry point"
```

---

## Phase 8: 示例与最终集成测试

### Task 19: 使用示例

**Files:**
- Create: `examples/basic_usage.py`
- Create: `examples/advanced_config.py`

- [ ] **Step 1: 创建 basic_usage.py**

```python
"""基础使用示例"""
from wordparser import parse_word_to_markdown

md, report = parse_word_to_markdown("input.docx", "output.md")

print(f"解析成功: {report.success}")
print(f"标题数: {report.stats.total_headings}")
print(f"耗时: {report.stats.processing_time:.2f}秒")
```

- [ ] **Step 2: 创建 advanced_config.py**

```python
"""高级配置示例"""
from wordparser import parse_word_to_markdown
from wordparser.config import (
    ParserConfig,
    VisionModelConfig,
    MultimodalConfig,
)

config = ParserConfig(
    max_heading_level=6,
    generate_toc=True,
    multimodal=MultimodalConfig(
        max_concurrent=4,
        model=VisionModelConfig(
            base_url="http://localhost:1234/v1",
            model="qwen2-vl-7b",
        ),
    ),
)

md, report = parse_word_to_markdown(
    "input.docx",
    "output.md",
    config=config,
)
```

- [ ] **Step 3: Commit**

```bash
git add examples/
git commit -m "docs: add usage examples"
```

---

### Task 20: 集成测试

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: 写集成测试**

`tests/test_integration.py`:
```python
"""端到端集成测试"""
from docx import Document
from docx.shared import Inches
from pathlib import Path
from wordparser import parse_word_to_markdown
from wordparser.config import ParserConfig


def _create_rich_docx(path: Path):
    """创建包含多种内容的复杂文档"""
    doc = Document()

    doc.add_heading("项目报告", level=1)
    doc.add_paragraph("这是一份项目报告的摘要。")

    doc.add_heading("1. 背景介绍", level=2)
    doc.add_paragraph("项目背景说明文字。")

    doc.add_heading("1.1 技术选型", level=3)
    doc.add_paragraph("我们选择了Python作为主要开发语言。")

    doc.add_heading("2. 数据分析", level=2)

    table = doc.add_table(rows=3, cols=3)
    headers = ["指标", "Q1", "Q2"]
    for j, h in enumerate(headers):
        table.rows[0].cells[j].text = h
    for i in range(1, 3):
        table.rows[i].cells[0].text = f"指标{i}"
        table.rows[i].cells[1].text = str(i * 10)
        table.rows[i].cells[2].text = str(i * 20)

    doc.add_paragraph("")
    doc.add_paragraph("总结段落。")

    doc.add_heading("结论", level=1)
    doc.add_paragraph("这是最终结论。")

    doc.save(str(path))


def test_full_pipeline_with_toc(tmp_path):
    docx_path = tmp_path / "rich.docx"
    md_path = tmp_path / "rich.md"
    _create_rich_docx(docx_path)

    config = ParserConfig(generate_toc=True)
    md, report = parse_word_to_markdown(
        str(docx_path), str(md_path), config=config
    )

    assert report.success
    assert md_path.exists()

    content = md_path.read_text(encoding="utf-8")
    assert "# 项目报告" in content
    assert "目录" in content
    assert "背景介绍" in content
    assert "技术选型" in content
    assert "|" in content
    assert "指标" in content
    assert "结论" in content


def test_full_pipeline_without_toc(tmp_path):
    docx_path = tmp_path / "simple.docx"
    md_path = tmp_path / "simple.md"

    doc = Document()
    doc.add_heading("标题", level=1)
    doc.add_paragraph("正文")
    doc.save(str(docx_path))

    config = ParserConfig(generate_toc=False)
    md, report = parse_word_to_markdown(
        str(docx_path), str(md_path), config=config
    )

    assert report.success
    assert "目录" not in md
    assert "# 标题" in md
    assert "正文" in md


def test_nonexistent_file():
    md, report = parse_word_to_markdown("nonexistent.docx")
    assert report.success is False
    assert len(report.errors) > 0
    assert report.errors[0].fatal is True
```

- [ ] **Step 2: 运行集成测试**

```bash
pytest tests/test_integration.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration tests"
```

---

## 自检清单

### Spec覆盖检查

| 设计规格要求 | 对应Task |
|-------------|----------|
| 文档预处理 | Task 5 |
| 标题结构化 1-6级 + 序号剔除 | Task 6 |
| 正文格式化（段落/列表） | Task 6 |
| 表格处理（简单） | Task 8 |
| 表格处理（复杂/多模态） | Task 12 |
| 图片提取 | Task 9 |
| 图片多模态解析 | Task 12 |
| 公式 OMML→LaTeX | Task 15 |
| 目录生成 | Task 14 |
| 后处理 | Task 7 |
| OpenAI兼容客户端 | Task 10 |
| 并行处理 | Task 13 |
| 编程接口 | Task 16 |
| CLI工具 | Task 17 |
| BAT脚本 | Task 18 |
| 异常体系 | Task 3 |
| 解析报告 | Task 4 |
| LibreOffice渲染 | 设计文档4.3节（P2延后实现） |

### 占位符扫描

无TBD/TODO/待补充。

### 类型一致性

所有Task中的类名、方法名、属性名保持一致：
- `VisionModelConfig.base_url` - 全文统一
- `MultimodalConfig.model` - 全文统一
- `ParserConfig.multimodal` - 全文统一
- `ParseReport.success/errors/stats` - 全文统一
- `TitleNode.level/text/anchor/children` - 全文统一
- `ContentBlock.type/content/metadata` - 全文统一

---

*实施计划 v1.0 - 共20个Task*
