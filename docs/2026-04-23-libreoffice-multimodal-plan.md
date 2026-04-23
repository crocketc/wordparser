# LibreOffice + 多模态扩展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 扩展 WordParser 支持 .doc 格式自动转换、Chart 图表解析、SmartArt 解析和复杂表格视觉降级。

**Architecture:** 两级降级链路——默认 XML 提取 + LLM 文本解析（纯 python），失败后可选降级到 LibreOffice 渲染 + 多模态视觉识别。所有解析统一走 qwen3.5-9b 全模态模型。

**Tech Stack:** python-docx, lxml, openpyxl, pdf2image, LibreOffice CLI, OpenAI SDK

---

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `wordparser/config.py` | 修改 | 新增 `enable_render_fallback` 配置项 |
| `wordparser/core/models.py` | 修改 | 新增 `ChartData`, `SeriesData`, `SmartArtNode`, `SmartArtData` 数据类 |
| `wordparser/core/chart_extractor.py` | 新增 | 从 ZIP 提取 chart XML + 嵌入 Excel，解析为结构化数据 |
| `wordparser/core/smartart_extractor.py` | 新增 | 从 ZIP 提取 SmartArt XML，解析节点和关系 |
| `wordparser/core/renderer.py` | 新增 | LibreOffice 渲染器：.doc 转换 + 页面渲染为 PNG |
| `wordparser/multimodal/client.py` | 修改 | 新增 `parse_text()` 文本解析方法 |
| `wordparser/multodal/parser.py` | 修改 | 重构 chart/smartart 方法，支持 XML+LLM 和渲染+视觉两种模式 |
| `wordparser/multimodal/prompts.py` | 修改 | 新增 Chart/SmartArt 结构化数据 LLM 提示词 |
| `wordparser/core/parser.py` | 修改 | 集成 .doc 转换、chart/smartart/复杂表格解析到主流程 |
| `wordparser/core/tables.py` | 修改 | 新增复杂表格 LLM 解析方法 |
| `wordparser_cli/main.py` | 修改 | 接受 .doc 文件、新增 render fallback CLI 选项 |
| `pyproject.toml` | 修改 | 新增 openpyxl 依赖 |
| `tests/conftest.py` | 新增 | 测试基础设施 |
| `tests/test_chart_extractor.py` | 新增 | Chart 提取器测试 |
| `tests/test_smartart_extractor.py` | 新增 | SmartArt 提取器测试 |
| `tests/test_renderer.py` | 新增 | 渲染器测试 |
| `tests/test_integration.py` | 新增 | 集成测试 |

---

## Task 1: 基础设施 — 配置扩展 + 数据模型 + 依赖 + 测试骨架

**Files:**
- Modify: `wordparser/config.py`
- Modify: `wordparser/core/models.py`
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 更新 pyproject.toml 添加 openpyxl 依赖**

在 `dependencies` 列表中 `Pillow` 行后添加 openpyxl：

```toml
dependencies = [
    "python-docx>=1.0",
    "httpx>=0.24",
    "pydantic>=2.0",
    "pdf2image>=1.16",
    "lxml>=4.9",
    "Pillow>=10.0",
    "openpyxl>=3.0",
]
```

- [ ] **Step 2: 安装新依赖**

Run: `pip install openpyxl>=3.0`

- [ ] **Step 3: 更新 config.py 添加 enable_render_fallback**

在 `ParserConfig` 中 `libreoffice_path` 行后添加：

```python
    libreoffice_path: str | None = None
    enable_render_fallback: bool = True
```

- [ ] **Step 4: 更新 models.py 添加数据类**

在 `ParsedDocument` 类之后添加：

```python
@dataclass
class SeriesData:
    name: str
    values: list[float | str]


@dataclass
class ChartData:
    chart_type: str
    title: str | None
    categories: list[str]
    series: list[SeriesData]
    raw_xml: str


@dataclass
class SmartArtNode:
    text: str
    level: int
    children: list[SmartArtNode] = field(default_factory=list)


@dataclass
class SmartArtData:
    layout_type: str
    root_nodes: list[SmartArtNode]
    raw_xml: str
```

- [ ] **Step 5: 创建测试骨架**

Create `tests/__init__.py`（空文件）。

Create `tests/conftest.py`：

```python
"""WordParser 测试配置"""
from pathlib import Path
import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR
```

- [ ] **Step 6: 验证导入**

Run: `python -c "from wordparser.config import ParserConfig; from wordparser.core.models import ChartData, SmartArtData; print('OK')"`

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add wordparser/config.py wordparser/core/models.py pyproject.toml tests/
git commit -m "feat: add config, data models, and test infrastructure for multimodal extension"
```

---

## Task 2: ChartExtractor — 图表 XML 解析

**Files:**
- Create: `wordparser/core/chart_extractor.py`
- Create: `tests/test_chart_extractor.py`

- [ ] **Step 1: 编写 ChartExtractor 测试**

Create `tests/test_chart_extractor.py`：

```python
"""ChartExtractor 测试"""
import pytest
from wordparser.core.chart_extractor import ChartExtractor


