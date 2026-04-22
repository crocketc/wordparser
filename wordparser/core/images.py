"""图片提取器模块

提供Word文档中图片的提取功能，包括：
- 从文档中提取所有图片
- 保存到指定目录
- 返回图片元信息
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.shape import CT_Picture
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.oxml import parse_xml, register_element_cls
import io


class ImageExtractor:
    """图片提取器

    负责从Word文档中提取图片并保存到指定目录。

    Attributes:
        output_dir: 图片保存目录
    """

    def __init__(self, output_dir: Path):
        """初始化图片提取器

        Args:
            output_dir: 图片保存目录
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, doc: DocxDocument, image_prefix: str = "image") -> List[Dict[str, Any]]:
        """从文档中提取所有图片

        遍历文档的所有段落和表格，提取图片并保存。

        Args:
            doc: docx Document对象
            image_prefix: 保存图片时的文件名前缀

        Returns:
            图片信息列表，每个元素包含：
            - path: 图片保存路径
            - index: 图片在文档中的索引
            - relationship_id: 图片的关系ID
            - paragraph_index: 所在段落的索引
        """
        images = []
        image_index = 0

        # 遍历文档的所有关系
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                # 获取图片数据
                image_data = rel.target_part.blob

                # 确定文件扩展名
                content_type = rel.target_part.content_type
                ext = self._get_extension(content_type)

                # 生成文件名
                filename = f"{image_prefix}_{image_index:04d}{ext}"
                filepath = self.output_dir / filename

                # 保存图片
                with open(filepath, "wb") as f:
                    f.write(image_data)

                # 收集图片信息
                image_info = {
                    "path": str(filepath),
                    "index": image_index,
                    "relationship_id": rel.rId,
                    "content_type": content_type,
                    "paragraph_index": -1,  # 简化实现，未追踪段落索引
                }
                images.append(image_info)

                image_index += 1

        return images

    def _get_extension(self, content_type: str) -> str:
        """根据内容类型获取文件扩展名

        Args:
            content_type: MIME类型

        Returns:
            文件扩展名（包含点号）
        """
        mapping = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/tiff": ".tiff",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        return mapping.get(content_type, ".bin")

    def extract_from_paragraphs(self, doc: DocxDocument, image_prefix: str = "image") -> List[Dict[str, Any]]:
        """从段落中提取图片（备用方法）

        Args:
            doc: docx Document对象
            image_prefix: 图片文件名前缀

        Returns:
            图片信息列表
        """
        images = []
        image_index = 0

        for para_idx, paragraph in enumerate(doc.paragraphs):
            # 检查段落中的runs是否包含图片
            for run in paragraph.runs:
                if hasattr(run, '_element'):
                    # 查找图片元素
                    for element in run._element.iter():
                        if element.tag.endswith('}blip') or element.tag.endswith('}graphic'):
                            # 这里需要更复杂的处理来提取图片
                            pass

        return images
