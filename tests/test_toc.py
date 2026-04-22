"""测试目录生成器"""
import pytest
from dataclasses import dataclass
from wordparser.core.toc import TOCGenerator


@dataclass
class Heading:
    """标题数据类（用于测试）"""
    level: int
    text: str
    number: str = ""


class TestTOCGenerator:
    """测试目录生成器"""

    def test_init(self):
        """测试初始化"""
        generator = TOCGenerator()
        assert generator is not None

    def test_generate_empty_list(self):
        """测试生成空目录"""
        generator = TOCGenerator()
        toc = generator.generate([])

        assert toc == ""

    def test_generate_single_level(self):
        """测试生成单级目录"""
        generator = TOCGenerator()

        headings = [
            Heading(level=1, text="第一章", number="1"),
            Heading(level=1, text="第二章", number="2"),
        ]

        toc = generator.generate(headings)

        assert "1. 第一章" in toc
        assert "2. 第二章" in toc
        assert toc.count("\n") == 1

    def test_generate_multiple_levels(self):
        """测试生成多级目录"""
        generator = TOCGenerator()

        headings = [
            Heading(level=1, text="第一章", number="1"),
            Heading(level=2, text="第一节", number="1.1"),
            Heading(level=3, text="小节", number="1.1.1"),
            Heading(level=1, text="第二章", number="2"),
        ]

        toc = generator.generate(headings)

        lines = toc.strip().split("\n")
        assert len(lines) == 4
        # 验证缩进
        assert not lines[0].startswith(" ")  # 一级标题无缩进
        assert lines[1].startswith("  ")  # 二级标题缩进
        assert lines[2].startswith("    ")  # 三级标题缩进

    def test_generate_with_numbering(self):
        """测试生成带编号的目录"""
        generator = TOCGenerator()

        headings = [
            Heading(level=1, text="前言", number=""),
            Heading(level=1, text="第一章", number="1"),
            Heading(level=2, text="概述", number="1.1"),
        ]

        toc = generator.generate(headings)

        # 前言无编号，只有项目符号
        lines = toc.strip().split("\n")
        assert "前言" in lines[0]
        assert lines[0].startswith("- 前言")  # 无编号时只有项目符号

    def test_generate_max_depth(self):
        """测试限制最大深度"""
        generator = TOCGenerator()

        headings = [
            Heading(level=1, text="第一章", number="1"),
            Heading(level=2, text="第一节", number="1.1"),
            Heading(level=3, text="小节", number="1.1.1"),
            Heading(level=4, text="小小节", number="1.1.1.1"),
        ]

        toc = generator.generate(headings, max_depth=3)

        # 不应包含四级标题
        assert "1.1.1.1" not in toc
        assert "小小节" not in toc

    def test_generate_custom_indent(self):
        """测试自定义缩进"""
        generator = TOCGenerator()

        headings = [
            Heading(level=1, text="第一章", number="1"),
            Heading(level=2, text="第一节", number="1.1"),
        ]

        toc = generator.generate(headings, indent_size=4)

        lines = toc.strip().split("\n")
        assert lines[1].startswith("    ")  # 4个空格缩进

    def test_generate_with_anchors(self):
        """测试生成带锚点的目录"""
        generator = TOCGenerator()

        headings = [
            Heading(level=1, text="第一章", number="1"),
            Heading(level=2, text="第一节", number="1.1"),
        ]

        toc = generator.generate(headings, add_anchors=True)

        # 验证锚点格式 - 包含链接格式
        assert "[1. 第一章](#第一章)" in toc
        assert "[1.1. 第一节](#第一节)" in toc

    def test_generate_skip_levels(self):
        """测试跳级标题"""
        generator = TOCGenerator()

        headings = [
            Heading(level=1, text="第一章", number="1"),
            Heading(level=3, text="直接三级", number="1.0.1"),  # 跳过二级
        ]

        toc = generator.generate(headings)

        lines = toc.strip().split("\n")
        assert len(lines) == 2