CHART_XML_BAR = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <c:chart>
    <c:title>
      <c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>Sales Report</a:t></a:r></a:p></c:rich></c:tx>
    </c:title>
    <c:autoTitleDeleted val="0"/>
    <c:plotArea>
      <c:barChart>
        <c:barDir val="col"/>
        <c:ser>
          <c:idx val="0"/>
          <c:tx><c:strRef><c:f>Sheet1!$B$1</c:f><c:strCache><c:ptCount val="1"/><c:pt idx="0"><c:v>Product A</c:v></c:pt></c:strCache></c:strRef></c:tx>
          <c:cat><c:strRef><c:f>Sheet1!$A$2:$A$4</c:f><c:strCache><c:ptCount val="3"/><c:pt idx="0"><c:v>Q1</c:v></c:pt><c:pt idx="1"><c:v>Q2</c:v></c:pt><c:pt idx="2"><c:v>Q3</c:v></c:pt></c:strCache></c:strRef></c:cat>
          <c:val><c:numRef><c:f>Sheet1!$B$2:$B$4</c:f><c:numCache><c:ptCount val="3"/><c:pt idx="0"><c:v>120</c:v></c:pt><c:pt idx="1"><c:v>150</c:v></c:pt><c:pt idx="2"><c:v>180</c:v></c:pt></c:numCache></c:numRef></c:val>
        </c:ser>
      </c:barChart>
    </c:plotArea>
  </c:chart>
</c:chartSpace>'''

CHART_XML_PIE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
  <c:chart>
    <c:title>
      <c:tx><c:rich xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:bodyPr/><a:p><a:r><a:t>Market Share</a:t></a:r></a:p></c:rich></c:tx>
    </c:title>
    <c:autoTitleDeleted val="0"/>
    <c:plotArea>
      <c:pieChart>
        <c:ser>
          <c:idx val="0"/>
          <c:tx><c:strRef><c:strCache><c:ptCount val="1"/><c:pt idx="0"><c:v>Share</c:v></c:pt></c:strCache></c:strRef></c:tx>
          <c:cat><c:strRef><c:strCache><c:ptCount val="3"/><c:pt idx="0"><c:v>A</c:v></c:pt><c:pt idx="1"><c:v>B</c:v></c:pt><c:pt idx="2"><c:v>C</c:v></c:pt></c:strCache></c:strRef></c:cat>
          <c:val><c:numRef><c:numCache><c:ptCount val="3"/><c:pt idx="0"><c:v>40</c:v></c:pt><c:pt idx="1"><c:v>35</c:v></c:pt><c:pt idx="2"><c:v>25</c:v></c:pt></c:numCache></c:numRef></c:val>
        </c:ser>
      </c:pieChart>
    </c:plotArea>
  </c:chart>
</c:chartSpace>'''

CHART_XML_NO_TITLE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
  <c:chart>
    <c:autoTitleDeleted val="1"/>
    <c:plotArea>
      <c:lineChart>
        <c:ser>
          <c:idx val="0"/>
          <c:tx><c:strRef><c:strCache><c:ptCount val="1"/><c:pt idx="0"><c:v>Series1</c:v></c:pt></c:strCache></c:strRef></c:tx>
          <c:cat><c:strRef><c:strCache><c:ptCount val="2"/><c:pt idx="0"><c:v>X1</c:v></c:pt><c:pt idx="1"><c:v>X2</c:v></c:pt></c:strCache></c:strRef></c:cat>
          <c:val><c:numRef><c:numCache><c:ptCount val="2"/><c:pt idx="0"><c:v>10</c:v></c:pt><c:pt idx="1"><c:v>20</c:v></c:pt></c:numCache></c:numRef></c:val>
        </c:ser>
      </c:lineChart>
    </c:plotArea>
  </c:chart>
