# Word文档转Markdown解析器 - 设计规格

**日期**: 2026-04-22
**版本**: 1.1
**状态**: 设计中

---

## 1. 概述

### 1.1 目标

开发一个Python实现的Word文档(.docx)解析服务，输出结构化、规范化的Markdown格式。支持8大核心功能模块，提供编程接口和CLI工具。

### 1.2 核心能力

| 模块 | 功能描述 |
|------|----------|
| 文档预处理 | 清理空白字符、统一编码、过滤控制符 |
| 标题结构化 | 1-6级标题映射、自动去除序号 |
| 正文格式化 | 段落、粗体、斜体、列表、链接转换 |
| 表格处理 | 简单表格MD化、复杂表格多模态识别 |
| 图片处理 | 提取所有类型图片、多模态解析、插回MD |
| 富内容解析 | 公式OMML→LaTeX、文本框、脚注、批注 |
| 目录重建 | 自动生成带锚点的MD目录 |
| 后处理 | 格式规范化、换行统一 |

---

## 2. 架构设计

### 2.1 整体架构

```
输入 .docx
    ↓
[预处理模块] → 清理文档
    ↓
[结构解析模块] → 提取标题/段落/列表
    ↓
[富内容处理模块] → 表格/图片/公式（并行）
    ├─ 表格处理器 → 简单MD化 / 复杂→视觉模型
    ├─ 图片处理器 → 提取→多模态识别
    └─ 公式处理器 → OMML→LaTeX
    ↓
[目录生成模块] → 重建MD目录
    ↓
[后处理模块] → 格式规范化
    ↓
输出 .md
```

### 2.2 模块职责

| 模块 | 输入 | 输出 | 职责 |
|------|------|------|------|
| 预处理 | raw .docx | 清理后文档 | 去噪、编码统一、过滤控制符 |
| 结构解析 | 文档对象 | 标题树+段落列表 | 标题层级映射、序号剔除 |
| 表格处理 | 表格元素 | MD表格/视觉识别结果 | 简单直转、复杂视觉化 |
| 图片处理 | 图片bytes | 文字描述 | 提取→base64→多模态识别→文字 |
| 公式处理 | OMML公式 | LaTeX公式 | OMML→LaTeX转换 |
| 目录生成 | 标题树 | MD目录+锚点 | 自动重建、可配置 |
| 后处理 | 原始MD | 规范化MD | 格式清洗、换行统一 |

---

## 3. 数据模型

### 3.1 核心数据结构

> 所以下模型定义在 `wordparser/core/models.py` 中集中管理。

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
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
    """标题节点"""
    level: int              # 1-6
    text: str               # 已去除序号
    anchor: str             # 锚点ID
    children: list[TitleNode] = field(default_factory=list)

@dataclass
class ContentBlock:
    """内容块（多态）"""
    type: BlockType
    content: Any
    metadata: dict = field(default_factory=dict)

@dataclass
class ParsedDocument:
    """解析后的文档结构"""
    metadata: dict = field(default_factory=dict)
    title_tree: list[TitleNode] = field(default_factory=list)
    content_blocks: list[ContentBlock] = field(default_factory=list)
```

### 3.2 标题层级映射

```python
Word Heading 1 → #      (一级标题)
Word Heading 2 → ##     (二级标题)
Word Heading 3 → ###    (三级标题)
Word Heading 4 → ####   (四级标题)
Word Heading 5 → #####  (五级标题)
Word Heading 6 → ###### (六级标题)
Word Heading 7+ → **加粗文本** (降级)
```

---

## 4. 多模态解析集成

### 4.1 配置驱动设计

```python
@dataclass
class VisionModelConfig:
    """视觉模型配置（OpenAI兼容）"""
    base_url: str = "http://localhost:1234/v1"  # LM Studio
    api_key: str | None = None
    model: str = "qwen2-vl-7b"
    timeout: int = 60
    temperature: float = 0.0

