from __future__ import annotations

import re
from docx.document import Document

from wordparser.core.models import BlockType, ContentBlock, TitleNode
from wordparser.config import ParserConfig

_HEADING_NUMBER_RE = re.compile(
    r"^(\d+(\.\d+)*[\.\s、])+[\s]*"
)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


class StructureParser:
    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()
        self._title_tree: list[TitleNode] = []
        self._doc_part = None  # 延迟设置，用于解析超链接

    def set_doc_part(self, doc_part) -> None:
        self._doc_part = doc_part

    def parse(self, doc: Document) -> list[ContentBlock]:
        blocks = []
        for para in doc.paragraphs:
            style_name = para.style.name if para.style else ""

            if style_name.startswith("Heading"):
                block = self._parse_heading(para, style_name)
                blocks.append(block)
            else:
                block = self._parse_paragraph(para)
                if block:
                    blocks.append(block)

        return blocks

    def get_title_tree(self) -> list[TitleNode]:
        return self._title_tree

    def _parse_heading(self, para, style_name: str) -> ContentBlock:
        level = self._extract_heading_level(style_name)
        text = para.text.strip()
        text = self._strip_heading_number(text)
        anchor = self._generate_anchor(text)

        node = TitleNode(level=level, text=text, anchor=anchor)
        self._add_to_title_tree(node)

        return ContentBlock(
            type=BlockType.HEADING,
            content=node,
            metadata={"_para_element": para._element},
        )

    def _extract_heading_level(self, style_name: str) -> int:
        match = re.search(r"\d+", style_name)
        level = int(match.group()) if match else 1
        return min(level, self.config.max_heading_level)

    def _strip_heading_number(self, text: str) -> str:
        return _HEADING_NUMBER_RE.sub("", text).strip()

    def _generate_anchor(self, text: str) -> str:
        return re.sub(r"[^\w一-鿿]+", "", text)

    def _add_to_title_tree(self, node: TitleNode) -> None:
        self._insert_into_tree(self._title_tree, node)

    def _insert_into_tree(self, siblings: list[TitleNode], node: TitleNode) -> None:
        if not siblings:
            siblings.append(node)
            return

        last = siblings[-1]
        if node.level > last.level:
            self._insert_into_tree(last.children, node)
        else:
            siblings.append(node)

    def _parse_paragraph(self, para) -> ContentBlock | None:
        text = self._extract_formatted_text(para)
        if not text:
            return None

        style_name = para.style.name if para.style else ""
        meta = {"_para_element": para._element}

        # 优先检测 numPr（XML 级别的编号）
        numPr = para._element.find(f"{{{W_NS}}}pPr/{{{W_NS}}}numPr")
        if numPr is not None:
            numId_el = numPr.find(f"{{{W_NS}}}numId")
            if numId_el is not None and numId_el.get(f"{{{W_NS}}}val", "0") != "0":
                ilvl_el = numPr.find(f"{{{W_NS}}}ilvl")
                ilvl = int(ilvl_el.get(f"{{{W_NS}}}val", "0")) if ilvl_el is not None else 0
                meta["level"] = ilvl
                return ContentBlock(type=BlockType.LIST, content=text, metadata=meta)

        if style_name.startswith("List"):
            return ContentBlock(type=BlockType.LIST, content=text, metadata=meta)

        return ContentBlock(type=BlockType.PARAGRAPH, content=text, metadata=meta)

    def _extract_formatted_text(self, para) -> str:
        """从段落中提取带格式的 Markdown 文本。

        遍历 paragraph 的 XML 子元素（w:r, w:hyperlink, m:oMath 等），
        按文档顺序生成 Markdown 格式文本。
        """
        parts: list[str] = []

        for child in para._element:
            tag = child.tag

            # 普通文本 run
            if tag == f"{{{W_NS}}}r":
                parts.append(self._format_run(child))

            # 超链接
            elif tag == f"{{{W_NS}}}hyperlink":
                parts.append(self._format_hyperlink(child))

            # 行内公式
            elif tag == f"{{{M_NS}}}oMath":
                parts.append(self._format_formula(child, inline=True))

            # 独立段落公式
            elif tag == f"{{{M_NS}}}oMathPara":
                parts.append(self._format_formula_block(child))

        text = "".join(parts).strip()
        return text

    def _format_run(self, run_element) -> str:
        """格式化单个 w:r 元素为 Markdown"""
        rPr = run_element.find(f"{{{W_NS}}}rPr")

        # 提取文本
        t_el = run_element.find(f"{{{W_NS}}}t")
        if t_el is None or t_el.text is None:
            return ""
        text = t_el.text

        if not text:
            return ""

        bold = False
        italic = False
        strike = False

        if rPr is not None:
            bold = rPr.find(f"{{{W_NS}}}b") is not None
            italic = rPr.find(f"{{{W_NS}}}i") is not None
            strike = rPr.find(f"{{{W_NS}}}strike") is not None

        # 应用格式（嵌套顺序：~~ > ** > *）
        if strike:
            text = f"~~{text}~~"
        if bold and italic:
            text = f"***{text}***"
        elif bold:
            text = f"**{text}**"
        elif italic:
            text = f"*{text}*"

        return text

    def _format_hyperlink(self, hyperlink_element) -> str:
        """格式化 w:hyperlink 元素为 Markdown 链接"""
        r_id = hyperlink_element.get(f"{{{R_NS}}}id")
        url = ""

        if r_id and self._doc_part:
            try:
                rel = self._doc_part.rels[r_id]
                url = rel.target_ref
            except (KeyError, AttributeError):
                pass

        # 提取链接文本
        texts = []
        for t_el in hyperlink_element.iter(f"{{{W_NS}}}t"):
            if t_el.text:
                texts.append(t_el.text)
        link_text = "".join(texts)

        if url and link_text:
            return f"[{link_text}]({url})"
        return link_text

    def _format_formula(self, omath_element, inline: bool = True) -> str:
        """格式化 m:oMath 元素为 LaTeX 公式"""
        from wordparser.core.formulas import FormulaProcessor

        omml_str = _element_to_string(omath_element)
        latex = FormulaProcessor().omml_to_latex(omml_str)

        if inline:
            return f"${latex}$"
        return f"$${latex}$$"

    def _format_formula_block(self, omath_para_element) -> str:
        """格式化 m:oMathPara 元素（独立段落公式）"""
        omath = omath_para_element.find(f"{{{M_NS}}}oMath")
        if omath is not None:
            return self._format_formula(omath, inline=False)
        return ""


def _element_to_string(element) -> str:
    """将 lxml 元素转为字符串（用于 OMML 解析）"""
    from lxml import etree
    return etree.tostring(element, encoding="unicode")
