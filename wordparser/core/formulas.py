"""公式处理器（OMML转LaTeX）"""
import re
import xml.etree.ElementTree as ET
from typing import Optional


class FormulaProcessor:
    """公式处理器

    将Office Math Markup Language (OMML)转换为LaTeX格式。
    """

    # OMML命名空间
    NAMESPACE = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}

    def __init__(self):
        """初始化公式处理器"""
        # 注册命名空间
        for prefix, uri in self.NAMESPACE.items():
            ET.register_namespace(prefix, uri)

    def omml_to_latex(self, omml: str) -> str:
        """将OMML公式转换为LaTeX格式

        Args:
            omml: OMML格式的公式字符串

        Returns:
            str: LaTeX格式的公式字符串

        Example:
            >>> processor = FormulaProcessor()
            >>> omml = '<m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f>'
            >>> latex = processor.omml_to_latex(omml)
            >>> print(latex)
            \\frac{1}{2}
        """
        if not omml or not omml.strip():
            return ""

        try:
            # 清理字符串并添加命名空间
            omml_clean = omml.strip()

            # 尝试使用正则表达式解析（更健壮）
            return self._parse_omml_with_regex(omml_clean)

        except Exception:
            # 如果解析失败，返回占位符
            return "*公式解析失败*"

    def _parse_omml_with_regex(self, omml: str) -> str:
        """使用正则表达式解析OMML

        Args:
            omml: OMML字符串

        Returns:
            str: LaTeX字符串
        """
        # 按优先级处理各种元素
        latex = omml

        # 1. 处理分数 <m:f>
        latex = self._convert_fraction(latex)

        # 2. 处理上标 <m:sSup>
        latex = self._convert_superscript(latex)

        # 3. 处理下标 <m:sSub>
        latex = self._convert_subscript(latex)

        # 4. 处理根号 <m:rad>
        latex = self._convert_radical(latex)

        # 5. 处理分隔符 <m:d>
        latex = self._convert_delimiter(latex)

        # 清理剩余标签
        latex = self._cleanup_tags(latex)

        return latex

    def _convert_fraction(self, omml: str) -> str:
        """转换分数

        <m:f>
            <m:num>分子</m:num>
            <m:den>分母</m:den>
        </m:f>
        -> \\frac{分子}{分母}
        """
        pattern = r'<m:f[^>]*>.*?<m:num[^>]*>(.*?)</m:num>.*?<m:den[^>]*>(.*?)</m:den>.*?</m:f>'

        def replace_fraction(match):
            numerator = self._extract_text(match.group(1))
            denominator = self._extract_text(match.group(2))
            return f"\\frac{{{numerator}}}{{{denominator}}}"

        return re.sub(pattern, replace_fraction, omml, flags=re.DOTALL)

    def _convert_superscript(self, omml: str) -> str:
        """转换上标

        <m:sSup>
            <m:e>底数</m:e>
            <m:sup>指数</m:sup>
        </m:sSup>
        -> 底数^{指数}
        """
        pattern = r'<m:sSup[^>]*>.*?<m:e[^>]*>(.*?)</m:e>.*?<m:sup[^>]*>(.*?)</m:sup>.*?</m:sSup>'

        def replace_superscript(match):
            base = self._extract_text(match.group(1))
            exp = self._extract_text(match.group(2))
            return f"{{{base}}}^{{{exp}}}"

        return re.sub(pattern, replace_superscript, omml, flags=re.DOTALL)

    def _convert_subscript(self, omml: str) -> str:
        """转换下标

        <m:sSub>
            <m:e>底数</m:e>
            <m:sub>下标</m:sub>
        </m:sSub>
        -> 底数_{下标}
        """
        pattern = r'<m:sSub[^>]*>.*?<m:e[^>]*>(.*?)</m:e>.*?<m:sub[^>]*>(.*?)</m:sub>.*?</m:sSub>'

        def replace_subscript(match):
            base = self._extract_text(match.group(1))
            sub = self._extract_text(match.group(2))
            return f"{{{base}}}_{{{sub}}}"

        return re.sub(pattern, replace_subscript, omml, flags=re.DOTALL)

    def _convert_radical(self, omml: str) -> str:
        """转换根号

        <m:rad>
            <m:deg>次数</m:deg>  (可选)
            <m:e>被开方数</m:e>
        </m:rad>
        -> \\sqrt[次数]{被开方数} 或 \\sqrt{被开方数}
        """
        # 带次数的根号
        pattern_with_deg = r'<m:rad[^>]*>.*?<m:deg[^>]*>(.*?)</m:deg>.*?<m:e[^>]*>(.*?)</m:e>.*?</m:rad>'

        def replace_radical_with_deg(match):
            deg = self._extract_text(match.group(1))
            e = self._extract_text(match.group(2))
            return f"\\sqrt[{deg}]{{{e}}}"

        omml = re.sub(pattern_with_deg, replace_radical_with_deg, omml, flags=re.DOTALL)

        # 不带次数的根号
        pattern_without_deg = r'<m:rad[^>]*>.*?<m:e[^>]*>(.*?)</m:e>.*?</m:rad>'

        def replace_radical_without_deg(match):
            e = self._extract_text(match.group(1))
            return f"\\sqrt{{{e}}}"

        return re.sub(pattern_without_deg, replace_radical_without_deg, omml, flags=re.DOTALL)

    def _convert_delimiter(self, omml: str) -> str:
        """转换分隔符（括号）

        <m:d>
            <m:dPr>
                <m:begChr>(</m:begChr>
                <m:endChr>)</m:endChr>
            </m:dPr>
            <m:e>内容</m:e>
        </m:d>
        -> \\left(内容\\right)
        """
        pattern = r'<m:d[^>]*>.*?<m:e[^>]*>(.*?)</m:e>.*?</m:d>'

        def replace_delimiter(match):
            block = match.group(0)
            # 在当前 <m:d> 块内搜索 begChr/endChr
            beg_chr_match = re.search(r'<m:begChr[^>]*>([^<]+)</m:begChr>', block)
            beg_chr = beg_chr_match.group(1) if beg_chr_match else '('

            end_chr_match = re.search(r'<m:endChr[^>]*>([^<]+)</m:endChr>', block)
            end_chr = end_chr_match.group(1) if end_chr_match else ')'

            content = self._extract_text(match.group(1))
            return f"\\left{beg_chr}{content}\\right{end_chr}"

        return re.sub(pattern, replace_delimiter, omml, flags=re.DOTALL)

    def _extract_text(self, xml: str) -> str:
        """从XML片段中提取文本内容

        Args:
            xml: XML片段

        Returns:
            str: 提取的文本
        """
        # 提取所有 <m:t> 标签中的文本
        texts = re.findall(r'<m:t[^>]*>([^<]+)</m:t>', xml)
        result = ''.join(texts)
        return result.strip()

    def _cleanup_tags(self, xml: str) -> str:
        """清理剩余的XML标签

        Args:
            xml: 包含标签的字符串

        Returns:
            str: 清理后的文本
        """
        # 移除所有剩余的XML标签
        clean = re.sub(r'<[^>]+>', '', xml)
        return clean.strip()

    def wrap_formula(
        self,
        latex: str,
        inline: bool = True,
        delimiter: Optional[str] = None
    ) -> str:
        """包装LaTeX公式

        Args:
            latex: LaTeX公式字符串
            inline: 是否为内联公式，默认True
            delimiter: 自定义分隔符，默认None（使用$或$$）

        Returns:
            str: 包装后的公式字符串

        Example:
            >>> processor = FormulaProcessor()
            >>> wrapped = processor.wrap_formula("x^2", inline=True)
            >>> print(wrapped)
            $x^2$
        """
        if delimiter:
            return f"{delimiter}{latex}{delimiter}"

        if inline:
            return f"${latex}$"
        else:
            return f"$${latex}$$"

    def convert_omml_text_runs(self, omml_runs: list) -> str:
        """转换多个OMML文本运行

        Args:
            omml_runs: OMML文本运行列表

        Returns:
            str: LaTeX字符串
        """
        latex_parts = []

        for run in omml_runs:
            if isinstance(run, str):
                latex_parts.append(self.omml_to_latex(run))
            else:
                # 假设是字典或其他格式
                omml_str = str(run)
                latex_parts.append(self.omml_to_latex(omml_str))

        return ''.join(latex_parts)
