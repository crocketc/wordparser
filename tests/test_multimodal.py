"""测试多模态解析器"""
import pytest
from dataclasses import dataclass
from typing import Optional, List
from wordparser.multimodal.parser import MultimodalParser, MultimodalResult
from wordparser.multimodal.parallel import ParallelMultimodalProcessor


class TestMultimodalResult:
    """测试MultimodalResult数据类"""

    def test_create_result(self):
        """测试创建结果对象"""
        result = MultimodalResult(
            content="测试内容",
            confidence=0.95,
            metadata={"type": "table"}
        )
        assert result.content == "测试内容"
        assert result.confidence == 0.95
        assert result.metadata == {"type": "table"}


class TestMultimodalParser:
    """测试多模态解析器"""

    def test_init(self):
        """测试初始化"""
        parser = MultimodalParser()
        assert parser is not None

    def test_parse_table(self):
        """测试解析表格"""
        parser = MultimodalParser()
        table_xml = """
        <w:tbl>
            <w:tr>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Header 1</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Header 2</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
            </w:tr>
            <w:tr>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Data 1</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
                <w:tc>
                    <w:p>
                        <w:r>
                            <w:t>Data 2</w:t>
                        </w:r>
                    </w:p>
                </w:tc>
            </w:tr>
        </w:tbl>
        """

        result = parser.parse_table(table_xml)
        assert isinstance(result, MultimodalResult)
        assert "Header 1" in result.content
        assert "Header 2" in result.content
        assert "Data 1" in result.content
        assert result.metadata["type"] == "table"

    def test_parse_image(self):
        """测试解析图片"""
        parser = MultimodalParser()
        image_data = {
            "format": "png",
            "width": 800,
            "height": 600,
            "data": b"fake_image_data"
        }

        result = parser.parse_image(image_data)
        assert isinstance(result, MultimodalResult)
        assert "image" in result.metadata["type"]
        assert result.metadata["format"] == "png"
        assert result.metadata["width"] == 800
        assert result.metadata["height"] == 600

    def test_parse_chart(self):
        """测试解析图表"""
        parser = MultimodalParser()
        chart_xml = """
        <c:chart>
            <c:title>
                <c:tx>
                    <c:v>测试图表</c:v>
                </c:tx>
            </c:title>
        </c:chart>
        """

        result = parser.parse_chart(chart_xml)
        assert isinstance(result, MultimodalResult)
        assert "chart" in result.metadata["type"]

    def test_parse_smartart(self):
        """测试解析SmartArt"""
        parser = MultimodalParser()
        smartart_data = {
            "type": "hierarchy",
            "nodes": [
                {"text": "根节点", "level": 0},
                {"text": "子节点1", "level": 1},
                {"text": "子节点2", "level": 1}
            ]
        }

        result = parser.parse_smartart(smartart_data)
        assert isinstance(result, MultimodalResult)
        assert "smartart" in result.metadata["type"]
        assert result.metadata["layout"] == "hierarchy"
        assert "根节点" in result.content


class TestParallelMultimodalProcessor:
    """测试并行多模态处理器"""

    def test_init(self):
        """测试初始化"""
        processor = ParallelMultimodalProcessor()
        assert processor.max_workers == 4
        assert processor.parser is not None

    def test_init_custom_workers(self):
        """测试自定义线程数"""
        processor = ParallelMultimodalProcessor(max_workers=8)
        assert processor.max_workers == 8

    def test_process_batch_mixed_types(self):
        """测试批量处理混合类型"""
        processor = ParallelMultimodalProcessor(max_workers=2)

        items = [
            {
                'type': 'table',
                'data': '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>单元格1</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
            },
            {
                'type': 'image',
                'data': {'format': 'png', 'width': 100, 'height': 100, 'data': b'test'}
            },
            {
                'type': 'chart',
                'data': '<c:chart><c:title><c:tx><c:v>测试图</c:v></c:tx></c:title></c:chart>'
            },
            {
                'type': 'smartart',
                'data': {
                    'type': 'hierarchy',
                    'nodes': [{'text': '节点1', 'level': 0}]
                }
            }
        ]

        results = processor.process_batch(items)

        assert len(results) == 4
        assert all(isinstance(r, MultimodalResult) for r in results)
        assert results[0].metadata['type'] == 'table'
        assert results[1].metadata['type'] == 'image'
        assert results[2].metadata['type'] == 'chart'
        assert results[3].metadata['type'] == 'smartart'

    def test_process_batch_unknown_type(self):
        """测试处理未知类型"""
        processor = ParallelMultimodalProcessor()

        items = [
            {'type': 'unknown', 'data': 'some data'}
        ]

        results = processor.process_batch(items)

        assert len(results) == 1
        assert results[0].confidence == 0.0
        assert '未知类型' in results[0].content

    def test_process_batch_empty_list(self):
        """测试处理空列表"""
        processor = ParallelMultimodalProcessor()

        results = processor.process_batch([])

        assert len(results) == 0

    def test_process_batch_preserves_order(self):
        """测试保持顺序"""
        processor = ParallelMultimodalProcessor(max_workers=4)

        items = [
            {'type': 'table', 'data': '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>A</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'},
            {'type': 'table', 'data': '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>B</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'},
            {'type': 'table', 'data': '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>C</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'},
        ]

        results = processor.process_batch(items)

        # 验证顺序
        assert 'A' in results[0].content
        assert 'B' in results[1].content
        assert 'C' in results[2].content

    def test_process_batch_with_callback(self):
        """测试带回调函数的批量处理"""
        processor = ParallelMultimodalProcessor()

        callback_results = []

        def callback(index, result):
            callback_results.append((index, result.metadata['type']))

        items = [
            {'type': 'table', 'data': '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>测试</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'}
        ]

        results = processor.process_batch_with_callback(items, callback)

        assert len(results) == 1
        assert len(callback_results) == 1
        assert callback_results[0][1] == 'table'

