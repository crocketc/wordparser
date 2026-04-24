from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TOCPosition(Enum):
    BEFORE_TITLE = "before_title"
    AFTER_TITLE = "after_title"


@dataclass
class VisionModelConfig:
    base_url: str = "http://localhost:1234/v1"
    api_key: str | None = None
    model: str = "qwen3.5-4b"
    timeout: int = 600
    temperature: float = 0.0


@dataclass
class MultimodalConfig:
    max_concurrent: int = 6
    batch_delay: float = 0.1
    retry_on_failure: bool = True
    model: VisionModelConfig = field(default_factory=VisionModelConfig)


@dataclass
class ParserConfig:
    max_heading_level: int = 6
    encoding: str = "utf-8"
    multimodal: MultimodalConfig | None = field(default_factory=MultimodalConfig)
    libreoffice_path: str | None = None
    enable_render_fallback: bool = True
    generate_toc: bool = True
    toc_position: TOCPosition = TOCPosition.AFTER_TITLE
    include_header_footer: bool = False
    include_comments: bool = False
    include_footnotes: bool = False