</c:chartSpace>'''


class TestChartExtractor:
    def setup_method(self):
        self.extractor = ChartExtractor()

    def test_parse_bar_chart(self):
        result = self.extractor._parse_chart_xml(CHART_XML_BAR)
        assert result.chart_type == "bar"
        assert result.title == "Sales Report"
        assert result.categories == ["Q1", "Q2", "Q3"]
        assert len(result.series) == 1
        assert result.series[0].name == "Product A"
        assert result.series[0].values == [120.0, 150.0, 180.0]

    def test_parse_pie_chart(self):
        result = self.extractor._parse_chart_xml(CHART_XML_PIE)
        assert result.chart_type == "pie"
        assert result.title == "Market Share"
        assert result.categories == ["A", "B", "C"]
        assert result.series[0].values == [40.0, 35.0, 25.0]

    def test_parse_line_chart_no_title(self):
        result = self.extractor._parse_chart_xml(CHART_XML_NO_TITLE)
        assert result.chart_type == "line"
        assert result.title is None
        assert result.categories == ["X1", "X2"]

    def test_format_chart_data_for_llm(self):
        from wordparser.core.models import ChartData, SeriesData
        data = ChartData(
            chart_type="bar",
            title="Test Chart",
            categories=["A", "B", "C"],
            series=[SeriesData(name="S1", values=[1.0, 2.0, 3.0])],
            raw_xml="<xml/>",
        )
        text = self.extractor.format_for_llm(data)
        assert "柱状图" in text
        assert "Test Chart" in text
        assert "S1" in text

    def test_chart_type_mapping(self):
        assert self.extractor._map_chart_type("barChart") == "bar"
        assert self.extractor._map_chart_type("lineChart") == "line"
        assert self.extractor._map_chart_type("pieChart") == "pie"
        assert self.extractor._map_chart_type("areaChart") == "area"
        assert self.extractor._map_chart_type("scatterChart") == "scatter"
        assert self.extractor._map_chart_type("unknownChart") == "unknown"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_chart_extractor.py -v`

Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: 实现 ChartExtractor**

Create `wordparser/core/chart_extractor.py`：

```python
"""Chart 数据提取器

从 .docx ZIP 包中提取 Chart XML 和嵌入 Excel，解析为结构化数据。
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Optional

from wordparser.core.models import ChartData, SeriesData

C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

CHART_TYPE_LABELS = {
    "bar": "柱状图",
    "line": "折线图",
    "pie": "饼图",
    "area": "面积图",
    "scatter": "散点图",
    "unknown": "未知类型",
}


class ChartExtractor:
    """从 .docx 中提取 Chart 数据"""

    def extract(self, docx_path: Path) -> list[ChartData]:
        """从 .docx ZIP 中提取所有图表数据"""
        results = []
        docx_path = Path(docx_path)

        with zipfile.ZipFile(docx_path, "r") as zf:
            chart_files = sorted(
                [n for n in zf.namelist() if n.startswith("word/charts/") and n.endswith(".xml")]
            )

            for chart_file in chart_files:
                xml_content = zf.read(chart_file).decode("utf-8")
                chart_data = self._parse_chart_xml(xml_content)
                if chart_data:
                    results.append(chart_data)

        return results

    def _parse_chart_xml(self, xml_content: str) -> Optional[ChartData]:
        """解析单个 chart XML"""
        chart_type = self._detect_chart_type(xml_content)
        title = self._extract_title(xml_content)
        categories = self._extract_categories(xml_content)
        series_list = self._extract_series(xml_content)

        return ChartData(
            chart_type=chart_type,
            title=title,
            categories=categories,
            series=series_list,
            raw_xml=xml_content,
        )

    def _detect_chart_type(self, xml: str) -> str:
        """检测图表类型"""
        type_patterns = {
            "barChart": "bar",
            "bar3DChart": "bar",
            "lineChart": "line",
            "line3DChart": "line",
            "pieChart": "pie",
            "pie3DChart": "pie",
            "areaChart": "area",
            "area3DChart": "area",
            "scatterChart": "scatter",
            "doughnutChart": "pie",
            "bubbleChart": "scatter",
        }
        for tag, ctype in type_patterns.items():
            if tag in xml:
                return ctype
        return "unknown"

    def _map_chart_type(self, xml_tag: str) -> str:
        """将 XML 标签名映射为图表类型"""
        mapping = {
            "barChart": "bar",
            "lineChart": "line",
            "pieChart": "pie",
            "areaChart": "area",
            "scatterChart": "scatter",
        }
        return mapping.get(xml_tag, "unknown")

    def _extract_title(self, xml: str) -> Optional[str]:
        """提取图表标题"""
        # 检查 autoTitleDeleted="1" 表示无标题
        if re.search(r'autoTitleDeleted[^>]*val="1"', xml):
            return None

        # 查找 <a:t>标题文本</a:t> 在 title 区域内
        title_match = re.search(r'<c:title>.*?<a:t>([^<]+)</a:t>.*?</c:title>', xml, re.DOTALL)
        if title_match:
            return title_match.group(1).strip()

        return None

    def _extract_categories(self, xml: str) -> list[str]:
        """提取类别标签"""
        # 在 <c:cat> 内查找 <c:v>文本</c:v>
        cat_match = re.search(r'<c:cat>.*?</c:cat>', xml, re.DOTALL)
        if not cat_match:
            return []

        cat_block = cat_match.group(0)
        return re.findall(r'<c:v>([^<]+)</c:v>', cat_block)

    def _extract_series(self, xml: str) -> list[SeriesData]:
        """提取所有数据系列"""
        series_list = []

        # 查找所有 <c:ser> 块
        ser_blocks = re.findall(r'<c:ser>.*?</c:ser>', xml, re.DOTALL)

        for block in ser_blocks:
            # 系列名
            name_match = re.search(r'<c:tx>.*?<c:v>([^<]+)</c:v>.*?</c:tx>', block, re.DOTALL)
            name = name_match.group(1).strip() if name_match else f"系列{len(series_list) + 1}"

            # 系列值
            val_match = re.search(r'<c:val>.*?</c:val>', block, re.DOTALL)
            values = []
            if val_match:
                val_block = val_match.group(0)
                value_strs = re.findall(r'<c:v>([^<]+)</c:v>', val_block)
                for v in value_strs:
                    try:
                        values.append(float(v))
                    except ValueError:
                        values.append(v)

            series_list.append(SeriesData(name=name, values=values))

        return series_list

    def format_for_llm(self, data: ChartData) -> str:
        """将 ChartData 格式化为 LLM 可理解的结构化文本"""
        lines = []
        type_label = CHART_TYPE_LABELS.get(data.chart_type, data.chart_type)
        lines.append(f"图表类型: {type_label}")
        if data.title:
            lines.append(f"标题: {data.title}")
        lines.append(f"数据系列数: {len(data.series)}")
        lines.append(f"类别: {', '.join(data.categories)}")
        lines.append("")
        lines.append("数据:")
        for series in data.series:
            values_str = ", ".join(str(v) for v in series.values)
            lines.append(f"  {series.name}: [{values_str}]")

        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_chart_extractor.py -v`

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/chart_extractor.py tests/test_chart_extractor.py
git commit -m "feat: add ChartExtractor - parse chart XML data from docx ZIP"
```

---

## Task 3: SmartArtExtractor — SmartArt XML 解析

**Files:**
- Create: `wordparser/core/smartart_extractor.py`
- Create: `tests/test_smartart_extractor.py`

- [ ] **Step 1: 编写 SmartArtExtractor 测试**

Create `tests/test_smartart_extractor.py`：

```python
"""SmartArtExtractor 测试"""
import pytest
from wordparser.core.smartart_extractor import SmartArtExtractor


SMARTART_DATA_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<dgm:dataModel xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <dgm:ptLst>
    <dgm:pt modelId="0" type="doc">
      <dgm:prSet/>
      <dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="1">
      <dgm:prSet/>
      <dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>根节点</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="2">
      <dgm:prSet/>
      <dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>子节点A</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="3">
      <dgm:prSet/>
      <dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>子节点B</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="4">
      <dgm:prSet/>
      <dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>孙节点</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
  </dgm:ptLst>
  <dgm:cxnLst>
    <dgm:cxn modelId="5" srcId="0" destId="1" type="parOf"/>
    <dgm:cxn modelId="6" srcId="1" destId="2" type="parOf"/>
    <dgm:cxn modelId="7" srcId="1" destId="3" type="parOf"/>
    <dgm:cxn modelId="8" srcId="2" destId="4" type="parOf"/>
  </dgm:cxnLst>
</dgm:dataModel>'''

