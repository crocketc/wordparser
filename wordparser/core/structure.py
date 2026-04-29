from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from docx.document import Document

from wordparser.core.models import BlockType, ContentBlock, TitleNode
from wordparser.config import ParserConfig
from wordparser.core.formulas import FormulaProcessor

_HEADING_NUMBER_RE = re.compile(
    r"^(\d+(\.\d+)*[\.\s、])+[\s]*"
)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

# 编号模式正则
# heading=True 表示该模式通常用于标题编号，heading=False 通常用于列表项
_NUMBER_PATTERNS = [
    (re.compile(r"^(\d+)((?:\.\d+)*)([\.\s、])"), "decimal", False),
    (re.compile(r"^第([一二三四五六七八九十百]+)([章部篇节])"), "cn_chapter", True),
    (re.compile(r"^([一二三四五六七八九十百]+)[、\s]"), "cn_numeral", True),
    (re.compile(r"^[（(]([一二三四五六七八九十]+)[）)]"), "cn_paren", True),
    (re.compile(r"^[（(](\d+)[）)]"), "num_paren", False),
    (re.compile(r"^([A-Za-z])([\.\s、])"), "alpha", False),
]

# 中文标题样式关键词（非 Heading 样式但实际为标题的样式名）
_CN_HEADING_STYLE_KEYWORDS = ("标题", "Title", "heading")

_SENTENCE_END_RE = re.compile(r"[。！？；]")
_CONTINUE_RE = re.compile(r"[（(][续續][）)]\s*$")

# 排除模式：已知非标题模式（图表标题、单位标注、带圈数字脚注等）
_EXCLUDE_PATTERNS = [
    re.compile(r"^(图|表|图表|Figure|Table)\s*[\d\-\.]+[：:\s\-]"),
    re.compile(r"^单位[：:]\s*"),
    re.compile(r"^[①-⑳㉈-㉏]"),
    re.compile(r"^\d+[）)]\s*\S+$"),
]


@dataclass
class ManualHeadingCandidate:
    score: int
    font_size: float
    has_numbering: bool
    heading_numbering: bool  # 编号模式是否为标题型（非列表型）
    number_depth: int
    indent: float
    number_prefix: str


