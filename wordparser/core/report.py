from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseStats:
    total_headings: int = 0
    total_paragraphs: int = 0
    total_tables: int = 0
    total_images: int = 0
    multimodal_calls: int = 0
    multimodal_failures: int = 0
    processing_time: float = 0.0


@dataclass
class ParseError:
    type: str
    message: str
    fatal: bool = False
    location: str | None = None


@dataclass
class ParseReport:
    success: bool
    output_path: Path | None
    errors: list[ParseError]
    stats: ParseStats

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def has_fatal_errors(self) -> bool:
        return any(e.fatal for e in self.errors)
