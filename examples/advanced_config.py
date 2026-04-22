"""WordParser 高级配置示例

演示如何使用高级功能，包括多模态配置、并发控制等。
"""

from pathlib import Path
from wordparser import WordParser, ParserConfig, MultimodalConfig, VisionModelConfig, TOCPosition


def multimodal_config():
    """多模态配置示例"""
    print("=== 多模态配置示例 ===\n")

    # 配置视觉模型
    vision_config = VisionModelConfig(
        base_url="http://localhost:1234/v1",  # 模型 API 地址
        api_key=None,  # API 密钥（如果需要）
        model="qwen2-vl-7b",  # 模型名称
        timeout=60,  # 超时时间（秒）
        temperature=0.0,  # 温度参数
    )

    # 配置多模态处理
    multimodal_config = MultimodalConfig(
        max_concurrent=4,  # 最大并发请求数
        batch_delay=0.1,  # 批处理延迟（秒）
        retry_on_failure=True,  # 失败时重试
        model=vision_config,
    )

    # 创建解析器配置
    config = ParserConfig(
        multimodal=multimodal_config,
        generate_toc=True,
    )

    # 创建解析器
    parser = WordParser(config)

    # 解析文档
    markdown, report = parser.parse_with_report("example.docx")

    print(f"多模态调用次数: {report.stats.multimodal_calls}")
    print(f"多模态失败次数: {report.stats.multimodal_failures}")


def toc_position_config():
    """目录位置配置示例"""
    print("=== 目录位置配置示例 ===\n")

    # 配置目录在标题之前
    config_before = ParserConfig(
        generate_toc=True,
        toc_position=TOCPosition.BEFORE_TITLE,
    )

    # 配置目录在标题之后
    config_after = ParserConfig(
        generate_toc=True,
        toc_position=TOCPosition.AFTER_TITLE,
    )

    # 创建解析器并对比
    parser_before = WordParser(config_before)
    parser_after = WordParser(config_after)

    markdown_before = parser_before.parse("example.docx")
    markdown_after = parser_after.parse("example.docx")

    print("目录在标题之前:")
    print(markdown_before[:300])
    print("\n目录在标题之后:")
    print(markdown_after[:300])


def advanced_processing_config():
    """高级处理配置示例"""
    print("=== 高级处理配置示例 ===\n")

    # 完整的高级配置
    config = ParserConfig(
        # 基本配置
        max_heading_level=6,  # 最大标题级别
        encoding="utf-8",  # 文件编码

        # 目录配置
        generate_toc=True,  # 生成目录
        toc_position=TOCPosition.AFTER_TITLE,  # 目录位置

        # 内容包含配置
        include_header_footer=False,  # 不包含页眉页脚
        include_comments=False,  # 不包含注释

        # 多模态配置（如果需要）
        multimodal=None,  # 暂不使用多模态

        # LibreOffice 路径（如果需要）
        libreoffice_path=None,  # 自动检测
    )

    # 创建解析器
    parser = WordParser(config)

    # 解析文档
    markdown, report = parser.parse_with_report("example.docx")

    print(f"处理完成，共 {report.stats.total_headings} 个标题")


def batch_processing():
    """批处理示例"""
    print("=== 批处理示例 ===\n")

    # 要处理的文档列表
    docx_files = [
        "document1.docx",
        "document2.docx",
        "document3.docx",
    ]

    # 创建解析器
    parser = WordParser()

    # 批量处理
    results = []
    for docx_file in docx_files:
        try:
            markdown, report = parser.parse_with_report(docx_file)

            # 保存结果
            output_path = Path(docx_file).with_suffix(".md")
            output_path.write_text(markdown, encoding="utf-8")

            results.append({
                "file": docx_file,
                "success": report.success,
                "headings": report.stats.total_headings,
                "paragraphs": report.stats.total_paragraphs,
            })

            print(f"✓ 已处理: {docx_file}")

        except Exception as e:
            print(f"✗ 处理失败: {docx_file}, 错误: {e}")
            results.append({
                "file": docx_file,
                "success": False,
                "error": str(e),
            })

    # 输出汇总
    print("\n批处理汇总:")
    for result in results:
        status = "✓" if result.get("success") else "✗"
        print(f"  {status} {result['file']}")


def error_handling():
    """错误处理示例"""
    print("=== 错误处理示例 ===\n")

    from wordparser import DocumentError, WordParserError

    # 创建解析器
    parser = WordParser()

    # 尝试解析不存在的文件
    try:
        markdown = parser.parse("nonexistent.docx")
    except DocumentError as e:
        print(f"文档错误: {e}")
    except WordParserError as e:
        print(f"解析错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

    # 解析并检查报告中的错误
    try:
        markdown, report = parser.parse_with_report("example.docx")

        if report.has_errors():
            print("解析过程中发生错误:")
            for error in report.errors:
                print(f"  - {error.type}: {error.message}")

        if report.has_fatal_errors():
            print("存在致命错误，解析结果可能不完整")

    except Exception as e:
        print(f"解析失败: {e}")


if __name__ == "__main__":
    # 注意：运行这些示例前，请确保有相应的 Word 文档

    # 1. 多模态配置
    # multimodal_config()

    # 2. 目录位置配置
    # toc_position_config()

    # 3. 高级处理配置
    # advanced_processing_config()

    # 4. 批处理
    # batch_processing()

    # 5. 错误处理
    # error_handling()

    print("请取消注释要运行的示例函数")
