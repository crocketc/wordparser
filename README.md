# WordParser

> Word 文档转 Markdown 解析库 —— 支持 .doc/.docx 格式，集成多模态 AI 解析图表和图片

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.1.0-orange.svg)](pyproject.toml)

## 特性

### 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **格式支持** | 支持 .doc 和 .docx 格式 | ✅ 已实现 |
| **结构解析** | 标题（1-6级）、段落、列表转换 | ✅ 已实现 |
| **表格处理** | 简单表格 MD 化 + 复杂表格 LLM 重建 | ✅ 已实现 |
| **图片解析** | 零持久化多模态 AI 识别 | ✅ 已实现 |
| **Chart 图表** | XML 数据提取 + LLM 语义理解 | ✅ 已实现 |
| **SmartArt** | XML 数据提取 + LLM 语义理解 | ✅ 已实现 |
| **公式转换** | OMML → LaTeX | ✅ 已实现 |
| **目录生成** | 自动生成带锚点的 MD 目录 | ✅ 已实现 |
| **降级机制** | LibreOffice 渲染 + 视觉模型降级 | ✅ 已实现 |

### 计划中功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **批注处理** | 提取文档批注 | 🚧 配置项预留，未实现 |
| **脚注处理** | 提取文档脚注 | 🚧 配置项预留，未实现 |

> 📋 **完整功能规范**: 查看 [OpenSpec 规范文档](openspec/specs/wordparser-core/spec.md) 了解详细的功能规格和场景定义。

### 技术亮点

- **零持久化**: 图片/图表内容不经磁盘存储，直接内存处理
- **多模态 AI**: 集成视觉模型（支持 Qwen3.5-4b 等全模态模型）
- **两级降级**: XML+LLM → 渲染+视觉 → 失败标记
- **并发处理**: 默认6并发，可配置
- **CLI 工具**: 开箱即用的命令行工具

## 安装

### Python 依赖

```bash
# 基础安装
pip install -e .

# 带 CLI 工具
pip install -e ".[cli]"

# 开发环境
pip install -e ".[cli,dev]"
```

### 系统依赖