@dataclass
class MultimodalConfig:
    """多模态解析配置"""
    max_concurrent: int = 4
    batch_delay: float = 0.1
    retry_on_failure: bool = True
    model: VisionModelConfig = field(default_factory=VisionModelConfig)
```

### 4.2 图片处理策略：零持久化

所有图片仅在内存中处理，不保存到磁盘。最终MD输出中不含图片引用，所有视觉内容转为文字描述。

```
Word图片元素 → python-docx提取bytes → 内存base64编码 → 传视觉模型 → 文字描述
                                                                         ↓
                                                                   直接插入MD
```

| 内容类型 | 提取方式 | 输出到MD |
|----------|----------|----------|
| 嵌入式图片 | python-docx直接提取bytes | 文字描述 |
| 形状内图片 | python-docx提取shape中的image bytes | 文字描述 |
| 文本框内图片 | 遍历textbox元素提取image bytes | 文字描述 |
| Chart图表 | LibreOffice渲染为临时图片 → base64 | 数据表格/文字描述 |
| SmartArt图形 | LibreOffice渲染为临时图片 → base64 | 结构描述 |
| 复杂表格 | LibreOffice渲染为临时图片 → base64 | MD表格 |

> 注：Chart/SmartArt/复杂表格需要LibreOffice渲染时产生临时文件，识别完成后立即删除。

### 4.3 Word元素渲染为图片

| 类型 | 处理方式 |
|------|----------|
| 复杂嵌套表格 | 视觉模型识别结构 |
| 嵌入式图片 | 描述+文字提取 |
| 形状内图片 | 描述+文字提取 |
| 文本框内图片 | 描述+文字提取 |
| Chart图表 | 结构识别+数据提取 |
| SmartArt图形 | 结构识别+关系提取 |

### 4.3 Word元素渲染为图片

Word中的复杂表格、Chart、SmartArt等元素需要渲染为图片才能送入视觉模型。python-docx本身不支持渲染，方案如下：

**方案：使用 LibreOffice 命令行转换**

```python
import subprocess
import tempfile
from pathlib import Path

