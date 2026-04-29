# CLAUDE.md 开发准则 - WordParser 项目

## 项目概览

**WordParser** 是一个 Python 实现的 Word 文档(.doc/.docx)转 Markdown 解析库，提供编程接口和 CLI 工具。

### 核心能力

| 模块 | 功能描述 | 状态 |
|------|----------|------|
| 文档预处理 | 清理空白字符、统一编码、过滤控制符 | 已实现 |
| 标题结构化 | 1-6级标题映射、自动去除序号 | 已实现 |
| 正文格式化 | 段落、列表转换 | 已实现 |
| 表格处理 | 简单表格 MD 化 + 复杂表格 LLM/视觉降级 | 已实现 |
| 图片处理 | 零持久化多模态识别（qwen3.5-9b） | 已实现 |
| Chart 图表 | XML 数据提取 + LLM 语义理解 + 渲染降级 | 已实现 |
| SmartArt | XML 数据提取 + LLM 语义理解 + 渲染降级 | 已实现 |
| .doc 格式 | 自动检测并调用 LibreOffice 转换为 .docx | 已实现 |
| 公式处理 | OMML→LaTeX 转换 | 已实现 |
| 目录生成 | 自动生成带锚点的 MD 目录 | 已实现 |
| 后处理 | 格式规范化、换行统一 | 已实现 |

### 项目状态

- **当前版本**: v0.1.0
- **状态**: 生产就绪
- **用户入口**: `wordparser.bat`（Windows 双击运行）

---

## 开发规范

### 语言规范（绝对强制）

**必须使用简体中文**编写所有注释、文档和用户交互内容。

## 工作流程

**研究 → 计划 → 实施 → 验证 → 提交**

### 执行确认规范

**非危险操作无需确认**，直接执行即可。

需要确认的操作：
- 删除/修改重要系统文件
- 破坏性操作（`rm -rf`、`git push --force`）
- 涉及生产环境的变更

无需确认的操作：
- 读取文件/目录
- 创建新文件
- 查看信息类命令
- 非破坏性编辑操作

---

## 开发经验沉淀

### 1. BAT 文件编码问题（重要！）

**问题现象**：双击 BAT 文件闪退，命令被截断，中文乱码。

**根本原因**：在 Unix/Linux 系统上使用 UTF-8 编码创建 BAT 文件，但 Windows CMD 期望 GBK 编码。

**解决方案**：
```python
with open('wordparser.bat', 'w', encoding='gbk', newline='\r\n') as f:
    f.write(bat_content)
```

### 2. Edit 操作必须精确匹配

old_string 必须包含完整的待替换代码块，不能只匹配方法签名。

### 3. 设计规格完整性检查

实现完成后需对照设计规格逐项核对，确保所有公开 API 和配置项完整。

### 4. 外部 API 限流处理

多模态 API 调用需实现重试机制，失败时应有降级策略。

---

## 项目架构

### 文件结构

