"""WordParser 基础使用示例

演示如何使用 WordParser 将 Word 文档转换为 Markdown 格式。
"""

from pathlib import Path
from wordparser import WordParser, ParserConfig


def basic_parse():
    """基础解析示例"""
    print("=== 基础解析示例 ===\n")

    # 创建解析器（使用默认配置）
    parser = WordParser()

    # 解析文档
    markdown = parser.parse("example.docx")

    # 输出结果
    print(markdown)


def parse_with_report():
    """解析并获取报告"""
    print("=== 解析并获取报告 ===\n")

    # 创建解析器
    parser = WordParser()

    # 解析文档并获取报告
    markdown, report = parser.parse_with_report("example.docx")

    # 输出 Markdown
    print("Markdown 内容:")
    print(markdown[:200] + "..." if len(markdown) > 200 else markdown)
    print()

    # 输出统计信息
    print("解析报告:")
    print(f"  成功: {report.success}")
    print(f"  标题数: {report.stats.total_headings}")
    print(f"  段落数: {report.stats.total_paragraphs}")
    print(f"  表格数: {report.stats.total_tables}")
    print(f"  图片数: {report.stats.total_images}")


def custom_config():
    """自定义配置示例"""
    print("=== 自定义配置示例 ===\n")

    # 创建自定义配置
    config = ParserConfig(
        generate_toc=False,  # 不生成目录
        max_heading_level=3,  # 只解析到三级标题
        encoding="utf-8",
    )

    # 使用自定义配置创建解析器
    parser = WordParser(config)

    # 解析文档
    markdown = parser.parse("example.docx")

    print(markdown)


def save_to_file():
    """保存到文件示例"""
    print("=== 保存到文件示例 ===\n")

    # 创建解析器
    parser = WordParser()

    # 解析文档
    markdown, _ = parser.parse_with_report("example.docx")

    # 保存到文件
    output_path = Path("output.md")
    output_path.write_text(markdown, encoding="utf-8")

    print(f"已保存到: {output_path}")


if __name__ == "__main__":
    # 注意：运行这些示例前，请确保有一个名为 example.docx 的 Word 文档

    # 1. 基础解析
    # basic_parse()

    # 2. 解析并获取报告
    # parse_with_report()

    # 3. 自定义配置
    # custom_config()

    # 4. 保存到文件
    # save_to_file()

    print("请取消注释要运行的示例函数")
