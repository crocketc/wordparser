"""手动标题启发式检测单元测试"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from collections import Counter

from wordparser.config import ManualHeadingConfig
from wordparser.core.structure import (
    ManualHeadingDetector,
    ManualHeadingCandidate,
    StructureParser,
)
from wordparser.core.models import BlockType


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# ============================================================
# 辅助函数：构造 mock 段落 XML
# ============================================================

def _make_run_element(text: str, bold: bool = False, font_size_half_pt: int | None = None):
    """构造 mock w:r 元素"""
    run = MagicMock()
    run.tag = f"{{{W_NS}}}r"

    t_el = MagicMock()
    t_el.text = text

    rPr = MagicMock()
    sz_el = None
    if font_size_half_pt is not None:
        sz_el = MagicMock()
        sz_el.get.return_value = str(font_size_half_pt)

    rPr.find = lambda tag: {
        f"{{{W_NS}}}b": MagicMock() if bold else None,
        f"{{{W_NS}}}sz": sz_el,
    }.get(tag)
    rPr.__bool__ = lambda self: True

    run.find = lambda tag: {
        f"{{{W_NS}}}t": t_el,
        f"{{{W_NS}}}rPr": rPr,
    }.get(tag)

    return run


def _make_para(text: str, style: str = "Normal", bold: bool = False,
               font_size_half_pt: int | None = None, numPr_val: str | None = None,
               indent_twip: int | None = None):
    """构造 mock 段落对象"""
    para = MagicMock()
    para.text = text

    style_mock = MagicMock()
    style_mock.name = style
    para.style = style_mock

    # 构造 run 子元素
    if text:
        run = _make_run_element(text, bold=bold, font_size_half_pt=font_size_half_pt)
        para._element = MagicMock()
        para._element.__iter__ = lambda self: iter([run])
    else:
        para._element = MagicMock()
        para._element.__iter__ = lambda self: iter([])

    # numPr
    if numPr_val is not None:
        numId_el = MagicMock()
        numId_el.get.return_value = numPr_val
        numPr_el = MagicMock()
        numPr_el.find.return_value = numId_el
        pPr = MagicMock()
        pPr.find.return_value = numPr_el

        def _find(tag):
            if tag == f"{{{W_NS}}}pPr":
                return pPr
            if tag == f"{{{W_NS}}}pPr/{{{W_NS}}}numPr":
                return numPr_el
            return None

        para._element.find = _find
    elif indent_twip is not None:
        pPr = MagicMock()
        ind_el = MagicMock()
        ind_el.get.return_value = str(indent_twip)
        pPr.find = lambda tag: {
            f"{{{W_NS}}}numPr": None,
            f"{{{W_NS}}}ind": ind_el,
        }.get(tag)

        def _find(tag):
            if tag == f"{{{W_NS}}}pPr":
                return pPr
            return None

        para._element.find = _find
    else:
        pPr = MagicMock()
        pPr.find.return_value = None

        def _find(tag):
            if tag == f"{{{W_NS}}}pPr":
                return pPr
            return None

        para._element.find = _find

    return para


# ============================================================
# 测试基准字号校准
# ============================================================

class TestCalibrate:
    def test_calibrate_finds_mode_font_size(self):
        """基准字号应为最常见字号"""
        config = ManualHeadingConfig()
        detector = ManualHeadingDetector(config)

        # 5 个正文段落（10.5pt）+ 1 个大字号段落（14pt）
        paras = [
            _make_para("正文1", font_size_half_pt=21),
            _make_para("正文2", font_size_half_pt=21),
            _make_para("正文3", font_size_half_pt=21),
            _make_para("标题", font_size_half_pt=28),
            _make_para("正文4", font_size_half_pt=21),
            _make_para("正文5", font_size_half_pt=21),
        ]
        detector.calibrate(paras)
        assert detector._base_font_size == 10.5

    def test_calibrate_with_heading_styles_excluded(self):
        """Heading 样式段落不参与基准字号统计"""
        config = ManualHeadingConfig()
        detector = ManualHeadingDetector(config)

        paras = [
            _make_para("正文", font_size_half_pt=21),
            _make_para("样式标题", style="Heading1", font_size_half_pt=28),
            _make_para("正文2", font_size_half_pt=21),
        ]
        detector.calibrate(paras)
        assert detector._base_font_size == 10.5


# ============================================================
# 测试打分信号
# ============================================================

class TestScoringSignals:
    def _make_detector_with_base(self, base_half_pt=21):
        config = ManualHeadingConfig(min_score=3)
        detector = ManualHeadingDetector(config)
        detector._base_font_size = base_half_pt / 2.0
        return detector

    def test_short_text_adds_score(self):
        """短文本（≤80字符）加 1 分"""
        detector = self._make_detector_with_base()
        para = _make_para("短标题文字", font_size_half_pt=21)
        result = detector.detect(para)
        # 仅短文本+无句末标点 = 2 分 < min_score(3)，应返回 None
        assert result is None

    def test_bold_and_short_passes_threshold(self):
        """加粗 + 短文本 + 无句末标点 = 5 分 >= 3"""
        detector = self._make_detector_with_base()
        para = _make_para("加粗短标题", bold=True, font_size_half_pt=21)
        result = detector.detect(para)
        assert result is not None
        assert result.score >= 3

    def test_large_font_adds_score(self):
        """大字号加 2 分"""
        detector = self._make_detector_with_base(21)
        para = _make_para("大字号标题", font_size_half_pt=28)
        result = detector.detect(para)
        assert result is not None

    def test_numbering_pattern_detected(self):
        """编号模式加 2 分"""
        detector = self._make_detector_with_base()
        para = _make_para("1.1 项目背景", font_size_half_pt=21)
        result = detector.detect(para)
        assert result is not None
        assert result.has_numbering is True

    def test_cn_chapter_detected(self):
        """中文章节编号"""
        detector = self._make_detector_with_base()
        para = _make_para("第一章 总则", font_size_half_pt=21)
        result = detector.detect(para)
        assert result is not None
        assert result.number_depth == 1

    def test_cn_paren_detected(self):
        """中文括号编号"""
        detector = self._make_detector_with_base()
        para = _make_para("（一）基本原则", font_size_half_pt=21)
        result = detector.detect(para)
        assert result is not None
        assert result.number_depth == 2

    def test_sentence_end_punctuation_reduces_score(self):
        """句末标点导致少 1 分"""
        detector = self._make_detector_with_base()
        para_with_punc = _make_para("这是一句话。", bold=True, font_size_half_pt=21)
        para_no_punc = _make_para("这是标题文字", bold=True, font_size_half_pt=21)

        result_with = detector.detect(para_with_punc)
        result_without = detector.detect(para_no_punc)

        if result_with and result_without:
            assert result_without.score > result_with.score

    def test_continue_suffix_excluded(self):
        """（续）后缀的段落应被排除"""
        detector = self._make_detector_with_base()
        para = _make_para("标题（续）", bold=True, font_size_half_pt=28)
        result = detector.detect(para)
        assert result is None


# ============================================================
# 测试列表项排除
# ============================================================

class TestListExclusion:
    def test_list_style_excluded(self):
        """List 样式段落不检测"""
        detector = ManualHeadingDetector(ManualHeadingConfig())
        detector._base_font_size = 10.5
        para = _make_para("列表项", style="ListParagraph", bold=True, font_size_half_pt=28)
        result = detector.detect(para)
        assert result is None

    def test_numPr_excluded(self):
        """有 numPr 的段落不检测"""
        detector = ManualHeadingDetector(ManualHeadingConfig())
        detector._base_font_size = 10.5
        para = _make_para("编号列表项", bold=True, font_size_half_pt=28, numPr_val="1")
        result = detector.detect(para)
        assert result is None


# ============================================================
# 测试层级推断
# ============================================================

class TestLevelInference:
    def test_numbering_depth_decimal(self):
        """十进制编号深度推断"""
        detector = ManualHeadingDetector(ManualHeadingConfig())
        c1 = ManualHeadingCandidate(score=5, font_size=14.0, has_numbering=True,
                                     heading_numbering=False,
                                     number_depth=1, indent=0, number_prefix="1.")
        assert detector.resolve_level(c1) == 1

        c2 = ManualHeadingCandidate(score=5, font_size=14.0, has_numbering=True,
                                     heading_numbering=False,
                                     number_depth=2, indent=0, number_prefix="1.1")
        assert detector.resolve_level(c2) == 2

        c3 = ManualHeadingCandidate(score=5, font_size=14.0, has_numbering=True,
                                     heading_numbering=False,
                                     number_depth=3, indent=0, number_prefix="1.1.1")
        assert detector.resolve_level(c3) == 3

    def test_numbering_depth_max_6(self):
        """编号深度上限为 6"""
        detector = ManualHeadingDetector(ManualHeadingConfig())
        c = ManualHeadingCandidate(score=5, font_size=14.0, has_numbering=True,
                                    heading_numbering=False,
                                    number_depth=8, indent=0, number_prefix="1.2.3.4.5.6.7.8")
        assert detector.resolve_level(c) == 6

    def test_font_size_level_map(self):
        """无编号时按字号排序推断层级"""
        detector = ManualHeadingDetector(ManualHeadingConfig())
        detector._base_font_size = 10.5

        candidates = [
            ManualHeadingCandidate(score=5, font_size=18.0, has_numbering=False,
                                   heading_numbering=False,
                                   number_depth=0, indent=0, number_prefix=""),
            ManualHeadingCandidate(score=5, font_size=14.0, has_numbering=False,
                                   heading_numbering=False,
                                   number_depth=0, indent=0, number_prefix=""),
            ManualHeadingCandidate(score=5, font_size=12.0, has_numbering=False,
                                   heading_numbering=False,
                                   number_depth=0, indent=0, number_prefix=""),
        ]
        detector.build_level_map(candidates)

        assert detector.resolve_level(candidates[0]) == 1  # 18pt 最大 → 1级
        assert detector.resolve_level(candidates[1]) == 2  # 14pt → 2级
        assert detector.resolve_level(candidates[2]) == 3  # 12pt → 3级


# ============================================================
# 测试编号检测
# ============================================================

class TestNumberDetection:
    def test_decimal_simple(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("1. 概述")
        assert has is True
        assert depth == 1
        assert is_h is False

    def test_decimal_nested(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("1.2.3 深层标题")
        assert has is True
        assert depth == 3
        assert is_h is False

    def test_cn_chapter(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("第三章 技术方案")
        assert has is True
        assert depth == 1
        assert is_h is True

    def test_cn_numeral(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("一、发行人基本情况")
        assert has is True
        assert depth == 2
        assert is_h is True

    def test_cn_paren(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("（十二）附则")
        assert has is True
        assert depth == 2
        assert is_h is True

    def test_num_paren(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("（3）具体要求")
        assert has is True
        assert depth == 2
        assert is_h is False

    def test_alpha(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("A. 附录说明")
        assert has is True
        assert depth == 2
        assert is_h is False

    def test_no_number(self):
        detector = ManualHeadingDetector(ManualHeadingConfig())
        has, depth, prefix, is_h = detector._detect_numbering("普通文本没有编号")
        assert has is False


# ============================================================
# 测试 StructureParser 集成
# ============================================================

class TestStructureParserIntegration:
    def test_manual_heading_disabled(self):
        """禁用手动标题检测时不产生手动标题"""
        from wordparser.config import ParserConfig
        config = ParserConfig()
        config.manual_heading.enabled = False
        parser = StructureParser(config)

        doc = MagicMock()
        para = _make_para("1.1 项目背景", font_size_half_pt=28)
        doc.paragraphs = [para]

        blocks = parser.parse(doc)
        # 不应检测为标题
        assert not any(b.type == BlockType.HEADING for b in blocks)

    def test_heading_style_not_interfered(self):
        """样式标题不受手动检测影响"""
        parser = StructureParser()
        doc = MagicMock()
        para = _make_para("样式标题", style="Heading1", font_size_half_pt=28)
        doc.paragraphs = [para]

        blocks = parser.parse(doc)
        assert len(blocks) == 1
        assert blocks[0].type == BlockType.HEADING


# ============================================================
# 测试排除模式
# ============================================================

class TestExclusionPatterns:
    """测试已知非标题模式的排除"""

    def _make_detector_with_base(self, base_half_pt=21):
        config = ManualHeadingConfig()
        detector = ManualHeadingDetector(config)
        detector._base_font_size = base_half_pt / 2.0
        return detector

    def test_chart_title_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("图表5-1：发行人设立时的股权结构", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_table_title_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("表8-11发行人2025年1-6月主要财务数据及指标", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_figure_english_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("Figure 1-1: Architecture", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_table_english_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("Table 2-3: Summary", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_unit_label_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("单位：万元、%", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_unit_label_percent_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("单位：%", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_circled_number_footnote_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("①采购商品/接受劳务情况", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_circled_number_multiple_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("⑤发行人面临的主要竞争情况", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_paren_number_list_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("1）办公室", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    def test_paren_number_long_list_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("15）小微担保中心（筹）", bold=True, font_size_half_pt=24)
        assert detector.detect(para) is None

    # 回归：正常标题不受影响

    def test_cn_numeral_heading_not_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("一、发行人基本情况", bold=True, font_size_half_pt=28)
        assert detector.detect(para) is not None

    def test_cn_chapter_heading_not_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("第一章 总则", bold=True, font_size_half_pt=28)
        assert detector.detect(para) is not None

    def test_cn_paren_heading_not_excluded(self):
        detector = self._make_detector_with_base()
        para = _make_para("（一）基本原则", bold=True, font_size_half_pt=28)
        assert detector.detect(para) is not None

    def test_colon_ending_penalty(self):
        """冒号结尾的文本应比无冒号的少 1 分"""
        detector = self._make_detector_with_base()
        para_no_colon = _make_para("发行人基本情况说明", bold=True, font_size_half_pt=28)
        para_with_colon = _make_para("发行人基本情况说明：", bold=True, font_size_half_pt=28)
        result_no = detector.detect(para_no_colon)
        result_with = detector.detect(para_with_colon)
        if result_no and result_with:
            assert result_with.score == result_no.score - 1