class DocumentRenderer:
    """将Word元素渲染为图片（仅返回bytes，不持久化）"""

    def __init__(self, libreoffice_path: str | None = None):
        self.lo_path = libreoffice_path or self._detect_libreoffice()

    def render_element(
        self,
        docx_path: Path,
        element_type: str,      # table/chart/smartart
        element_index: int      # 文档中第几个该类型元素
    ) -> bytes:
        """
        渲染指定元素，返回PNG bytes（不落盘）

        流程：
        1. 将原始docx拆分为仅含目标元素的单页docx
        2. 调用LibreOffice转换为PDF（临时目录）
        3. 使用pdf2image将PDF页转为PNG bytes
        4. 裁剪到元素区域
        5. 清理所有临时文件，返回bytes
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # ... 拆分 + 渲染逻辑 ...
            png_path = Path(tmpdir) / "output.png"
            return png_path.read_bytes()

    def render_page(
        self,
        docx_path: Path,
        page_number: int = 0
    ) -> bytes:
        """渲染整页，返回PNG bytes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ... 渲染逻辑 ...
            png_path = Path(tmpdir) / f"page_{page_number}.png"
            return png_path.read_bytes()

    def _detect_libreoffice(self) -> str:
        """自动检测LibreOffice路径"""
        candidates = [
            "soffice",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        import shutil
        for path in candidates:
            if Path(path).exists() or shutil.which(path):
                return path
        raise RuntimeError("未找到LibreOffice，请安装或配置路径")
```

**配置项扩展：**

```python
@dataclass
class ParserConfig:
    # ... 其他配置 ...

    # 渲染配置
    libreoffice_path: str | None = None   # LibreOffice路径（自动检测）
```

**依赖项新增：**

```toml
dependencies = [
    "python-docx>=1.0",
    "httpx>=0.24",
    "pydantic>=2.0",
    "pdf2image>=1.16",       # PDF转图片
    # 系统依赖: LibreOffice + Poppler (pdf2image后端)
]
```

### 4.4 并行处理

```python
class ParallelMultimodalProcessor:
    """并行多模态处理器"""
    def process_batch(self, tasks: list[MultimodalTask]) -> list[MultimodalParseResult]:
        # 使用ThreadPoolExecutor并行处理
        # 保持结果顺序与输入一致
        pass
```

---

## 5. 公式处理方案

### 5.1 OMML → LaTeX 转换

Word中的数学公式使用Office Math Markup Language (OMML)格式存储。转换方案：

```python
import lxml.etree as ET

class FormulaProcessor:
    """公式处理器：OMML → LaTeX"""

    # OMML命名空间
    OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

    def omml_to_latex(self, omml_element: ET.Element) -> str:
        """
        将OMML元素转换为LaTeX字符串

        实现方式：手写递归解析器，遍历OMML XML树
        OMML标签映射规则：
          - m:f  (fraction)  → \frac{num}{den}
          - m:rad (radical)  → \sqrt{content} 或 \sqrt[n]{content}
          - m:sup (superscript) → ^{content}
          - m:sub (subscript)   → _{content}
          - m:nary (n-ary operator) → \sum/\prod/\int 等
          - m:d  (delimiter)  → \left( \right)
          - m:acc (accent)    → \hat, \vec 等
        """
        pass

    def _convert_node(self, node: ET.Element) -> str:
        """递归转换单个OMML节点"""
        tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag

        converters = {
            "f": self._convert_fraction,
            "rad": self._convert_radical,
            "sup": self._convert_superscript,
            "sub": self._convert_subscript,
            "nary": self._convert_nary,
            "d": self._convert_delimiter,
            "acc": self._convert_accent,
            "r": self._convert_run,        # 普通文本run
            "e": self._convert_element,     # 基础元素
        }

        converter = converters.get(tag, self._convert_default)
        return converter(node)

    def _convert_fraction(self, node: ET.Element) -> str:
        num = self._convert_children(node.find(f"{{{self.OMML_NS}}}num"))
        den = self._convert_children(node.find(f"{{{self.OMML_NS}}}den"))
        return f"\\frac{{{num}}}{{{den}}}"

    # ... 其他转换方法类似
```

**输出规则：**
- 行内公式 → `$formula$`
- 独立公式块 → `$$formula$$`（前后各空一行）

---

## 6. 编程接口

### 6.1 主入口

```python
def parse_word_to_markdown(
    docx_path: str | Path,
    output_path: str | Path | None = None,
    *,
    config: ParserConfig | None = None,
) -> tuple[str, ParseReport]:
    """
    将Word文档解析为Markdown

    Returns:
        (Markdown内容, 解析报告)
    """
```

### 6.2 配置对象

```python
@dataclass
class ParserConfig:
    # 基础选项
    max_heading_level: int = 6
    encoding: str = "utf-8"

    # 多模态配置
    multimodal: MultimodalConfig | None = None

    # 渲染配置（Chart/SmartArt/复杂表格需要LibreOffice）
    libreoffice_path: str | None = None

    # 目录选项
    generate_toc: bool = True
    toc_position: TOCPosition = TOCPosition.AFTER_TITLE

    # 其他
    include_header_footer: bool = False
    include_comments: bool = False
```

---

## 7. CLI工具

### 7.1 设计原则

- CLI与编程接口完全解耦
- BAT脚本作为唯一用户入口
- `python -m` 方式仅用于开发调试

### 7.2 BAT启动脚本

```batch
@echo off
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    pause
    exit /b 1
)

python -m wordparser_cli %*

if errorlevel 1 (
    pause
)
```

### 7.3 CLI命令

```bash
# 基础用法
wordparser.bat parse doc.docx -o out.md

# 高级选项
wordparser.bat parse doc.docx -o out.md ^
    --vision-url "http://localhost:1234/v1" ^
    --max-concurrent 8 ^
    --no-toc
