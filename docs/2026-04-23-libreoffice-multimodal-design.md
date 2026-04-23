# LibreOffice + 多模态扩展设计规格

**日期**: 2026-04-23
**版本**: 1.0
**状态**: 待实现

---

## 1. 概述

### 1.1 目标

在现有 WordParser 基础上扩展四大能力：

| 能力 | 说明 |
|------|------|
| .doc → .docx 自动转换 | 检测 .doc 格式自动调用 LibreOffice 转换，对用户透明 |
| Chart 图表解析 | 从 ZIP/XML 提取图表数据 + LLM 语义理解，生成结构化 Markdown |
| SmartArt 解析 | 从 ZIP/XML 提取节点关系 + LLM 语义理解，生成层级描述 |
| 复杂表格视觉降级 | 检测复杂表格 → 提取单元格数据 + 可选渲染 → 视觉模型重建 |

### 1.2 核心原则

- **默认零外部依赖**：XML 提取 + LLM 文本解析是主路径，纯 Python 实现
- **两级降级**：XML+LLM 失败 → LibreOffice 渲染+多模态 → 失败标记
- **单一模型接口**：统一使用 qwen3.5-9b 全模态模型（OpenAICompatibleVisionClient），文本走文本通道，图片走图片通道
- **配置驱动**：通过 `enable_render_fallback` 控制是否启用渲染降级

---

## 2. 模块架构

### 2.1 新增/修改文件

```
wordparser/
├── core/
│   ├── renderer.py            # [新增] LibreOffice 渲染器
│   ├── chart_extractor.py     # [新增] Chart 数据提取器
│   ├── smartart_extractor.py  # [新增] SmartArt 数据提取器
│   ├── parser.py              # [修改] 集成新模块到主流程
│   └── tables.py              # [修改] 增加复杂表格视觉降级
├── config.py                  # [修改] 新增配置项
└── multimodal/
    ├── parser.py              # [修改] 重构为视觉模型调用
    └── prompts.py             # [修改] 新增 Chart/SmartArt 提示词
```

### 2.2 模块职责

| 模块 | 职责 | 外部依赖 |
|------|------|----------|
| `ChartExtractor` | 从 .docx ZIP 中提取 chart XML + 嵌入 Excel，解析为结构化数据 | zipfile, openpyxl, lxml |
| `SmartArtExtractor` | 从 .docx ZIP 中提取 SmartArt XML，解析节点和关系 | zipfile, lxml |
| `DocumentRenderer` | LibreOffice 渲染：.doc 转换 + 元素/页面渲染为 PNG | LibreOffice CLI, pdf2image |
| `MultimodalParser` | 接收结构化数据或截图，调用视觉模型生成语义描述 | OpenAI client |

---

## 3. 配置扩展

```python
@dataclass
class ParserConfig:
    # 现有配置
    max_heading_level: int = 6
    encoding: str = "utf-8"
    multimodal: MultimodalConfig | None = None
    generate_toc: bool = True
    toc_position: TOCPosition = TOCPosition.AFTER_TITLE
    include_header_footer: bool = False
    include_comments: bool = False

    # 新增配置
    libreoffice_path: str | None = None        # LibreOffice 路径（自动检测）
    enable_render_fallback: bool = True         # XML+LLM 失败时是否降级到渲染+多模态
```

---

## 4. 数据模型

### 4.1 Chart 数据

```python
@dataclass
class SeriesData:
    name: str
    values: list[float | str]

@dataclass
class ChartData:
    chart_type: str              # bar/line/pie/scatter/area
    title: str | None
    categories: list[str]
    series: list[SeriesData]
    raw_xml: str                 # 保留原始 XML 用于 LLM
```

### 4.2 SmartArt 数据

```python
@dataclass
class SmartArtNode:
    text: str
    level: int
    children: list[SmartArtNode]

@dataclass
class SmartArtData:
    layout_type: str             # 流程/层次/循环/矩阵等
    root_nodes: list[SmartArtNode]
    raw_xml: str
```

