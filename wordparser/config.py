"""WordParser 配置模块

本模块定义了解析器的所有配置类，包括：
- TOCPosition: 目录位置枚举
- VisionModelConfig: 视觉模型配置
- MultimodalConfig: 多模态处理配置
- ParserConfig: 主解析器配置
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TOCPosition(Enum):
    """目录位置枚举

    定义自动生成的目录在 Markdown 文档中的插入位置。
    """
    BEFORE_TITLE = "before_title"  # 在文档标题之前插入目录
    AFTER_TITLE = "after_title"    # 在文档标题之后插入目录


@dataclass
class VisionModelConfig:
    """视觉模型配置

    配置多模态视觉模型的连接参数和调用行为。
    用于图片、Chart、SmartArt 等内容的 AI 识别。

    Attributes:
        base_url: 多模态 API 服务地址（如 LM Studio 本地服务）
        api_key: API 密钥（可选，本地服务通常不需要）
        model: 模型名称（需支持视觉能力，如 qwen3.5-4b、qwen3.5-9b）
        timeout: 单次请求超时时间（秒）
        temperature: 采样温度（0.0 为确定性输出，越高越随机）
    """
    base_url: str = "http://localhost:1234/v1"  # API 服务地址
    api_key: str | None = None                   # API 密钥（可选）
    model: str = "qwen3.5-4b"                    # 模型名称
    timeout: int = 600                           # 请求超时时间（秒）
    temperature: float = 0.0                     # 采样温度


@dataclass
class MultimodalConfig:
    """多模态处理配置

    控制图片、图表、SmartArt 等内容的多模态 AI 处理行为。

    Attributes:
        max_concurrent: 最大并发请求数（同时处理多少个图片/图表）
        batch_delay: 批次之间的延迟时间（秒），避免 API 限流
        retry_on_failure: 失败时是否自动重试
        model: 视觉模型配置详情
    """
    max_concurrent: int = 6                      # 最大并发请求数
    batch_delay: float = 0.1                     # 批次延迟（秒）
    retry_on_failure: bool = True                # 失败时重试
    model: VisionModelConfig = field(default_factory=VisionModelConfig)


@dataclass
class ParserConfig:
    """主解析器配置

    控制 Word 文档解析的整体行为和输出格式。

    Attributes:
        max_heading_level: 最大解析的标题层级（1-6），超过此层级的标题转为普通段落
        encoding: 输出 Markdown 文件的编码格式
        multimodal: 多模态处理配置（设为 None 则禁用多模态功能）
        libreoffice_path: LibreOffice 可执行文件路径（None 为自动检测）
        enable_render_fallback: 是否启用渲染降级（XML+LLM 失败时尝试 LibreOffice 渲染+视觉识别）
        generate_toc: 是否自动生成目录
        toc_position: 目录插入位置（文档标题前或后）
        include_header_footer: 是否提取页眉页脚
        include_comments: 是否提取文档批注（⚠️ 当前版本未实现）
        include_footnotes: 是否提取文档脚注（⚠️ 当前版本未实现）

    Note:
        include_comments、include_footnotes 配置项已预留，
        但当前版本尚未实现，设为 True 不会生效。
        include_header_footer 已实现，可直接使用。
    """
    max_heading_level: int = 6                   # 最大标题层级（1-6）
    encoding: str = "utf-8"                      # 输出编码
    multimodal: MultimodalConfig | None = field(default_factory=MultimodalConfig)  # 多模态配置
    libreoffice_path: str | None = None          # LibreOffice 路径（自动检测）
    enable_render_fallback: bool = True          # 启用渲染降级
    generate_toc: bool = True                    # 生成目录
    toc_position: TOCPosition = TOCPosition.AFTER_TITLE  # 目录位置
    include_header_footer: bool = False          # 包含页眉页脚
    include_comments: bool = False               # 包含批注（⚠️ 未实现）
    include_footnotes: bool = False              # 包含脚注（⚠️ 未实现）
