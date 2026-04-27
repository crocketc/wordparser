"""SmartArt 数据提取器

从 .docx ZIP 包中提取 SmartArt (diagram) XML，解析节点和关系。
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Optional

from wordparser.core.models import SmartArtData, SmartArtNode


class SmartArtExtractor:
    """从 .docx 中提取 SmartArt 数据"""

    def extract(self, docx_path: Path) -> list[SmartArtData]:
        results = []
        docx_path = Path(docx_path)

        with zipfile.ZipFile(docx_path, "r") as zf:
            data_files = sorted(
                [n for n in zf.namelist() if n.startswith("word/diagrams/data") and n.endswith(".xml")]
            )

            for data_file in data_files:
                xml_content = zf.read(data_file).decode("utf-8")
                smartart_data = self._parse_smartart_xml(xml_content)
                if smartart_data:
                    results.append(smartart_data)

        return results

    def extract_by_rid(self, docx_path: Path, rid_to_target: dict[str, str]) -> dict[str, SmartArtData]:
        """按 rId 提取 SmartArt 数据，返回 {rId: SmartArtData}。

        Args:
            docx_path: .docx 文件路径
            rid_to_target: {rId: "diagrams/data1.xml"} 映射
        """
        results: dict[str, SmartArtData] = {}
        docx_path = Path(docx_path)

        with zipfile.ZipFile(docx_path, "r") as zf:
            for rId, target in rid_to_target.items():
                sa_path = f"word/{target}" if not target.startswith("word/") else target
                if sa_path in zf.namelist():
                    xml_content = zf.read(sa_path).decode("utf-8")
                    sa_data = self._parse_smartart_xml(xml_content)
                    if sa_data:
                        results[rId] = sa_data

        return results

    def _parse_smartart_xml(self, xml_content: str) -> Optional[SmartArtData]:
        points = self._extract_points(xml_content)
        connections = self._extract_connections(xml_content)
        root_nodes = self._build_tree(points, connections)

        return SmartArtData(
            layout_type=self._detect_layout_type(xml_content),
            root_nodes=root_nodes,
            raw_xml=xml_content,
        )

    def _extract_points(self, xml: str) -> dict[int, tuple[str, str]]:
        """提取所有节点：返回 {modelId: (type, text)}"""
        points = {}
        pt_pattern = re.finditer(
            r'<dgm:pt\s+modelId="(\d+)"(?:\s+type="([^"]*)")?\s*>.*?</dgm:pt>',
            xml, re.DOTALL,
        )
        for match in pt_pattern:
            model_id = int(match.group(1))
            pt_type = match.group(2) or ""
            pt_block = match.group(0)
            texts = re.findall(r'<a:t>([^<]+)</a:t>', pt_block)
            text = " ".join(texts).strip()
            points[model_id] = (pt_type, text)
        return points

    def _extract_connections(self, xml: str) -> list[tuple[int, int]]:
        """提取父子关系：返回 [(parentId, childId), ...]"""
        connections = []
        seen = set()

        cxn_self = re.finditer(
            r'<dgm:cxn\s+[^>]*srcId="(\d+)"[^>]*destId="(\d+)"[^>]*type="parOf"[^>]*/?\s*>',
            xml,
        )
        for match in cxn_self:
            pair = (int(match.group(1)), int(match.group(2)))
            if pair not in seen:
                connections.append(pair)
                seen.add(pair)

        cxn_full = re.finditer(
            r'<dgm:cxn\s+[^>]*srcId="(\d+)"[^>]*destId="(\d+)"[^>]*type="parOf"[^>]*>.*?</dgm:cxn>',
            xml, re.DOTALL,
        )
        for match in cxn_full:
            pair = (int(match.group(1)), int(match.group(2)))
            if pair not in seen:
                connections.append(pair)
                seen.add(pair)

        return connections

    def _build_tree(
        self,
        points: dict[int, tuple[str, str]],
        connections: list[tuple[int, int]],
    ) -> list[SmartArtNode]:
        children_map: dict[int, list[int]] = {}
        for parent_id, child_id in connections:
            children_map.setdefault(parent_id, []).append(child_id)

        doc_children = children_map.get(0, [])
        if not doc_children:
            all_children = {child for _, child in connections}
            root_ids = [
                pid for pid in points
                if pid != 0 and points[pid][0] != "doc" and pid not in all_children
            ]
        else:
            root_ids = doc_children

        def make_node(node_id: int, level: int) -> SmartArtNode:
            _, text = points.get(node_id, ("", ""))
            child_ids = children_map.get(node_id, [])
            children = [make_node(cid, level + 1) for cid in child_ids]
            return SmartArtNode(text=text, level=level, children=children)

        return [make_node(rid, 0) for rid in root_ids]

    def _detect_layout_type(self, xml: str) -> str:
        return "unknown"

    def format_for_llm(self, data: SmartArtData) -> str:
        lines = []
        lines.append("SmartArt 类型: 流程/结构图")
        lines.append(f"节点数: {self._count_nodes(data.root_nodes)}")
        lines.append("")
        lines.append("节点结构:")

        def format_node(node: SmartArtNode, indent: int = 0):
            prefix = "  " * indent + "- " if indent > 0 else "- "
            lines.append(f"{prefix}{node.text}")
            for child in node.children:
                format_node(child, indent + 1)

        for node in data.root_nodes:
            format_node(node)

        return "\n".join(lines)

    def _count_nodes(self, nodes: list[SmartArtNode]) -> int:
        count = len(nodes)
        for node in nodes:
            count += self._count_nodes(node.children)
        return count
