"""WordParser CLI工具

所有默认值动态从 config.py 读取，实现单一配置源（Single Source of Truth）
"""

import logging
from pathlib import Path
from typing import Optional

import typer

from wordparser import ParserConfig, MultimodalConfig, VisionModelConfig, WordParser, configure_logging

app = typer.Typer(
    name="wordparser",
    help="Word文档转Markdown解析工具",
    add_completion=False,
)

# 从 config.py 动态读取默认值（单一配置源）
_DEFAULT_MULTIMODAL = MultimodalConfig()
_DEFAULT_PARSER = ParserConfig()


@app.command()
def parse(
    docx_file: str = typer.Argument(
        ...,
        help="要解析的Word文档路径（支持 .doc 和 .docx）",
        exists=True,
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="输出Markdown文件路径（默认打印到 stdout）",
    ),
    multimodal: bool = typer.Option(
        _DEFAULT_MULTIMODAL.enabled,
        "--multimodal/--no-multimodal",
        help=f"是否启用多模态AI解析（图片/图表/SmartArt）（默认: {_DEFAULT_MULTIMODAL.enabled}）",
    ),
    vision_url: Optional[str] = typer.Option(
        None,
        "--vision-url",
        help="多模态视觉模型API地址",
    ),
    vision_model: Optional[str] = typer.Option(
        None,
        "--vision-model",
        help="视觉模型名称",
    ),
    max_concurrent: int = typer.Option(
        _DEFAULT_MULTIMODAL.max_concurrent,
        "--max-concurrent",
        help=f"最大并发请求数（默认: {_DEFAULT_MULTIMODAL.max_concurrent}，见 wordparser.config.MultimodalConfig）",
    ),
    render_fallback: bool = typer.Option(
        _DEFAULT_PARSER.enable_render_fallback,
        "--render-fallback/--no-render-fallback",
        help=f"解析失败时是否降级到LibreOffice渲染+多模态识别（默认: {_DEFAULT_PARSER.enable_render_fallback}）",
    ),
    libreoffice_path: Optional[str] = typer.Option(
        None,
        "--libreoffice-path",
        help="LibreOffice 可执行文件路径（自动检测）",
    ),
    toc: bool = typer.Option(
        _DEFAULT_PARSER.generate_toc,
        "--toc/--no-toc",
        help=f"是否生成目录（默认: {_DEFAULT_PARSER.generate_toc}）",
    ),
    max_heading: int = typer.Option(
        _DEFAULT_PARSER.max_heading_level,
        "--max-heading",
        help="最大标题级别（1-6）（默认: 见 wordparser.config.ParserConfig）",
        min=1,
        max=6,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="显示详细信息",
    ),
):
    """
    解析Word文档为Markdown格式

    所有配置项的默认值见 wordparser.config 模块。

    示例:
        wordparser parse document.docx
        wordparser parse document.doc -o output.md
        wordparser parse document.docx --no-toc --max-heading 3
        wordparser parse document.docx --vision-url http://localhost:1234/v1
        wordparser parse document.docx --no-multimodal
    """
    try:
        # 始终创建 MultimodalConfig，使用默认值或用户指定的值
        model_config = VisionModelConfig(
            base_url=vision_url or _DEFAULT_MULTIMODAL.model.base_url,
            model=vision_model or _DEFAULT_MULTIMODAL.model.model,
        )
        multimodal_config = MultimodalConfig(
            enabled=multimodal,
            max_concurrent=max_concurrent,
            model=model_config,
        )

        config = ParserConfig(
            generate_toc=toc,
            max_heading_level=max_heading,
            multimodal=multimodal_config,
            enable_render_fallback=render_fallback,
            libreoffice_path=libreoffice_path,
        )

        configure_logging(config.logging)

        parser = WordParser(config)

        if verbose:
            typer.echo(f"正在解析文档: {docx_file}")

        markdown, report = parser.parse_with_report(docx_file)

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            if verbose:
                typer.echo(f"已保存到: {output_path}")
        else:
            typer.echo(markdown)

        if verbose:
            typer.echo("\n解析统计:")
            typer.echo(f"  标题数: {report.stats.total_headings}")
            typer.echo(f"  段落数: {report.stats.total_paragraphs}")
            typer.echo(f"  表格数: {report.stats.total_tables}")
            typer.echo(f"  图片数: {report.stats.total_images}")

        if report.has_errors():
            if verbose:
                typer.echo("\n警告: 解析过程中发生错误", err=True)
            for error in report.errors:
                typer.echo(f"  - {error.type}: {error.message}", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"错误: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def version():
    """显示版本信息"""
    typer.echo("WordParser v0.1.0")


if __name__ == "__main__":
    app()
