"""SmartArtExtractor 测试"""
import pytest
from wordparser.core.smartart_extractor import SmartArtExtractor


SMARTART_DATA_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<dgm:dataModel xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <dgm:ptLst>
    <dgm:pt modelId="0" type="doc">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="1">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>根节点</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="2">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>子节点A</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="3">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>子节点B</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="4">
      <dgm:prSet/><dgm:spPr/>
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
