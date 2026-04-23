from __future__ import annotations

import re


class PostProcessor:
    MULTIPLE_BLANKS_RE = re.compile(r"\n{3,}")
    HEADING_RE = re.compile(r"^(#{1,6}\s)", re.MULTILINE)

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
        text = re.sub(r"([^\n])\n(#{1,6}\s)", r"\1\n\n\2", text)
        text = re.sub(r"(#{1,6}\s[^\n]+)\n([^\n#])", r"\1\n\n\2", text)
        return text
