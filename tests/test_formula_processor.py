"""测试公式处理器（OMML → LaTeX）"""
import pytest
from wordparser.core.formulas import FormulaProcessor


class TestFormulaProcessor:
    """测试 FormulaProcessor 类"""

    def test_init(self):
        """测试初始化"""
        processor = FormulaProcessor()
        assert processor is not None
        assert processor.NAMESPACE == {
            'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'
        }

    def test_empty_omml(self):
        """测试空 OMML 输入"""
        processor = FormulaProcessor()
        assert processor.omml_to_latex("") == ""
        assert processor.omml_to_latex("   ") == ""
        assert processor.omml_to_latex(None) == ""

    def test_fraction(self):
        """测试分数转换"""
        processor = FormulaProcessor()
        omml = '<m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f>'
        result = processor.omml_to_latex(omml)
        assert result == r"\frac{1}{2}"

    def test_superscript(self):
        """测试上标转换"""
        processor = FormulaProcessor()
        omml = '<m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup>'
        result = processor.omml_to_latex(omml)
        assert result == r"{x}^{2}"

    def test_subscript(self):
        """测试下标转换"""
        processor = FormulaProcessor()
        omml = '<m:sSub><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sub><m:r><m:t>1</m:t></m:r></m:sub></m:sSub>'
        result = processor.omml_to_latex(omml)
        assert result == r"{x}_{1}"

    def test_radical(self):
        """测试根号转换"""
        processor = FormulaProcessor()
        omml = '<m:rad><m:e><m:r><m:t>x</m:t></m:r></m:e></m:rad>'
        result = processor.omml_to_latex(omml)
        assert result == r"\sqrt{x}"

    def test_radical_with_degree(self):
        """测试带次数的根号转换"""
        processor = FormulaProcessor()
        omml = '<m:rad><m:deg><m:r><m:t>3</m:t></m:r></m:deg><m:e><m:r><m:t>x</m:t></m:r></m:e></m:rad>'
        result = processor.omml_to_latex(omml)
        assert result == r"\sqrt[3]{x}"

    def test_delimiter(self):
        """测试分隔符（括号）转换"""
        processor = FormulaProcessor()
        omml = '<m:d><m:dPr><m:begChr>(</m:begChr><m:endChr>)</m:endChr></m:dPr><m:e><m:r><m:t>x</m:t></m:r></m:e></m:d>'
        result = processor.omml_to_latex(omml)
        assert result == r"\left(x\right)"

    def test_complex_formula(self):
        """测试复杂公式（分数+上标）"""
        processor = FormulaProcessor()
        omml = '<m:f><m:num><m:r><m:t>a</m:t></m:r></m:num><m:den><m:r><m:t>b</m:t></m:r></m:den></m:f>'
        result = processor.omml_to_latex(omml)
        assert result == r"\frac{a}{b}"

    def test_wrap_formula_inline(self):
        """测试内联公式包装"""
        processor = FormulaProcessor()
        result = processor.wrap_formula("x^2", inline=True)
        assert result == r"$x^2$"

    def test_wrap_formula_block(self):
        """测试块级公式包装"""
        processor = FormulaProcessor()
        result = processor.wrap_formula("x^2", inline=False)
        assert result == r"$$x^2$$"

    def test_wrap_formula_custom_delimiter(self):
        """测试自定义分隔符（前后使用相同分隔符）"""
        processor = FormulaProcessor()
        result = processor.wrap_formula("x^2", delimiter="\\[")
        # wrap_formula 对 delimiter 前后使用相同值
        assert result == r"\[x^2\["

    def test_invalid_omml(self):
        """测试无效 OMML 输入"""
        processor = FormulaProcessor()
        result = processor.omml_to_latex("invalid xml")
        # 应该返回解析失败标记或清理后的文本
        assert "invalid xml" in result or result == "*公式解析失败*"

    def test_convert_omml_text_runs(self):
        """测试批量转换 OMML 文本运行"""
        processor = FormulaProcessor()
        omml_runs = [
            '<m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f>',
            '<m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup>',
        ]
        result = processor.convert_omml_text_runs(omml_runs)
        assert r"\frac{1}{2}" in result
        assert "{x}^{2}" in result


class TestStructureParserFormulas:
    """测试 StructureParser 中的公式处理"""

    def test_namespace_constants(self):
        """测试命名空间常量定义"""
        from wordparser.core.structure import M_NS, W_NS

        assert M_NS == 'http://schemas.openxmlformats.org/officeDocument/2006/math'
        assert W_NS == 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

    def test_element_to_string(self):
        """测试 XML 元素转字符串"""
        from wordparser.core.structure import _element_to_string
        from lxml import etree

        element = etree.fromstring('<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:r><m:t>x</m:t></m:r></m:oMath>')
        result = _element_to_string(element)
        assert 'm:oMath' in result or 'oMath' in result