```
Document_Parsing/
├── wordparser/                      # 核心库
│   ├── __init__.py                  # 导出 parse_word_to_markdown
│   ├── config.py                    # ParserConfig, VisionModelConfig, MultimodalConfig
│   ├── exceptions.py                # 异常体系
│   ├── core/
│   │   ├── models.py                # 数据模型（含 ChartData, SmartArtData）
│   │   ├── report.py                # 解析报告
│   │   ├── parser.py                # WordParser 主解析器（编排全流程）
│   │   ├── preprocessor.py          # 文档预处理
│   │   ├── structure.py             # 标题/段落/列表解析
│   │   ├── tables.py                # 表格处理（简单+复杂）
│   │   ├── images.py                # 图片处理
│   │   ├── chart_extractor.py       # Chart XML 数据提取
│   │   ├── smartart_extractor.py    # SmartArt XML 数据提取
│   │   ├── renderer.py              # LibreOffice 渲染器（.doc 转换+页面渲染）
│   │   ├── formulas.py              # OMML→LaTeX
│   │   ├── toc.py                   # 目录生成
│   │   └── postprocess.py           # 后处理
│   └── multimodal/
│       ├── client.py                # OpenAI 兼容客户端（文本+图片）
│       ├── parser.py                # 多模态解析器（两级降级链路）
│       ├── parallel.py              # 并行处理器
│       └── prompts.py               # Prompt 模板
├── wordparser_cli/                  # CLI 工具
│   ├── __init__.py
│   └── main.py                      # typer app 入口
├── tests/                           # 测试
│   ├── test_chart_extractor.py
│   ├── test_smartart_extractor.py
│   ├── test_renderer.py
│   └── test_formula_processor.py
├── wordparser.bat                   # 用户入口（GBK 编码）
├── docs/                            # 文档
├── pyproject.toml
└── README.md
```

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 配置系统 | `config.py` | ParserConfig, MultimodalConfig, VisionModelConfig, TOCPosition |
| 异常体系 | `exceptions.py` | WordParserError, DocumentError, ContentProcessError 等 |
| 数据模型 | `core/models.py` | BlockType, TitleNode, ContentBlock, ParsedDocument, ChartData, SmartArtData |
| 主解析器 | `core/parser.py` | WordParser - 编排全流程（含 .doc 转换、chart/smartart/复杂表格） |
| Chart 提取 | `core/chart_extractor.py` | 从 ZIP 提取 chart XML，解析类型/标题/系列/数据 |
| SmartArt 提取 | `core/smartart_extractor.py` | 从 ZIP 提取 SmartArt XML，构建节点树 |
| LibreOffice 渲染 | `core/renderer.py` | .doc→.docx 转换、页面渲染为 PNG |
| 多模态解析 | `multimodal/parser.py` | 两级降级：XML+LLM → 渲染+视觉 → 失败标记 |
| 视觉客户端 | `multimodal/client.py` | OpenAI 兼容客户端，支持文本和图片通道 |
| 表格处理 | `core/tables.py` | 简单表格 MD 化 + 复杂表格数据提取 |

### 解析流程

```
输入文件（.doc / .docx）
    ↓
[.doc 自动转换] → LibreOffice 转为 .docx（如需）
    ↓
[预处理模块] → 清理文档
    ↓
[结构解析模块] → 提取标题/段落/列表
    ↓
[富内容处理模块]
    ├─ 嵌入图片 → 零持久化视觉模型 → 文字描述
    ├─ Chart → XML 提取 → LLM 语义理解 → Markdown
    ├─ SmartArt → XML 提取 → LLM 语义理解 → Markdown
    └─ 复杂表格 → 数据提取 → LLM 重建 → Markdown
    ↓
[目录生成模块] → 重建 MD 目录
    ↓
[后处理模块] → 格式规范化
    ↓
输出 .md
```

### 降级链路

```
XML + LLM 解析（默认，纯 python）
    ├─ 成功 → 输出结果
    └─ 失败 → enable_render_fallback=True?
                  ├─ 是 → LibreOffice 渲染 + 多模态识别
                  │         ├─ 成功 → 输出结果
                  │         └─ 失败 → 标记 [解析失败]，继续
                  └─ 否 → 标记，继续
```

---

## 编程接口

### 主入口函数

```python
from wordparser import parse_word_to_markdown

# 基础用法（支持 .doc 和 .docx）
md_content, report = parse_word_to_markdown("document.docx")

# 保存到文件
md_content, report = parse_word_to_markdown("document.docx", "output.md")

# 使用自定义配置
from wordparser.config import ParserConfig, MultimodalConfig

config = ParserConfig(
    max_heading_level=6,
    generate_toc=True,
    encoding="utf-8",
    enable_render_fallback=True,
    libreoffice_path=None,  # 自动检测
    multimodal=MultimodalConfig(
        enabled=False,  # 关闭多模态 AI 解析，不调用模型
    ),
)
md_content, report = parse_word_to_markdown("document.docx", config=config)
```

### 返回值

- `md_content`: Markdown 文本（str）
- `report`: ParseReport 对象
  - `success`: 是否成功
  - `output_path`: 输出文件路径
  - `errors`: 错误列表
  - `stats`: 统计信息（标题数、段落数、表格数、图片数等）

---

## CLI 工具

### 使用方式

