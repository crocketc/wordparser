from __future__ import annotations

import re


class PostProcessor:
    MULTIPLE_BLANKS_RE = re.compile(r"\n{3,}")
    HEADING_RE = re.compile(r"^(#{1,6}\s)", re.MULTILINE)
    CODE_BLOCK_RE = re.compile(r"(`{3,}).*?\1", re.DOTALL)

    def process(self, markdown: str) -> str:
        markdown = self._normalize_blank_lines(markdown)
        markdown = self._trim_lines(markdown)
        markdown = self._ensure_heading_spacing(markdown)
        markdown = markdown.strip() + "\n"
        return markdown

    def _normalize_blank_lines(self, text: str) -> str:
        return self.MULTIPLE_BLANKS_RE.sub("\n\n", text)

    def _trim_lines(self, text: str) -> str:
        lines = text.split("\n")
        return "\n".join(line.rstrip() for line in lines)

    def _ensure_heading_spacing(self, text: str) -> str:
        # 提取代码块，用占位符替换以避免代码块内的 # 被误处理
        code_blocks: list[str] = []
        def save_code_block(m):
            code_blocks.append(m.group(0))
            return f"\x00CODE_BLOCK_{len(code_blocks) - 1}\x00"

        text = self.CODE_BLOCK_RE.sub(save_code_block, text)

        text = re.sub(r"([^\n])\n(#{1,6}\s)", r"\1\n\n\2", text)
        text = re.sub(r"(#{1,6}\s[^\n]+)\n([^\n#])", r"\1\n\n\2", text)

        # 还原代码块
        for i, block in enumerate(code_blocks):
            text = text.replace(f"\x00CODE_BLOCK_{i}\x00", block)

        return text
