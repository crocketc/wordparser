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

    def test_chart_type_detection(self):
        assert self.extractor._detect_chart_type("<c:barChart/>") == "bar"
        assert self.extractor._detect_chart_type("<c:lineChart/>") == "line"
        assert self.extractor._detect_chart_type("<c:pieChart/>") == "pie"
        assert self.extractor._detect_chart_type("<c:areaChart/>") == "area"
        assert self.extractor._detect_chart_type("<c:scatterChart/>") == "scatter"
        assert self.extractor._detect_chart_type("<c:unknownElement/>") == "unknown"