class ManualHeadingDetector:
    """启发式手动标题检测器

    通过字号、加粗、编号模式等多维信号打分，
    从非 Heading 样式段落中识别手动标题并推断层级。
    """

    def __init__(self, config) -> None:
        self.config = config
        self._base_font_size: float | None = None
        self._font_size_level_map: dict[float, int] = {}

    def calibrate(self, paragraphs) -> None:
        """统计正文基准字号（众数）"""
        sizes: list[float] = []
        for para in paragraphs:
            style_name = para.style.name if para.style else ""
            if style_name.startswith("Heading"):
                continue
            # 排除中式标题样式
            if StructureParser._is_cn_heading_style(style_name):
                continue
            sz = self._get_dominant_font_size(para)
            if sz is not None:
                sizes.append(sz)

        if sizes:
            counter = Counter(sizes)
            self._base_font_size = counter.most_common(1)[0][0]

    def detect(self, para) -> ManualHeadingCandidate | None:
        """对段落打分，返回候选信息或 None"""
        text = para.text.strip()
        if not text:
            return None

        # 排除：续行标题
        if _CONTINUE_RE.search(text):
            return None

        # 排除：列表项（numPr 或 List 样式）
        if self._is_list_item(para):
            return None

        # 排除：已知非标题模式（图表标题、单位标注、脚注等）
        if self._is_known_non_heading(text):
            return None

        # 硬性限制：超过 max_length 的文本不应该是标题
        if len(text) > self.config.max_length:
            return None

        score = 0

        # 信号 1：短文本（此时已满足长度要求，直接加分）
        score += 1

        # 信号 2：字号 >= 基准 + delta
        font_size = self._get_dominant_font_size(para)
        is_large_font = False
        if font_size is not None and self._base_font_size is not None:
            if font_size >= self._base_font_size + self.config.font_size_delta:
                is_large_font = True
                score += 2

        # 信号 3：主要 run 加粗（先计算，后面可能降权）
        is_bold = self._is_mostly_bold(para)

        # 信号 4：编号模式（标题型+2，列表型+1）
        has_numbering, number_depth, number_prefix, heading_numbering = self._detect_numbering(text)
        if has_numbering:
            score += 2 if heading_numbering else 1

        # 信号 5：不含句末标点（冒号结尾降权，可能是描述性文本）
        if not _SENTENCE_END_RE.search(text):
            score += 1
            if text.rstrip().endswith(("：", ":")):
                score -= 1

        # 列表型编号 + 基准字号 → 加粗只是强调，不是标题信号
        if has_numbering and not heading_numbering and not is_large_font:
            is_bold = False

        if is_bold:
            score += 2

        if score < self.config.min_score:
            return None

        indent = self._get_left_indent(para)

        return ManualHeadingCandidate(
            score=score,
            font_size=font_size or 0.0,
            has_numbering=has_numbering,
            heading_numbering=heading_numbering,
            number_depth=number_depth,
            indent=indent,
            number_prefix=number_prefix,
        )

    def build_level_map(self, candidates) -> None:
        """根据候选集合的字号分布构建字号→层级映射"""
        sizes = sorted(
            {c.font_size for c in candidates if not c.heading_numbering and c.font_size > 0},
            reverse=True,
        )
        self._font_size_level_map = {}
        for i, sz in enumerate(sizes):
            level = min(i + 1, 6)
            self._font_size_level_map[sz] = level

    def resolve_level(self, candidate: ManualHeadingCandidate) -> int:
        """确定最终层级"""
        if candidate.has_numbering and candidate.number_depth > 0:
            return min(candidate.number_depth, 6)

        # 无编号：查字号映射表
        level = self._font_size_level_map.get(candidate.font_size)
        if level is not None:
            return level

        # 兜底：字号越大层级越高
        if self._base_font_size and candidate.font_size > self._base_font_size:
            delta = candidate.font_size - self._base_font_size
            return min(max(1, 4 - int(delta / 2)), 6)

        return 2

    def _get_dominant_font_size(self, para) -> float | None:
        """获取段落主导字号（pt）"""
        sizes: list[float] = []
        for child in para._element:
            if child.tag == f"{{{W_NS}}}r":
                rPr = child.find(f"{{{W_NS}}}rPr")
                if rPr is not None:
                    sz_el = rPr.find(f"{{{W_NS}}}sz")
                    if sz_el is not None:
                        val = sz_el.get(f"{{{W_NS}}}val")
                        if val:
                            sizes.append(int(val) / 2.0)
        if not sizes:
            return None
        counter = Counter(sizes)
        return counter.most_common(1)[0][0]

    def _is_mostly_bold(self, para) -> bool:
        """检查段落中加粗 run 的占比"""
        total_runs = 0
        bold_runs = 0
        for child in para._element:
            if child.tag == f"{{{W_NS}}}r":
                t_el = child.find(f"{{{W_NS}}}t")
                if t_el is None or not t_el.text or not t_el.text.strip():
                    continue
                total_runs += 1
                rPr = child.find(f"{{{W_NS}}}rPr")
                if rPr is not None and rPr.find(f"{{{W_NS}}}b") is not None:
                    bold_runs += 1
        if total_runs == 0:
            return False
        return (bold_runs / total_runs) >= self.config.bold_ratio_threshold

    def _detect_numbering(self, text: str) -> tuple[bool, int, str, bool]:
        """检测编号模式，返回 (是否匹配, 层级深度, 编号前缀, 是否标题型编号)"""
        for pattern, kind, is_heading in _NUMBER_PATTERNS:
            m = pattern.match(text)
            if m:
                if kind == "decimal":
                    num_part = m.group(1) + m.group(2)
                    depth = num_part.count(".") + 1
                    prefix = m.group(0).strip()
                    return True, depth, prefix, is_heading
                elif kind == "cn_chapter":
                    return True, 1, m.group(0), is_heading
                elif kind == "cn_numeral":
                    return True, 2, m.group(0).rstrip(), is_heading
                elif kind == "cn_paren":
                    return True, 2, m.group(0), is_heading
                elif kind == "num_paren":
                    return True, 2, m.group(0), is_heading
                elif kind == "alpha":
                    return True, 2, m.group(0).strip(), is_heading
        return False, 0, "", False

    def _is_list_item(self, para) -> bool:
        """检查段落是否为列表项"""
        style_name = para.style.name if para.style else ""
        if style_name.startswith("List"):
            return True

        numPr = para._element.find(f"{{{W_NS}}}pPr/{{{W_NS}}}numPr")
        if numPr is not None:
            numId_el = numPr.find(f"{{{W_NS}}}numId")
            if numId_el is not None and numId_el.get(f"{{{W_NS}}}val", "0") != "0":
                return True
        return False

    def _is_known_non_heading(self, text: str) -> bool:
        """检查文本是否匹配已知的非标题模式（图表标题、单位标注、脚注等）"""
        for pattern in _EXCLUDE_PATTERNS:
            if pattern.search(text):
                return True
        return False

    def _get_left_indent(self, para) -> float:
        """获取段落左缩进量（pt）"""
        pPr = para._element.find(f"{{{W_NS}}}pPr")
        if pPr is None:
            return 0.0
        ind = pPr.find(f"{{{W_NS}}}ind")
        if ind is None:
            return 0.0
        left = ind.get(f"{{{W_NS}}}left")
        if left:
            return int(left) / 20.0  # twip → pt
        return 0.0