**LibreOffice**（可选，用于 .doc 转换和渲染降级）:
- Windows: 下载安装 [LibreOffice](https://www.libreoffice.org/)
- macOS: `brew install libreoffice`
- Linux: `sudo apt install libreoffice`

**Poppler**（可选，用于 PDF 转图片）:
- Windows: `choco install poppler` 或 `conda install -c conda-forge poppler`
- macOS: `brew install poppler`
- Linux: `sudo apt-get install poppler-utils`

### 多模态 AI 模型

使用 LM Studio 加载本地视觉模型（推荐 **qwen3.5-9b**）:

```bash
# 启动 API 服务器
lm-studio

# 在设置中：
# 1. 下载模型: qwen3.5-9b (或任意支持视觉的模型)
# 2. 启动服务器端口: 1234
```

## 快速开始

### CLI 工具

```bash
# 基础用法
wordparser parse document.docx -o output.md

# 禁用目录
wordparser parse document.docx -o output.md --no-toc

# 限制标题层级
wordparser parse document.docx --max-heading 3

# 配置多模态 API
wordparser parse document.docx --vision-url http://localhost:1234/v1

# 详细输出
wordparser parse document.docx -v
```

### BAT 启动器（Windows）

双击 `wordparser.bat`，拖入 .docx 文件即可解析，自动保存为同名 .md 文件。

### 编程接口

```python
from wordparser import parse_word_to_markdown, ParserConfig, MultimodalConfig, VisionModelConfig

# 基础用法
md_content, report = parse_word_to_markdown("document.docx")

# 保存到文件
md_content, report = parse_word_to_markdown("document.docx", "output.md")

# 自定义配置
config = ParserConfig(
    max_heading_level=6,
    generate_toc=True,
    enable_render_fallback=True,
    multimodal=MultimodalConfig(
        max_concurrent=4,
        model=VisionModelConfig(
            base_url="http://localhost:1234/v1",
            model="qwen3.5-9b",
        ),
    ),
)
md_content, report = parse_word_to_markdown("document.docx", config=config)

# 检查结果
print(f"解析成功: {report.success}")
print(f"标题数: {report.stats.total_headings}")
print(f"图片数: {report.stats.total_images}")
```

## 配置说明

### ParserConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_heading_level` | int | 6 | 最大标题级别（1-6） |
| `generate_toc` | bool | True | 是否生成目录 |
| `toc_position` | TOCPosition | AFTER_TITLE | 目录位置（BEFORE_TITLE/AFTER_TITLE） |
| `enable_render_fallback` | bool | True | 启用渲染降级 |
| `libreoffice_path` | str \| None | None | LibreOffice 路径（自动检测） |
| `encoding` | str | "utf-8" | 输出编码 |
| `include_header_footer` | bool | False | 包含页眉页脚 |
| `include_footnotes` | bool | False | 包含脚注（未实现） |
| `include_comments` | bool | False | 包含批注（未实现） |

### MultimodalConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_concurrent` | int | 6 | 最大并发数 |
| `batch_delay` | float | 0.1 | 批次延迟（秒） |
| `retry_on_failure` | bool | True | 失败重试 |
| `model` | VisionModelConfig | - | 视觉模型配置 |

### VisionModelConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_url` | str | "http://localhost:1234/v1" | API 地址 |
| `model` | str | "qwen3.5-4b" | 模型名称 |
| `api_key` | str \| None | None | API 密钥 |
| `timeout` | int | 600 | 超时时间（秒） |
| `temperature` | float | 0.0 | 温度参数 |

## 项目结构

```
Document_Parsing/
├── wordparser/                      # 核心库
│   ├── __init__.py                  # 主入口
│   ├── config.py                    # 配置类
│   ├── exceptions.py                # 异常体系
│   ├── core/
│   │   ├── models.py                # 数据模型
│   │   ├── report.py                # 解析报告
│   │   ├── parser.py                # 主解析器
│   │   ├── preprocessor.py          # 预处理
│   │   ├── structure.py             # 结构解析
│   │   ├── tables.py                # 表格处理
│   │   ├── images.py                # 图片处理
│   │   ├── chart_extractor.py       # Chart 提取
│   │   ├── smartart_extractor.py    # SmartArt 提取
│   │   ├── renderer.py              # 渲染器
│   │   ├── formulas.py              # 公式转换
│   │   ├── toc.py                   # 目录生成
│   │   └── postprocess.py           # 后处理
│   └── multimodal/
│       ├── client.py                # 视觉客户端
│       ├── parser.py                # 多模态解析器
│       ├── parallel.py              # 并行处理器
│       └── prompts.py               # Prompt 模板
├── wordparser_cli/                  # CLI 工具
│   └── main.py                      # typer app
├── openspec/                        # OpenSpec 规范
│   ├── specs/                       # 功能规范
│   │   └── wordparser-core/         # 核心功能规范
│   │       └── spec.md              # 详细功能规格
│   ├── changes/                     # 变更记录
│   └── config.yaml                  # OpenSpec 配置
├── tests/                           # 测试
├── docs/                            # 文档
├── wordparser.bat                   # Windows 启动器
├── pyproject.toml                   # 项目配置
└── README.md                        # 本文件
```

## 开发

### 运行测试

```bash
pytest

# 带覆盖率
pytest --cov=wordparser --cov-report=html
```

### 代码规范

- 语言：简体中文（注释、文档）
- 编码：UTF-8
- Python 版本：≥ 3.10

## 限制和已知问题

### 功能限制

1. **批注**: 配置项存在但未实现，当前版本不支持提取
2. **脚注**: 配置项存在但未实现，当前版本不支持提取
3. **样式**: 不保留原始文档的样式信息（字体、颜色等）
4. **宏**: 不支持 VBA 宏

### 已知问题

1. **复杂嵌套表格**: Markdown 重建可能不完美
2. **多模态依赖**: 依赖外部 API，可用性取决于模型服务
3. **格式丢失**: LibreOffice 转换可能丢失某些格式信息

---

## 常见问题

### Q: BAT 文件双击闪退？

A: 检查 BAT 文件编码是否为 GBK，确保在 Windows 环境下创建。

### Q: 多模态解析失败？

A: 确认 LM Studio API 服务器正在运行，模型名称正确。

### Q: .doc 文件解析失败？

A: 确认已安装 LibreOffice，或通过 `--libreoffice-path` 指定路径。

### Q: 如何调试解析过程？

A: 使用 CLI 的 `-v` 参数查看详细输出和统计信息。

## License

MIT License

---

*最后更新: 2026-04-27*