```

---

## 8. 错误处理

### 8.1 异常体系

```python
WordParserError
├── DocumentError (致命)
│   ├── DocumentEncryptedError
│   ├── DocumentCorruptedError
│   └── UnsupportedFormatError
└── ContentProcessError (可恢复)
    ├── TableProcessError
    ├── ImageProcessError
    └── MultimodalAPIError
```

### 8.2 降级策略

| 失败场景 | 降级方案 |
|----------|----------|
| 复杂表格解析失败 | 简单MD转换 → 图片引用 |
| 图片多模态失败 | 保留原始图片+注释 |
| API调用超时 | 自动重试 → 降级标记 |
| LibreOffice未安装 | 跳过渲染类处理，仅提取原始图片资源 |

### 8.3 解析报告

```python
@dataclass
class ParseReport:
    success: bool
    output_path: Path | None
    errors: list[ParseError]
    stats: ParseStats
```

---

## 9. 项目结构

```
Document_Parsing/                    # 项目根目录
├── wordparser/                      # 核心库
│   ├── __init__.py                  # 导出 parse_word_to_markdown, ParserConfig 等
│   ├── config.py                    # 所有配置类
│   ├── exceptions.py                # 异常定义
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py                # 数据模型（ParsedDocument, TitleNode, ContentBlock, ResourceRegistry）
│   │   ├── report.py                # 解析报告（ParseReport, ParseError, ParseStats）
│   │   ├── parser.py                # WordParser主解析器
│   │   ├── preprocessor.py          # 预处理模块
│   │   ├── structure.py             # 结构解析模块
│   │   ├── tables.py                # 表格处理器
│   │   ├── images.py                # 图片处理器
│   │   ├── formulas.py              # 公式处理器（OMML→LaTeX）
│   │   ├── renderer.py              # Word元素渲染为图片（LibreOffice）
│   │   ├── toc.py                   # 目录生成
│   │   └── postprocess.py           # 后处理模块
│   └── multimodal/
│       ├── __init__.py
│       ├── client.py                # OpenAI兼容客户端
│       ├── parser.py                # 多模态解析器
│       ├── parallel.py              # 并行处理器
│       └── prompts.py               # Prompt模板
│
├── wordparser_cli/                  # CLI工具（解耦）
│   ├── __init__.py
│   ├── main.py                      # CLI入口
│   └── commands/
│       ├── __init__.py
│       ├── parse.py                 # parse命令
│       ├── multimodal.py            # multimodal命令（独立测试）
│       └── config.py                # config命令（生成配置）
│
├── wordparser.bat                   # 用户入口（根目录）
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_parser.py
│   ├── test_tables.py
│   ├── test_formulas.py
│   ├── test_multimodal.py
│   └── fixtures/
│       └── samples/                 # 测试用Word文档
│
├── docs/
│   └── 2026-04-22-word-parser-design.md
│
├── examples/
│   ├── basic_usage.py
│   └── advanced_config.py
│
├── pyproject.toml
└── README.md
```

---

## 10. 依赖项

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
```

**系统依赖：**
- LibreOffice（Word元素渲染为图片）
- Poppler（pdf2image后端，PDF转图片）

---

## 11. 实施优先级

| 阶段 | 功能 | 优先级 |
|------|------|--------|
| P0 | 核心解析流程（预处理+结构解析+后处理） | 必须 |
| P0 | 编程接口 + 数据模型 | 必须 |
| P1 | 表格处理（简单+复杂） | 高 |
| P1 | 图片处理（提取+多模态） | 高 |
| P1 | CLI工具 + BAT脚本 | 高 |
| P2 | 多模态集成（并行处理） | 中 |
| P2 | 公式处理（OMML→LaTeX） | 中 |
| P2 | 渲染器（LibreOffice集成） | 中 |
| P3 | 高级特性（脚注/批注/页眉页脚） | 低 |

---

*设计规格 v1.1 - 待评审*