def make_anchor(text: str) -> str:
    """统一的锚点生成函数，供 structure 和 toc 模块共用。

    规则：转小写 + 非词字符替换为连字符 + 去首尾连字符。
    """
    anchor = text.lower()
    anchor = re.sub(r"[^\w一-鿿]+", "-", anchor)
    return anchor.strip("-")


class StructureParser:
    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()
        self._title_tree: list[TitleNode] = []
        self._doc_part = None  # 延迟设置，用于解析超链接
        self._formula_processor = FormulaProcessor()

    def set_doc_part(self, doc_part) -> None:
        self._doc_part = doc_part

    def parse(self, doc: Document) -> list[ContentBlock]:
        paragraphs = doc.paragraphs

        # 检测正文起始位置，用于排除封面页段落
        content_start = self._find_content_start_index(paragraphs)

        # 第一遍：校准基准字号 + 收集候选手动标题 + 识别中式标题样式
        manual_candidates: dict[int, ManualHeadingCandidate] = {}
        cn_heading_indices: set[int] = set()
        detector: ManualHeadingDetector | None = None
        if self.config.manual_heading.enabled:
            detector = ManualHeadingDetector(self.config.manual_heading)
            detector.calibrate(paragraphs)
            for i, para in enumerate(paragraphs):
                style_name = para.style.name if para.style else ""
                if style_name.startswith("Heading"):
                    continue
                # 识别中式标题样式（如"一、标题一"、"标题样式"等）
                if self._is_cn_heading_style(style_name) and para.text.strip():
                    cn_heading_indices.add(i)
                elif i < content_start:
                    # 封面/目录区域的段落不进行手动标题检测
                    continue
                else:
                    candidate = detector.detect(para)
                    if candidate:
                        manual_candidates[i] = candidate
            detector.build_level_map(manual_candidates.values())

        # 第二遍：生成 ContentBlock
        blocks: list[ContentBlock] = []
        for i, para in enumerate(paragraphs):
            style_name = para.style.name if para.style else ""

            if style_name.startswith("Heading"):
                blocks.append(self._parse_heading(para, style_name))
            elif i in cn_heading_indices:
                blocks.append(self._parse_cn_style_heading(para))
            elif i in manual_candidates:
                candidate = manual_candidates[i]
                level = detector.resolve_level(candidate)
                blocks.append(self._parse_manual_heading(para, candidate, level))
            else:
                block = self._parse_paragraph(para)
                if block:
                    blocks.append(block)

        return blocks

    def get_title_tree(self) -> list[TitleNode]:
        return self._title_tree

    @staticmethod
    def _find_content_start_index(paragraphs) -> int:
        """找到正文内容起始位置（封面/目录之后的第一个段落索引）。

        策略：
        1. 找 TOC 区域（样式以 "toc" 开头忽略大小写，或含"目录"文本）
        2. 从 TOC 标记向后扫描跳过所有 TOC 条目
        3. 无 TOC 时，找第一个真正的标题段落（Heading/cn_heading/标题型编号）
        4. 都找不到则返回 0
        """
        toc_marker_idx = None

        # 阶段1：定位 TOC 标记
        for i, para in enumerate(paragraphs):
            style_name = para.style.name if para.style else ""
            text = para.text.strip()

            # TOC 样式（忽略大小写，兼容 "TOC 1"/"toc 1"/"TOC 标题2"）
            if style_name.lower().startswith("toc"):
                if toc_marker_idx is None:
                    toc_marker_idx = i
            # "目录" 文本（仅取第一个）
            elif text in ("目录", "目 录") and toc_marker_idx is None:
                toc_marker_idx = i

        if toc_marker_idx is not None:
            # 从标记位置向后扫描，跳过所有 TOC 条目
            content_start = toc_marker_idx + 1
            for i in range(toc_marker_idx + 1, len(paragraphs)):
                para = paragraphs[i]
                style_name = para.style.name if para.style else ""
                text = para.text.strip()

                if style_name.lower().startswith("toc"):
                    content_start = i + 1
                elif not text:
                    continue  # 空段落，跳过
                else:
                    break  # 非空非TOC → 正文开始

            return content_start

        # 阶段2：无 TOC，找第一个真正的标题段落
        for i, para in enumerate(paragraphs):
            style_name = para.style.name if para.style else ""
            text = para.text.strip()
            if not text:
                continue

            # Heading 样式
            if style_name.startswith("Heading"):
                return i

            # cn_heading 样式（含"标题"/"Title"等关键词）
            if StructureParser._is_cn_heading_style(style_name):
                return i

            # 带标题型编号（如 "第一章"、"一、"）
            for pattern, kind, is_heading in _NUMBER_PATTERNS:
                if is_heading and pattern.match(text):
                    return i

        return 0

    @staticmethod
    def _is_cn_heading_style(style_name: str) -> bool:
        """检测中文标题样式名（非 Heading 标准样式但实际为标题）"""
        if style_name.startswith("Heading"):
            return False
        if style_name.startswith("List") or style_name.startswith("TOC"):
            return False
        for kw in _CN_HEADING_STYLE_KEYWORDS:
            if kw in style_name:
                return True
        return False

    def _parse_cn_style_heading(self, para) -> ContentBlock:
        """解析中式标题样式段落，从文本编号推断层级"""
        text = para.text.strip()

        # 长度检查：超过 max_length 降级为普通段落
        if len(text) > self.config.manual_heading.max_length:
            return self._parse_paragraph(para)

        anchor_text = _HEADING_NUMBER_RE.sub("", text).strip() or text
        anchor = make_anchor(anchor_text)

        # 从文本编号推断层级
        level = self._infer_cn_heading_level(text)

        node = TitleNode(level=level, text=text, anchor=anchor)
        self._add_to_title_tree(node)

        return ContentBlock(
            type=BlockType.HEADING,
            content=node,
            metadata={
                "_para_element": para._element,
                "cn_style_heading": True,
            },
        )

    def _infer_cn_heading_level(self, text: str) -> int:
        """从中式标题文本推断层级"""
        # 第X章 → 1级
        m = re.match(r"^第[一二三四五六七八九十百]+[章部篇节]", text)
        if m:
            return 1
        # 一、二、三、 → 2级
        if re.match(r"^[一二三四五六七八九十百]+[、]", text):
            return 2
        # （一）（二） → 3级
        if re.match(r"^[（(][一二三四五六七八九十]+[）)]", text):
            return 3
        # 无编号 → 默认2级
        return 2

    def _parse_heading(self, para, style_name: str) -> ContentBlock:
        level = self._extract_heading_level(style_name)
        text = para.text.strip()
        text = self._strip_heading_number(text)

        # 长度检查：超过 max_length 降级为普通段落
        if len(text) > self.config.manual_heading.max_length:
            return self._parse_paragraph(para)

        anchor = make_anchor(text)

        node = TitleNode(level=level, text=text, anchor=anchor)
        self._add_to_title_tree(node)

        return ContentBlock(
            type=BlockType.HEADING,
            content=node,
            metadata={"_para_element": para._element},
        )

    def _parse_manual_heading(
        self, para, candidate: ManualHeadingCandidate, level: int
    ) -> ContentBlock:
        text = para.text.strip()
        anchor_text = _HEADING_NUMBER_RE.sub("", text).strip() or text
        anchor = make_anchor(anchor_text)

        node = TitleNode(level=level, text=text, anchor=anchor)
        self._add_to_title_tree(node)

        return ContentBlock(
            type=BlockType.HEADING,
            content=node,
            metadata={
                "_para_element": para._element,
                "manual_heading": True,
            },
        )

    def _extract_heading_level(self, style_name: str) -> int:
        match = re.search(r"\d+", style_name)
        level = int(match.group()) if match else 1
        return min(level, self.config.max_heading_level)

    def _strip_heading_number(self, text: str) -> str:
        return _HEADING_NUMBER_RE.sub("", text).strip()

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
        omml_str = _element_to_string(omath_element)
        latex = self._formula_processor.omml_to_latex(omml_str)

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
