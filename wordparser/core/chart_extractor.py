"""Chart 数据提取器

从 .docx ZIP 包中提取 Chart XML 和嵌入 Excel，解析为结构化数据。
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Optional

from wordparser.core.models import ChartData, SeriesData

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
        mapping = {
            "barChart": "bar",
            "lineChart": "line",
            "pieChart": "pie",
            "areaChart": "area",
            "scatterChart": "scatter",
        }
        return mapping.get(xml_tag, "unknown")

    def _extract_title(self, xml: str) -> Optional[str]:
        if re.search(r'autoTitleDeleted[^>]*val="1"', xml):
            return None
        title_match = re.search(r'<c:title>.*?<a:t>([^<]+)</a:t>.*?</c:title>', xml, re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        return None

    def _extract_categories(self, xml: str) -> list[str]:
        cat_match = re.search(r'<c:cat>.*?</c:cat>', xml, re.DOTALL)
        if not cat_match:
            return []
        cat_block = cat_match.group(0)
        return re.findall(r'<c:v>([^<]+)</c:v>', cat_block)

    def _extract_series(self, xml: str) -> list[SeriesData]:
        series_list = []
        ser_blocks = re.findall(r'<c:ser>.*?</c:ser>', xml, re.DOTALL)

        for block in ser_blocks:
            name_match = re.search(r'<c:tx>.*?<c:v>([^<]+)</c:v>.*?</c:tx>', block, re.DOTALL)
            name = name_match.group(1).strip() if name_match else f"系列{len(series_list) + 1}"

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