SMARTART_EMPTY_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<dgm:dataModel xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <dgm:ptLst>
    <dgm:pt modelId="0" type="doc">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p></dgm:t>
    </dgm:pt>
  </dgm:ptLst>
  <dgm:cxnLst/>
</dgm:dataModel>'''


class TestSmartArtExtractor:
    def setup_method(self):
        self.extractor = SmartArtExtractor()

    def test_parse_smartart_data(self):
        result = self.extractor._parse_smartart_xml(SMARTART_DATA_XML)
        assert len(result.root_nodes) >= 1
        root = result.root_nodes[0]
        assert root.text == "根节点"
        assert len(root.children) == 2
        assert root.children[0].text == "子节点A"
        assert root.children[1].text == "子节点B"
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0].text == "孙节点"

    def test_parse_empty_smartart(self):
        result = self.extractor._parse_smartart_xml(SMARTART_EMPTY_XML)
        assert len(result.root_nodes) == 0

    def test_format_smartart_for_llm(self):
        from wordparser.core.models import SmartArtData, SmartArtNode
        data = SmartArtData(
            layout_type="process",
            root_nodes=[
                SmartArtNode(text="步骤1", level=0, children=[
                    SmartArtNode(text="子步骤", level=1),
                ]),
                SmartArtNode(text="步骤2", level=0),
            ],
            raw_xml="<xml/>",
        )
        text = self.extractor.format_for_llm(data)
        assert "步骤1" in text
        assert "子步骤" in text
        assert "步骤2" in text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_smartart_extractor.py -v`

Expected: FAIL

- [ ] **Step 3: 实现 SmartArtExtractor**

Create `wordparser/core/smartart_extractor.py`：

```python
"""SmartArt 数据提取器

从 .docx ZIP 包中提取 SmartArt (diagram) XML，解析节点和关系。
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Optional

from wordparser.core.models import SmartArtData, SmartArtNode

DGM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


class SmartArtExtractor:
    """从 .docx 中提取 SmartArt 数据"""

    def extract(self, docx_path: Path) -> list[SmartArtData]:
        """从 .docx ZIP 中提取所有 SmartArt 数据"""
        results = []
        docx_path = Path(docx_path)

        with zipfile.ZipFile(docx_path, "r") as zf:
            # SmartArt 数据文件在 word/diagrams/data*.xml
            data_files = sorted(
                [n for n in zf.namelist() if n.startswith("word/diagrams/data") and n.endswith(".xml")]
            )

            for data_file in data_files:
                xml_content = zf.read(data_file).decode("utf-8")
                smartart_data = self._parse_smartart_xml(xml_content)
                if smartart_data:
                    results.append(smartart_data)

        return results

    def _parse_smartart_xml(self, xml_content: str) -> Optional[SmartArtData]:
        """解析 SmartArt data XML"""
        # 提取所有点（pt）— 包含文本内容
        points = self._extract_points(xml_content)
        # 提取所有连接（cxn）— 包含父子关系
        connections = self._extract_connections(xml_content)

        # 构建树
        root_nodes = self._build_tree(points, connections)

        return SmartArtData(
            layout_type=self._detect_layout_type(xml_content),
            root_nodes=root_nodes,
            raw_xml=xml_content,
        )

    def _extract_points(self, xml: str) -> dict[int, tuple[str, str]]:
        """提取所有节点：返回 {modelId: (type, text)}"""
        points = {}
        # 匹配 <dgm:pt modelId="N" type="T">...<a:t>文本</a:t>...</dgm:pt>
        pt_pattern = re.finditer(
            r'<dgm:pt\s+modelId="(\d+)"(?:\s+type="([^"]*)")?\s*>.*?</dgm:pt>',
            xml, re.DOTALL,
        )
        for match in pt_pattern:
            model_id = int(match.group(1))
            pt_type = match.group(2) or ""
            pt_block = match.group(0)

            # 提取 <a:t> 文本
            texts = re.findall(r'<a:t>([^<]+)</a:t>', pt_block)
            text = " ".join(texts).strip()

            points[model_id] = (pt_type, text)

        return points

    def _extract_connections(self, xml: str) -> list[tuple[int, int]]:
        """提取父子关系：返回 [(parentId, childId), ...]"""
        connections = []
        cxn_pattern = re.finditer(
            r'<dgm:cxn\s+[^>]*srcId="(\d+)"[^>]*destId="(\d+)"[^>]*type="parOf"[^>]*/?\s*>',
            xml,
        )
        for match in cxn_pattern:
            src_id = int(match.group(1))
            dest_id = int(match.group(2))
            connections.append((src_id, dest_id))

        # 也匹配完整闭合标签形式
        cxn_full = re.finditer(
            r'<dgm:cxn\s+[^>]*srcId="(\d+)"[^>]*destId="(\d+)"[^>]*type="parOf"[^>]*>.*?</dgm:cxn>',
            xml, re.DOTALL,
        )
        existing = set(connections)
        for match in cxn_full:
            pair = (int(match.group(1)), int(match.group(2)))
            if pair not in existing:
                connections.append(pair)

        return connections

    def _build_tree(
        self,
        points: dict[int, tuple[str, str]],
        connections: list[tuple[int, int]],
    ) -> list[SmartArtNode]:
        """根据连接关系构建节点树"""
        # 构建 parent → children 映射
        children_map: dict[int, list[int]] = {}
        for parent_id, child_id in connections:
            children_map.setdefault(parent_id, []).append(child_id)

        # 找根节点：被 doc 类型节点（modelId=0, type="doc"）连接的节点
        doc_children = children_map.get(0, [])
        if not doc_children:
            # 没有 doc 节点连接，取所有没有父节点的非 doc 节点
            all_children = {child for _, child in connections}
            all_parents = {parent for parent, _ in connections}
            root_ids = [
                pid for pid in points
                if pid != 0 and points[pid][0] != "doc" and pid not in all_children
            ]
        else:
            root_ids = doc_children

        def make_node(node_id: int, level: int) -> SmartArtNode:
            _, text = points.get(node_id, ("", ""))
            child_ids = children_map.get(node_id, [])
            children = [make_node(cid, level + 1) for cid in child_ids]
            return SmartArtNode(text=text, level=level, children=children)

        return [make_node(rid, 0) for rid in root_ids]

    def _detect_layout_type(self, xml: str) -> str:
        """检测 SmartArt 布局类型（简化）"""
        # 布局信息通常在 drawing XML 中，这里做简单推断
        return "unknown"

    def format_for_llm(self, data: SmartArtData) -> str:
        """将 SmartArtData 格式化为 LLM 可理解的结构化文本"""
        lines = []
        lines.append("SmartArt 类型: 流程/结构图")
        lines.append(f"节点数: {self._count_nodes(data.root_nodes)}")
        lines.append("")
        lines.append("节点结构:")

        def format_node(node: SmartArtNode, indent: int = 0):
            prefix = "  " * indent + "- " if indent > 0 else "- "
            lines.append(f"{prefix}{node.text}")
            for child in node.children:
                format_node(child, indent + 1)

        for node in data.root_nodes:
            format_node(node)

        return "\n".join(lines)

    def _count_nodes(self, nodes: list[SmartArtNode]) -> int:
        """递归计算节点数"""
        count = len(nodes)
        for node in nodes:
            count += self._count_nodes(node.children)
        return count
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_smartart_extractor.py -v`

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/smartart_extractor.py tests/test_smartart_extractor.py
git commit -m "feat: add SmartArtExtractor - parse SmartArt XML from docx ZIP"
```

---

## Task 4: DocumentRenderer — LibreOffice 封装

**Files:**
- Create: `wordparser/core/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: 编写 renderer 测试**

Create `tests/test_renderer.py`：

```python
"""DocumentRenderer 测试"""
import pytest
from wordparser.core.renderer import DocumentRenderer


class TestDocumentRenderer:
    def test_detect_libreoffice_returns_string_or_none(self):
        renderer = DocumentRenderer()
        # 不假设 LibreOffice 已安装，只验证返回类型
        result = renderer._detect_libreoffice()
        assert result is None or isinstance(result, str)

    def test_is_available_without_libreoffice(self):
        renderer = DocumentRenderer(libreoffice_path="/nonexistent/soffice")
        assert renderer.is_available() is False

    def test_is_doc_detection(self):
        from pathlib import Path
        renderer = DocumentRenderer()
        assert renderer.is_doc(Path("test.doc")) is True
        assert renderer.is_doc(Path("test.docx")) is False
        assert renderer.is_doc(Path("test.DOC")) is True
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_renderer.py -v`

Expected: FAIL

- [ ] **Step 3: 实现 DocumentRenderer**

Create `wordparser/core/renderer.py`：

```python
"""LibreOffice 渲染器

提供 .doc → .docx 转换和页面渲染为图片功能。
LibreOffice 是可选依赖，不可用时相关功能自动跳过。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class DocumentRenderer:
    """LibreOffice 文档渲染器"""

    def __init__(self, libreoffice_path: str | None = None):
        self.lo_path = libreoffice_path or self._detect_libreoffice()

    def is_available(self) -> bool:
        """检测 LibreOffice 是否可用"""
        if not self.lo_path:
            return False
        try:
            result = subprocess.run(
                [self.lo_path, "--version"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_doc(self, path: Path) -> bool:
        """检测是否为 .doc 格式（非 .docx）"""
        return path.suffix.lower() == ".doc"

    def convert_doc_to_docx(self, doc_path: Path, output_dir: Path | None = None) -> Path:
        """将 .doc 转换为 .docx，返回转换后的路径"""
        if not self.is_available():
            raise RuntimeError("LibreOffice 不可用，无法转换 .doc 文件")

        doc_path = Path(doc_path)
        output_dir = output_dir or doc_path.parent

        result = subprocess.run(
            [
                self.lo_path,
                "--headless",
                "--convert-to", "docx",
                "--outdir", str(output_dir),
                str(doc_path),
            ],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice 转换失败: {result.stderr}")

        output_path = output_dir / doc_path.with_suffix(".docx").name
        if not output_path.exists():
            raise RuntimeError(f"转换输出文件不存在: {output_path}")

        return output_path

    def render_page_to_image(self, docx_path: Path, page_number: int = 0) -> bytes:
        """渲染指定页为 PNG bytes

        流程：LibreOffice docx→PDF → pdf2image PDF→PNG → bytes
        """
        if not self.is_available():
            raise RuntimeError("LibreOffice 不可用")

        from pdf2image import convert_from_path

        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: docx → PDF
            subprocess.run(
                [
                    self.lo_path,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", tmpdir,
                    str(docx_path),
                ],
                capture_output=True, text=True, timeout=120,
            )

            pdf_path = Path(tmpdir) / docx_path.with_suffix(".pdf").name
            if not pdf_path.exists():
                raise RuntimeError(f"PDF 渲染失败: {pdf_path}")

            # Step 2: PDF → PNG
            images = convert_from_path(str(pdf_path), first_page=page_number + 1, last_page=page_number + 1)
            if not images:
                raise RuntimeError(f"页面 {page_number} 渲染为图片失败")

            import io
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            return buf.getvalue()

    def _detect_libreoffice(self) -> str | None:
        """自动检测 LibreOffice 路径"""
        # 1. 检查 PATH
        path_result = shutil.which("soffice")
        if path_result:
            return path_result

        # 2. Windows 常见路径
        candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate

        # 3. Linux/macOS 常见路径
        linux_candidates = [
            "/usr/bin/soffice",
            "/usr/local/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
        for candidate in linux_candidates:
            if Path(candidate).exists():
                return candidate

        return None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_renderer.py -v`

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add wordparser/core/renderer.py tests/test_renderer.py
git commit -m "feat: add DocumentRenderer - LibreOffice wrapper for doc conversion and page rendering"
```

---

## Task 5: 视觉客户端文本模式 + 提示词更新

**Files:**
- Modify: `wordparser/multimodal/client.py`
- Modify: `wordparser/multimodal/prompts.py`

- [ ] **Step 1: 在 client.py 中添加 parse_text 方法**

在 `OpenAICompatibleVisionClient` 类的 `parse_from_file` 方法之后添加：

```python
    def parse_text(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """纯文本对话，用于 LLM 解析结构化数据

        Args:
            prompt: 完整的提示词（包含数据）
            max_tokens: 覆盖默认的最大 token 数
            temperature: 覆盖默认的温度参数

        Returns:
            模型的回复文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
        )

        return response.choices[0].message.content
```

- [ ] **Step 2: 更新 prompts.py 添加 Chart/SmartArt 结构化数据提示词**

在 `SMARTART_PROMPT` 常量之后添加：

```python
# Chart 结构化数据 LLM 提示词（XML 提取模式）
CHART_DATA_PROMPT = """你是一个专业的数据分析师。以下是从一个图表中提取的结构化数据，请将其转换为清晰的 Markdown 格式。

要求：
1. 输出图表标题（如有）
2. 用 Markdown 表格展示数据
3. 简要描述图表中的关键趋势或发现

图表数据：
{chart_data}

请直接输出 Markdown 格式结果。"""

# SmartArt 结构化数据 LLM 提示词（XML 提取模式）
SMARTART_DATA_PROMPT = """你是一个专业的内容整理专家。以下是从一个 SmartArt 图形中提取的结构化数据，请将其转换为清晰的 Markdown 格式。

要求：
1. 用 Markdown 列表展示节点层级关系
2. 保留原始的层级缩进
3. 如有流程逻辑，用箭头或编号标注步骤顺序

SmartArt 数据：
{smartart_data}

请直接输出 Markdown 格式结果。"""

# 复杂表格 LLM 提示词
COMPLEX_TABLE_PROMPT = """你是一个专业的表格数据整理专家。以下是一个复杂 Word 表格的单元格数据，请将其重建为正确的 Markdown 表格。

要求：
1. 准确识别表头行
2. 处理合并单元格（用 colspan/rowspan 标注或拆分为多个单元格）
3. 保持数据的对齐关系

单元格数据：
{table_data}

请直接输出 Markdown 表格。"""
```

- [ ] **Step 3: 验证导入**

Run: `python -c "from wordparser.multimodal.client import OpenAICompatibleVisionClient; from wordparser.multimodal.prompts import CHART_DATA_PROMPT, SMARTART_DATA_PROMPT, COMPLEX_TABLE_PROMPT; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add wordparser/multimodal/client.py wordparser/multimodal/prompts.py
git commit -m "feat: add text-only LLM method and chart/smartart/table prompts"
```

---

## Task 6: 降级链路逻辑 — MultimodalParser 重构

**Files:**
- Modify: `wordparser/multimodal/parser.py`

- [ ] **Step 1: 重构 MultimodalParser**

将 `wordparser/multimodal/parser.py` 重写为支持两种模式的解析器：

```python
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
        # 主路径：结构化数据 + LLM 文本通道
        try:
            return self._parse_chart_via_llm(chart_data)
        except Exception as e:
            logger.warning(f"Chart LLM 解析失败: {e}")

        # 降级路径：渲染 + 视觉
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
        from wordparser.multimodal.prompts import TABLE_PROMPT
        image_bytes = self.renderer.render_page_to_image(docx_path)
        result = self.vision_client.parse_from_bytes(image_bytes, TABLE_PROMPT)
        return MultimodalResult(
            content=result,
            confidence=0.8,
            metadata={"type": "table", "method": "render_vision"},
        )
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from wordparser.multimodal.parser import MultimodalParser, MultimodalResult; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add wordparser/multimodal/parser.py
git commit -m "refactor: MultimodalParser with XML+LLM and render+vision fallback chain"
```

---

## Task 7: 复杂表格处理扩展

**Files:**
- Modify: `wordparser/core/tables.py`

- [ ] **Step 1: 在 TableProcessor 中添加复杂表格数据提取和 LLM 解析方法**

在 `TableProcessor` 类的 `is_complex` 方法之后添加：

```python
    def extract_table_data(self, table: Table) -> str:
        """提取表格的完整单元格数据，用于 LLM 解析

        Args:
            table: docx Table 对象

        Returns:
            格式化的单元格数据文本
        """
        if not table:
            return ""

        lines = []
        for row_idx, row in enumerate(table.rows):
            cells = []
            for cell in row.cells:
                cell_text = cell.text.strip().replace("\n", " ")
                # 检测合并单元格
                merge_info = ""
                tc_pr = cell._element.tcPr
                if tc_pr is not None:
                    grid_span = tc_pr.gridSpan
                    if grid_span is not None and grid_span.val > 1:
                        merge_info = f"[colspan={grid_span.val}]"
                    v_merge = tc_pr.vMerge
                    if v_merge is not None:
                        merge_info += "[rowspan]"
                cells.append(f"{cell_text}{merge_info}")
            lines.append(f"行{row_idx}: {' | '.join(cells)}")

        return "\n".join(lines)
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from wordparser.core.tables import TableProcessor; t = TableProcessor(); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add wordparser/core/tables.py
git commit -m "feat: add extract_table_data method for complex table LLM parsing"
```

---

## Task 8: 主解析器集成

**Files:**
- Modify: `wordparser/core/parser.py`

这是核心集成任务，将所有新模块接入主解析流程。

- [ ] **Step 1: 重写 parser.py 集成所有新模块**

将 `wordparser/core/parser.py` 重写为：

```python
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

        # Chart / SmartArt 提取器
        self.chart_extractor = ChartExtractor()
        self.smartart_extractor = SmartArtExtractor()

        # LibreOffice 渲染器
        self.renderer = DocumentRenderer(
            libreoffice_path=self.config.libreoffice_path,
        )

        # 视觉客户端
        self.vision_client = None
        if self.config.multimodal:
            from wordparser.multimodal.client import OpenAICompatibleVisionClient
            self.vision_client = OpenAICompatibleVisionClient(
                base_url=self.config.multimodal.model.base_url,
                model=self.config.multimodal.model.model,
                temperature=self.config.multimodal.model.temperature,
            )

        # 多模态解析器（降级链路）
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
                for i, desc in enumerate(chart_descriptions):
                    markdown_lines.append(f"{desc}\n\n")

            # SmartArt 描述
            if smartart_descriptions:
                markdown_lines.append("\n## SmartArt 内容\n\n")
                for i, desc in enumerate(smartart_descriptions):
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
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from wordparser.core.parser import WordParser; p = WordParser(); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add wordparser/core/parser.py
git commit -m "feat: integrate chart, smartart, complex table, and doc conversion into main parser"
```

---

## Task 9: CLI 更新

**Files:**
- Modify: `wordparser_cli/main.py`

- [ ] **Step 1: 更新 CLI 接受 .doc 文件并添加新选项**

在 `parse` 命令中修改参数和配置构建：

1. 将 `docx_file` 参数的 help 文本改为接受 `.doc` 和 `.docx`
2. 添加 `enable_render_fallback` 选项
3. 更新配置构建逻辑

将 `parse` 函数替换为：

```python
@app.command()
def parse(
    docx_file: str = typer.Argument(
        ...,
        help="要解析的Word文档路径（支持 .doc 和 .docx）",
        exists=True,
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="输出Markdown文件路径（默认打印到 stdout）",
    ),
    vision_url: Optional[str] = typer.Option(
        None,
        "--vision-url",
        help="多模态视觉模型API地址",
    ),
    vision_model: Optional[str] = typer.Option(
        None,
        "--vision-model",
        help="视觉模型名称",
    ),
    max_concurrent: int = typer.Option(
        4,
        "--max-concurrent",
        help="最大并发请求数",
    ),
    render_fallback: bool = typer.Option(
        True,
        "--render-fallback/--no-render-fallback",
        help="解析失败时是否降级到LibreOffice渲染+多模态识别",
    ),
    libreoffice_path: Optional[str] = typer.Option(
        None,
        "--libreoffice-path",
        help="LibreOffice 可执行文件路径（自动检测）",
    ),
    toc: bool = typer.Option(
        True,
        "--toc/--no-toc",
        help="是否生成目录",
    ),
    max_heading: int = typer.Option(
        6,
        "--max-heading",
        help="最大标题级别（1-6）",
        min=1,
        max=6,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="显示详细信息",
    ),
):
    """
    解析Word文档为Markdown格式

    示例:
        wordparser parse document.docx
        wordparser parse document.doc -o output.md
        wordparser parse document.docx --no-toc --max-heading 3
        wordparser parse document.docx --vision-url http://localhost:1234/v1
    """
    try:
        # 构建多模态配置
        multimodal_config = None
        if vision_url:
            model_config = VisionModelConfig(
                base_url=vision_url,
                model=vision_model or "qwen3.5-9b",
            )
            multimodal_config = MultimodalConfig(
                max_concurrent=max_concurrent,
                model=model_config,
            )

        config = ParserConfig(
            generate_toc=toc,
            max_heading_level=max_heading,
            multimodal=multimodal_config,
            enable_render_fallback=render_fallback,
            libreoffice_path=libreoffice_path,
        )

        parser = WordParser(config)

        if verbose:
            typer.echo(f"正在解析文档: {docx_file}")

        markdown, report = parser.parse_with_report(docx_file)

        # 输出结果
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            if verbose:
                typer.echo(f"✓ 已保存到: {output_path}")
        else:
            typer.echo(markdown)

        # 显示统计信息
        if verbose:
            typer.echo("\n解析统计:")
            typer.echo(f"  标题数: {report.stats.total_headings}")
            typer.echo(f"  段落数: {report.stats.total_paragraphs}")
            typer.echo(f"  表格数: {report.stats.total_tables}")
            typer.echo(f"  图片数: {report.stats.total_images}")

        # 检查错误
        if report.has_errors():
            if verbose:
                typer.echo("\n警告: 解析过程中发生错误", err=True)
                for error in report.errors:
                    typer.echo(f"  - {error.type}: {error.message}", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"错误: {e}", err=True)
        raise typer.Exit(code=1)
```

- [ ] **Step 2: 验证 CLI 帮助**

Run: `python -m wordparser_cli parse --help`

Expected: 显示帮助信息，包含 `--render-fallback` 和 `--libreoffice-path` 选项

- [ ] **Step 3: Commit**

```bash
git add wordparser_cli/main.py
git commit -m "feat: CLI accepts .doc files, adds render-fallback and libreoffice-path options"
```

---

## Task 10: 端到端验证

**Files:**
- 无新文件，验证现有功能

- [ ] **Step 1: 验证基础 .docx 解析仍正常**

Run: `python -c "from wordparser import WordParser; p = WordParser(); print('Parser init OK')"`

Expected: `Parser init OK`

- [ ] **Step 2: 验证 .doc 检测和错误提示**

Run: `python -c "from wordparser import WordParser, ParserConfig; p = WordParser(ParserConfig(libreoffice_path='/nonexistent')); p.parse('test.doc')" 2>&1 || true`

Expected: 提示需要 LibreOffice

- [ ] **Step 3: 验证所有新模块导入**

Run: `python -c "from wordparser.core.chart_extractor import ChartExtractor; from wordparser.core.smartart_extractor import SmartArtExtractor; from wordparser.core.renderer import DocumentRenderer; from wordparser.multimodal.parser import MultimodalParser; print('All imports OK')"`

Expected: `All imports OK`

- [ ] **Step 4: 运行全部测试**

Run: `python -m pytest tests/ -v`

Expected: All passed

- [ ] **Step 5: Final commit（如有格式修正）**

```bash
git add -A
git commit -m "feat: complete LibreOffice + multimodal extension for WordParser"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: 设计文档中 .doc 转换（Task 4+8）、Chart（Task 2+6+8）、SmartArt（Task 3+6+8）、复杂表格（Task 7+8）均有对应任务
- [x] **Placeholder scan**: 无 TBD/TODO，所有步骤包含实际代码
- [x] **Type consistency**: `ChartData`, `SeriesData`, `SmartArtData`, `SmartArtNode` 在 models.py 定义，各模块使用一致；`MultimodalResult` 在 parser.py 中定义并使用
- [x] **Dependency order**: Task 1（基础）→ Task 2-4（提取器，可并行）→ Task 5-6（客户端+解析器）→ Task 7（表格）→ Task 8（集成）→ Task 9（CLI）→ Task 10（验证）
