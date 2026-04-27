"""目录生成器"""
from typing import List, Optional
from dataclasses import dataclass
from wordparser.core.structure import make_anchor


@dataclass
class Heading:
    """标题数据类"""
    level: int
    text: str
    number: str = ""



class TOCGenerator:
    """目录生成器

    根据文档标题层级生成Markdown格式的目录。
    """

    def __init__(self):
        """初始化目录生成器"""
        self.default_indent_size = 2  # 默认每级缩进空格数

    def generate(
        self,
        headings: List[Heading],
        max_depth: int = 6,
        indent_size: Optional[int] = None,
        add_anchors: bool = False
    ) -> str:
        """生成目录

        Args:
            headings: 标题列表
            max_depth: 最大包含的标题级别（1-6），默认6
            indent_size: 每级缩进的空格数，默认2
            add_anchors: 是否添加锚点链接，默认False

        Returns:
            str: Markdown格式的目录字符串

        Example:
            >>> generator = TOCGenerator()
            >>> headings = [
            ...     Heading(level=1, text="第一章", number="1"),
            ...     Heading(level=2, text="第一节", number="1.1"),
            ... ]
            >>> toc = generator.generate(headings)
            >>> print(toc)
            1. 第一章
              1.1. 第一节
        """
        if not headings:
            return ""

        indent_size = indent_size or self.default_indent_size

        lines = []

        for heading in headings:
            # 跳过超过最大深度的标题
            if heading.level > max_depth:
                continue

            # 计算缩进
            indent = " " * ((heading.level - 1) * indent_size)

            # 构建标题文本
            if heading.number:
                title_text = f"{heading.number}. {heading.text}"
            else:
                title_text = heading.text

            # 添加锚点（如果启用）
            if add_anchors:
                anchor = self._create_anchor(heading.text)
                line = f'{indent}- [{title_text}](#{anchor})'
            else:
                line = f'{indent}- {title_text}'

            lines.append(line)

        return "\n".join(lines)

    def _create_anchor(self, text: str) -> str:
        """创建锚点标识符（使用统一的锚点生成函数）"""
        return make_anchor(text)

    def generate_with_depth_indicators(
        self,
        headings: List[Heading],
        max_depth: int = 6
    ) -> str:
        """生成带深度指示符的目录

        使用数字标记表示层级关系，如:
        1. 第一章
        1.1 第一节
        1.1.1 小节

        Args:
            headings: 标题列表
            max_depth: 最大包含的标题级别

        Returns:
            str: Markdown格式的目录字符串
        """
        if not headings:
            return ""

        lines = []

        for heading in headings:
            if heading.level > max_depth:
                continue

            if heading.number:
                line = f"{heading.number} {heading.text}"
            else:
                line = heading.text

            lines.append(line)

        return "\n".join(lines)

    def generate_bullet_style(
        self,
        headings: List[Heading],
        max_depth: int = 6
    ) -> str:
        """生成项目符号风格的目录

        使用不同符号表示不同层级:
        • 一级标题
          ◦ 二级标题
            ▪ 三级标题

        Args:
            headings: 标题列表
            max_depth: 最大包含的标题级别

        Returns:
            str: Markdown格式的目录字符串
        """
        if not headings:
            return ""

        bullets = ['•', '◦', '▪', '·', '⋄', '‒']
        lines = []

        for heading in headings:
            if heading.level > max_depth:
                continue

            indent = "  " * (heading.level - 1)
            bullet = bullets[(heading.level - 1) % len(bullets)]

            if heading.number:
                title_text = f"{heading.number}. {heading.text}"
            else:
                title_text = heading.text

            line = f"{indent}{bullet} {title_text}"
            lines.append(line)

        return "\n".join(lines)
