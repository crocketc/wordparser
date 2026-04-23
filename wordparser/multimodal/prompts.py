"""Prompt模板模块

定义用于多模态AI解析的各种提示词模板。
"""

# 表格解析提示词
TABLE_PROMPT = """请分析这张图片中的表格内容，并按照以下要求返回结果：

1. **表格结构**：识别表格的行数和列数
2. **表头信息**：提取表格的表头（第一行）
3. **数据内容**：逐行提取表格中的数据
4. **合并单元格**：如果有合并单元格，请特别标注

返回格式请使用Markdown表格格式，例如：

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |

如果表格过于复杂或无法识别，请说明原因。"""

# 图片描述提示词
IMAGE_PROMPT = """请详细描述这张图片的内容，包括：

1. **主要元素**：图片中的主要物体、人物或场景
2. **布局结构**：元素的排列和空间关系
3. **文本内容**：如果有文字，请提取所有可见文本
4. **颜色和样式**：颜色方案、字体、图形样式等
5. **目的推断**：根据内容推断图片的用途或含义

请使用清晰的结构化语言描述，便于后续处理。"""

# 图表解析提示词
CHART_PROMPT = """请分析这张图表图片，并提供以下信息：

1. **图表类型**：柱状图、折线图、饼图、散点图等
2. **标题和标签**：图表标题、坐标轴标签、图例
3. **数据系列**：识别数据系列的名称和数量
4. **数据值**：尽可能准确地读取图表中的数值
5. **趋势分析**：描述数据呈现的趋势或模式
6. **关键洞察**：从图表中得出的主要结论

返回格式：
- 图表类型：[类型]
- 标题：[标题]
- 数据：[结构化数据]
- 洞察：[主要发现]"""

# SmartArt解析提示词
SMARTART_PROMPT = """请分析这张SmartArt或流程图，并提供：

1. **图形类型**：层次结构、流程图、循环图、矩阵等
2. **节点信息**：识别所有文本框及其内容
3. **层级关系**：描述元素之间的层级或逻辑关系
4. **连接关系**：箭头或连接线表示的关系
5. **流程逻辑**：如果是流程图，描述步骤顺序

返回格式请使用结构化的文本或Mermaid图表格式（如果适用）。

示例输出：
```
类型：层次结构
根节点：[内容]
├── 子节点1：[内容]
│   └── 孙节点1：[内容]
└── 子节点2：[内容]
```"""


def get_table_prompt(custom_instructions: str = "") -> str:
    """获取表格解析提示词

    Args:
        custom_instructions: 自定义指令，将附加到基础提示词后

    Returns:
        完整的表格解析提示词
    """
    if custom_instructions:
        return TABLE_PROMPT + "\n\n额外要求：\n" + custom_instructions
    return TABLE_PROMPT


def get_image_prompt(custom_instructions: str = "") -> str:
    """获取图片描述提示词

    Args:
        custom_instructions: 自定义指令

    Returns:
        完整的图片描述提示词
    """
    if custom_instructions:
        return IMAGE_PROMPT + "\n\n额外要求：\n" + custom_instructions
    return IMAGE_PROMPT


def get_chart_prompt(custom_instructions: str = "") -> str:
    """获取图表解析提示词

    Args:
        custom_instructions: 自定义指令

    Returns:
        完整的图表解析提示词
    """
    if custom_instructions:
        return CHART_PROMPT + "\n\n额外要求：\n" + custom_instructions
    return CHART_PROMPT


def get_smartart_prompt(custom_instructions: str = "") -> str:
    """获取SmartArt解析提示词

    Args:
        custom_instructions: 自定义指令

    Returns:
        完整的SmartArt解析提示词
    """
    if custom_instructions:
        return SMARTART_PROMPT + "\n\n额外要求：\n" + custom_instructions
    return SMARTART_PROMPT


# Chart 结构化数据 LLM 提示词（XML 提取模式）
CHART_DATA_PROMPT = """你是一个专业的数据分析师。以下是从一个图表中提取的结构化数据，请将其转换为清晰的 Markdown 格式。

要求：
1. 输出图表标题（如有）
2. 用 Markdown 表格展示数据
3. 简要描述图表中的关键趋势或发现

图表数据：
{chart_data}

请直接输出 Markdown 格式结果。"""

# SmartArt 结构化数据 LLM 提示词（XML 提取模式）
SMARTART_DATA_PROMPT = """你是一个专业的内容整理专家。以下是从一个 SmartArt 图形中提取的结构化数据，请将其转换为清晰的 Markdown 格式。

要求：
1. 用 Markdown 列表展示节点层级关系
2. 保留原始的层级缩进
3. 如有流程逻辑，用箭头或编号标注步骤顺序

SmartArt 数据：
{smartart_data}

请直接输出 Markdown 格式结果。"""

# 复杂表格 LLM 提示词
COMPLEX_TABLE_PROMPT = """你是一个专业的表格数据整理专家。以下是一个复杂 Word 表格的单元格数据，请将其重建为正确的 Markdown 表格。

要求：
1. 准确识别表头行
2. 处理合并单元格（用 colspan/rowspan 标注或拆分为多个单元格）
3. 保持数据的对齐关系

单元格数据：
{table_data}

请直接输出 Markdown 表格。"""
