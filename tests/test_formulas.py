"""测试公式处理器"""
import pytest
from wordparser.core.formulas import FormulaProcessor


class TestFormulaProcessor:
    """测试公式处理器"""

    def test_init(self):
        """测试初始化"""
        processor = FormulaProcessor()
        assert processor is not None

    def test_omml_to_latex_simple_fraction(self):
        """测试简单分数转换"""
        processor = FormulaProcessor()

        omml = """
        <m:f>
            <m:num>
                <m:r><m:t>1</m:t></m:r>
            </m:num>
            <m:den>
                <m:r><m:t>2</m:t></m:r>
            </m:den>
        </m:f>
        """

        latex = processor.omml_to_latex(omml)
        assert "\\frac" in latex
        assert "1" in latex
        assert "2" in latex

    def test_omml_to_latex_superscript(self):
        """测试上标转换"""
        processor = FormulaProcessor()

        omml = """
        <m:sSup>
            <m:e>
                <m:r><m:t>x</m:t></m:r>
            </m:e>
            <m:sup>
                <m:r><m:t>2</m:t></m:r>
            </m:sup>
        </m:sSup>
        """

        latex = processor.omml_to_latex(omml)
        assert "^" in latex or "^{2}" in latex
        assert "x" in latex

    def test_omml_to_latex_subscript(self):
        """测试下标转换"""
        processor = FormulaProcessor()

        omml = """
        <m:sSub>
            <m:e>
                <m:r><m:t>x</m:t></m:r>
            </m:e>
            <m:sub>
                <m:r><m:t>1</m:t></m:r>
            </m:sub>
        </m:sSub>
        """

        latex = processor.omml_to_latex(omml)
        assert "_" in latex or "_{1}" in latex
        assert "x" in latex

    def test_omml_to_latex_radical(self):
        """测试根号转换"""
        processor = FormulaProcessor()

        omml = """
        <m:rad>
            <m:deg>
                <m:r><m:t>3</m:t></m:r>
            </m:deg>
            <m:e>
                <m:r><m:t>x</m:t></m:r>
            </m:e>
        </m:rad>
        """

        latex = processor.omml_to_latex(omml)
        assert "\\sqrt" in latex

    def test_omml_to_latex_delimiter(self):
        """测试分隔符（括号）转换"""
        processor = FormulaProcessor()

        omml = """
        <m:d>
            <m:dPr>
                <m:begChr>(</m:begChr>
                <m:endChr>)</m:endChr>
            </m:dPr>
            <m:e>
                <m:r><m:t>x + y</m:t></m:r>
            </m:e>
        </m:d>
        """

        latex = processor.omml_to_latex(omml)
        assert "(" in latex or "\\left(" in latex
        assert ")" in latex or "\\right)" in latex

    def test_wrap_formula_inline(self):
        """测试内联公式包装"""
        processor = FormulaProcessor()

        latex = processor.wrap_formula("x^2 + y^2", inline=True)
        assert latex.startswith("$")
        assert latex.endswith("$")

    def test_wrap_formula_display(self):
        """测试块级公式包装"""
        processor = FormulaProcessor()

        latex = processor.wrap_formula("x^2 + y^2", inline=False)
        assert latex.startswith("$$")
        assert latex.endswith("$$")

    def test_wrap_formula_custom_delimiter(self):
        """测试自定义分隔符"""
        processor = FormulaProcessor()

        # 使用配对分隔符字典（实际应用中会这样处理）
        # 这里测试使用简单的相同分隔符
        latex = processor.wrap_formula("x^2", inline=True, delimiter="\\(")
        # 当使用单个分隔符参数时，前后会使用相同的分隔符
        assert "\\(x^2\\(" in latex  # 当前后使用相同时

        # 测试使用$$作为自定义分隔符
        latex2 = processor.wrap_formula("x^2", inline=True, delimiter="$$")
        assert latex2 == "$$x^2$$"

    def test_omml_to_latex_complex(self):
        """测试复杂公式转换"""
        processor = FormulaProcessor()

        omml = """
        <m:f>
            <m:num>
                <m:r><m:t>x + y</m:t></m:r>
            </m:num>
            <m:den>
                <m:r><m:t>2</m:t></m:r>
            </m:den>
        </m:f>
        """

        latex = processor.omml_to_latex(omml)
        assert "\\frac" in latex
        assert "x + y" in latex or "x+y" in latex

    def test_omml_to_latex_empty(self):
        """测试空公式"""
        processor = FormulaProcessor()

        latex = processor.omml_to_latex("")
        assert latex == ""