---

## 5. 各元素处理流程

### 5.1 .doc → .docx 自动转换

```
输入文件
  ├─ .docx → 直接进入解析流程
  └─ .doc  → DocumentRenderer.convert_doc_to_docx()
              ├─ 成功 → 返回 .docx 路径 → 进入解析流程
              └─ LibreOffice 不可用 → 抛出 DocumentError
```

在 `WordParser._parse_document` 入口处自动处理，用户无需感知。

### 5.2 Chart 图表

```
.docx ZIP
  ├─ word/charts/chart1.xml   → ChartExtractor → ChartData（类型、系列、值）
  ├─ word/embeddings/*.xlsx   → openpyxl → 补充数据表
  └─ [降级] DocumentRenderer → 整页 PNG

主路径（XML + LLM）：
  ChartData → 格式化为结构化文本 → qwen3.5-9b 文本通道 → Markdown

降级路径（渲染 + 多模态）：
  整页 PNG → qwen3.5-9b 图片通道 → Markdown
```

**ChartExtractor 核心接口**：

```python
class ChartExtractor:
    def extract(self, docx_path: Path) -> list[ChartData]:
        """从 .docx ZIP 中提取所有图表数据"""

    def _parse_chart_xml(self, xml_content: str) -> ChartData:
        """解析单个 chart XML"""

    def _read_embedded_excel(self, docx_path: Path) -> dict[str, list[list]]:
        """读取嵌入的 Excel 数据，按图表名索引"""
```

### 5.3 SmartArt

```
.docx ZIP
  ├─ word/smartArt1.xml       → SmartArtExtractor → SmartArtData（节点、关系）
  ├─ word/smartArtData1.xml   → 补充布局类型
  └─ [降级] DocumentRenderer → 整页 PNG

主路径（XML + LLM）：
  SmartArtData → 格式化为层级文本 → qwen3.5-9b 文本通道 → Markdown

降级路径（渲染 + 多模态）：
  整页 PNG → qwen3.5-9b 图片通道 → Markdown
```

**SmartArtExtractor 核心接口**：

```python
class SmartArtExtractor:
    def extract(self, docx_path: Path) -> list[SmartArtData]:
        """从 .docx ZIP 中提取所有 SmartArt 数据"""

    def _parse_smartart_xml(self, xml_content: str) -> SmartArtData:
        """解析单个 SmartArt XML"""
```

### 5.4 复杂表格

```
TableProcessor.is_complex() 检测
  ├─ 简单表格 → 现有 process_simple() → Markdown 表格
  └─ 复杂表格 → 单元格数据提取 + LLM 解析
                  ├─ 成功 → Markdown 表格
                  └─ 失败 + enable_render_fallback
                      └─ 渲染截图 → qwen3.5-9b → Markdown 表格
```

---

## 6. DocumentRenderer

```python
class DocumentRenderer:
    """LibreOffice 渲染器"""

    def __init__(self, libreoffice_path: str | None = None):
        self.lo_path = libreoffice_path or self._detect_libreoffice()

    def convert_doc_to_docx(self, doc_path: Path, output_dir: Path) -> Path:
        """将 .doc 转换为 .docx"""
        # soffice --headless --convert-to docx --outdir <output_dir> <doc_path>

    def render_page_to_image(self, docx_path: Path, page_number: int = 0) -> bytes:
        """渲染整页为 PNG bytes
        流程：LibreOffice docx→PDF → pdf2image PDF→PNG → bytes
        """

    def is_available(self) -> bool:
        """检测 LibreOffice 是否可用"""

    def _detect_libreoffice(self) -> str | None:
        """自动检测 LibreOffice 路径"""
        # 搜索优先级：
        # 1. soffice（PATH 中）
        # 2. C:\Program Files\LibreOffice\program\soffice.exe
        # 3. C:\Program Files (x86)\LibreOffice\program\soffice.exe
```

