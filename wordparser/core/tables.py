"""表格处理器模块

提供Word文档中表格的处理功能，包括：
- 简单表格的文本提取
- 复杂表格的识别
"""

from typing import Optional
from docx.table import Table


class TableProcessor:
    """表格处理器

    负责处理Word文档中的表格，提取表格内容并判断表格复杂度。

    Attributes:
        COMPLEX_ROW_THRESHOLD: 判定为复杂表格的行数阈值
        COMPLEX_COL_THRESHOLD: 判定为复杂表格的列数阈值
    """

    COMPLEX_ROW_THRESHOLD = 20
    COMPLEX_COL_THRESHOLD = 15

    def __init__(self):
        """初始化表格处理器"""
        pass

    def process_simple(self, table: Table) -> str:
        """处理简单表格，提取文本内容

        将表格转换为易读的文本格式，保留表格结构信息。

        Args:
            table: docx Table对象

        Returns:
            表格的文本表示，包含行列信息

        Examples:
            >>> processor = TableProcessor()
            >>> result = processor.process_simple(table)
            >>> print(result)
            | 姓名 | 年龄 | 职位 |
            | 张三 | 28 | 工程师 |
        """
        if not table:
            return ""

        lines = []

        # 处理每一行
        for row_idx, row in enumerate(table.rows):
            cells = []
            for cell in row.cells:
                # 获取单元格文本
                cell_text = cell.text.strip()
                cells.append(cell_text)

            # 用 | 分隔单元格
            line = " | ".join(cells)
            lines.append(f"| {line} |")

        return "\n".join(lines)

    def is_complex(self, table: Table) -> bool:
        """判断表格是否为复杂表格

        复杂表格的判定标准：
        1. 包含嵌套表格
        2. 包含合并单元格（跨行或跨列）
        3. 行数超过阈值 AND 列数超过阈值（大表格）

        Args:
            table: docx Table对象

        Returns:
            True表示复杂表格，False表示简单表格
        """
        if not table:
            return False

        # 检查行数和列数（大表格判定需要同时满足）
        if len(table.rows) > self.COMPLEX_ROW_THRESHOLD and len(table.columns) > self.COMPLEX_COL_THRESHOLD:
            return True

        # 检查嵌套表格
        for row in table.rows:
            for cell in row.cells:
                if cell.tables:
                    return True

        # 检查合并单元格
        for row in table.rows:
            for cell in row.cells:
                # 检查是否为合并单元格的一部分
                if cell._element.tcPr is not None:
                    # 检查gridSpan（跨列）
                    grid_span = cell._element.tcPr.gridSpan
                    if grid_span is not None and grid_span.val > 1:
                        return True

                    # 检查vMerge（跨行）
                    v_merge = cell._element.tcPr.vMerge
                    if v_merge is not None:
                        return True

        return False

    def extract_table_data(self, table: Table) -> str:
        """提取表格的完整单元格数据，用于 LLM 解析

        Args:
            table: docx Table 对象

        Returns:
            格式化的单元格数据文本
        """
        if not table:
            return ""

        lines = []
        for row_idx, row in enumerate(table.rows):
            cells = []
            for cell in row.cells:
                cell_text = cell.text.strip().replace("\n", " ")
                merge_info = ""
                tc_pr = cell._element.tcPr
                if tc_pr is not None:
                    grid_span = tc_pr.gridSpan
                    if grid_span is not None and grid_span.val > 1:
                        merge_info = f"[colspan={grid_span.val}]"
                    v_merge = tc_pr.vMerge
                    if v_merge is not None:
                        merge_info += "[rowspan]"
                cells.append(f"{cell_text}{merge_info}")
            lines.append(f"行{row_idx}: {' | '.join(cells)}")

        return "\n".join(lines)