```bash
# 基础用法（支持 .doc 和 .docx）
wordparser.bat parse document.docx -o output.md

# 禁用目录
wordparser.bat parse document.docx -o output.md --no-toc

# 限制标题层级
wordparser.bat parse document.docx -o output.md --max-heading 3

# 详细输出
wordparser.bat parse document.docx -o output.md -v

# 关闭多模态 AI 解析（不调用模型，图片/图表显示为占位符）
wordparser.bat parse document.docx --no-multimodal

# 配置多模态
wordparser.bat parse document.docx --vision-url http://localhost:1234/v1

# 禁用渲染降级
wordparser.bat parse document.docx --no-render-fallback

# 指定 LibreOffice 路径
wordparser.bat parse document.docx --libreoffice-path "C:\Program Files\LibreOffice\program\soffice.exe"
```

### BAT 启动器

用户直接双击 `wordparser.bat`，拖入 .docx 文件即可解析，自动保存为同名 .md 文件。

---

## 待实现功能

1. **高级特性**：脚注处理、批注处理、页眉页脚处理

---

## 依赖项

### Python 依赖

```
python-docx>=1.0     # Word 文档解析
httpx>=0.24          # HTTP 客户端（多模态 API）
pydantic>=2.0        # 数据验证
pdf2image>=1.16      # PDF 转图片（渲染降级路径）
lxml>=4.9            # XML 解析
Pillow>=10.0         # 图片处理
openpyxl>=3.0        # 读取 Chart 内嵌 Excel
openai               # OpenAI SDK（视觉模型调用）
```

### CLI 依赖

```
typer>=0.9           # CLI 框架
rich>=13.0           # 终端输出美化
```

### 系统依赖（可选）

- **LibreOffice**：.doc 格式转换 + 渲染降级路径
- **Poppler**：pdf2image 后端，PDF 转图片

---

## 多模态配置

### 本地 LM Studio 配置

默认配置使用本地 LM Studio API，全模态模型 qwen3.5-9b。

所有配置项默认值定义在 `wordparser/config.py`，CLI 自动同步这些默认值。

```python
from wordparser.config import VisionModelConfig, MultimodalConfig, ParserConfig

# 使用默认配置（见 config.py）
config = ParserConfig()

# 关闭多模态 AI 解析
config = ParserConfig(
    multimodal=MultimodalConfig(enabled=False)
)

# 或覆盖部分配置
config = ParserConfig(
    multimodal=MultimodalConfig(
        enabled=True,  # 是否启用多模态解析（默认: True）
        max_concurrent=6,  # 最大并发请求数
        model=VisionModelConfig(
            base_url="http://localhost:1234/v1",
        ),
    ),
)
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | True | 是否启用多模态 AI 解析，False 时跳过所有模型调用 |
| `max_concurrent` | int | 6 | 最大并发请求数 |
| `model.base_url` | str | http://localhost:1234/v1 | 多模态 API 服务地址 |
| `model.model` | str | qwen3.5-4b | 模型名称 |

### 可用模型

- **qwen3.5-9b**（推荐默认，全模态模型，文本+图片）
- 其他 LM Studio 支持的视觉模型

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_chart_extractor.py -v
pytest tests/test_smartart_extractor.py -v
pytest tests/test_renderer.py -v
```

### 测试覆盖

| 测试文件 | 测试数 | 覆盖模块 |
|---------|--------|---------|
| `test_chart_extractor.py` | 5 | Chart XML 解析、类型检测、格式化 |
| `test_smartart_extractor.py` | 3 | SmartArt 节点树构建、空数据处理 |
| `test_renderer.py` | 3 | LibreOffice 检测、.doc 识别 |
| `test_formula_processor.py` | 16 | OMML → LaTeX 转换、公式格式化 |

---

## Git 提交规范

### 提交信息格式

```
<type>: <description>

[optional body]
```

### 类型（type）

- `feat`: 新功能
- `fix`: 修复 bug
- `refactor`: 重构
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具相关

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

---

## 相关文档

- **原始设计规格**: `docs/2026-04-22-word-parser-design.md`
- **原始实施计划**: `docs/2026-04-22-word-parser-plan.md`
- **LibreOffice+多模态设计**: `docs/2026-04-23-libreoffice-multimodal-design.md`
- **LibreOffice+多模态实施计划**: `docs/2026-04-23-libreoffice-multimodal-plan.md`
- **经验教训**: `docs/lessons-learned.md`

---

*最后更新: 2026-04-24*