---

## 7. 主流程集成

`WordParser._parse_document` 扩展点：

```python
def _parse_document(self, docx_path):
    docx_path = Path(docx_path)

    # 1. .doc 自动转换（新增）
    docx_path = self._ensure_docx(docx_path)

    # 2. 加载并预处理文档（现有）
    doc = DocxDocument(str(docx_path))
    doc = self.preprocessor.clean(doc)

    # 3. 结构解析（现有）
    blocks = self.structure_parser.parse(doc)
    title_tree = self.structure_parser.get_title_tree()

    # 4. 嵌入图片解析（现有）
    image_descriptions = self._parse_images(doc)

    # 5. Chart 解析（新增）
    chart_descriptions = self._parse_charts(docx_path)

    # 6. SmartArt 解析（新增）
    smartart_descriptions = self._parse_smartarts(docx_path)

    # 7. 复杂表格视觉降级（新增）
    table_blocks = self._parse_tables(doc)

    # 8. 生成 Markdown（现有 + 新内容整合）
    # 9. 后处理（现有）
```

---

## 8. 降级与错误处理

### 8.1 降级链路

```
XML + LLM 解析（默认，纯 python）
    ├─ 成功 → 输出结果
    └─ 失败 → enable_render_fallback=True?
                  ├─ 是 → LibreOffice 渲染 + 多模态识别
                  │         ├─ 成功 → 输出结果
                  │         └─ 失败 → 标记，继续
                  └─ 否 → 标记，继续
```

### 8.2 各场景处理

| 失败场景 | 降级策略 | 用户感知 |
|----------|----------|----------|
| .doc 但 LibreOffice 不可用 | 抛出 `DocumentError` | 解析失败，明确提示 |
| Chart XML 解析失败 | 尝试渲染降级 → 标记 | 输出有标记 |
| SmartArt XML 解析失败 | 尝试渲染降级 → 标记 | 输出有标记 |
| LibreOffice 渲染失败 | 标记 `[元素解析失败]` | 不中断流程 |
| 视觉模型 API 调用失败 | 重试 1 次 → 标记 | 输出有标记 |
| openpyxl 读取嵌入 Excel 失败 | 仅用 XML 数据 | 数据可能不完整 |

---

## 9. 输出示例

### 9.1 Chart 输出

```markdown
### 图表：季度销售趋势

**类型**: 折线图 | **系列**: 2个

| 季度 | 产品A | 产品B |
|------|-------|-------|
| Q1   | 120   | 80    |
| Q2   | 150   | 95    |
| Q3   | 180   | 110   |
| Q4   | 210   | 130   |

> **趋势分析**: 产品A和产品B均呈持续上升趋势，产品A增速更快。
```

### 9.2 SmartArt 输出

```markdown
### 流程图：项目开发流程

- 需求分析
  - 用户调研
  - 需求文档编写
- 设计阶段
  - 架构设计
  - 详细设计
- 开发实现
- 测试上线
```

### 9.3 复杂表格输出

```markdown
| 项目 | Q1 | Q2 | Q3 | Q4 |
|------|-----|-----|-----|-----|
| 收入 | 100 | 150 | 180 | 210 |
| 成本 | 60  | 70  | 75  | 80  |
| 利润 | 40  | 80  | 105 | 130 |
```

---

## 10. 依赖变更

```toml
dependencies = [
    # 现有
    "python-docx>=1.0",
    "httpx>=0.24",
    "pydantic>=2.0",
    "lxml>=4.9",
    "Pillow>=10.0",
    # 新增
    "openpyxl>=3.0",       # 读取 Chart 内嵌 Excel
    "pdf2image>=1.16",     # 渲染降级路径 PDF→PNG
]
```

系统依赖（可选）：
- **LibreOffice**：.doc 转换 + 渲染降级路径
- **Poppler**：pdf2image 后端

---

*设计规格 v1.0 - 待实现*
