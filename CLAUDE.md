# CLAUDE.md 开发准则 - WordParser 项目

## 项目概览

**WordParser** 是一个 Python 实现的 Word 文档(.docx)转 Markdown 解析库，提供编程接口和 CLI 工具。

### 核心能力

| 模块 | 功能描述 |
|------|----------|
| 文档预处理 | 清理空白字符、统一编码、过滤控制符 |
| 标题结构化 | 1-6级标题映射、自动去除序号 |
| 正文格式化 | 段落、列表转换 |
| 表格处理 | 简单表格 MD 化 |
| 图片处理 | 提取图片（多模态识别待实现） |
| 公式处理 | OMML→LaTeX 转换（待实现） |
| 目录生成 | 自动生成带锚点的 MD 目录 |
| 后处理 | 格式规范化、换行统一 |

### 项目状态

- **当前版本**: v0.1.0
- **状态**: 生产就绪（核心功能可用）
- **用户入口**: `wordparser.bat`（Windows 双击运行）

---

## 开发规范

### 语言规范（绝对强制）

**必须使用简体中文**编写所有注释、文档和用户交互内容。

### 网络检索规范

进行网络搜索时使用 `tavily-mcp` 或 `brave-search` 搜索工具。

### 图片/视觉处理规范

| 任务类型 | 优先工具 |
|---------|---------|
| OCR 文字识别 | `paddleocr-vl` Skill |
| 图像分析/理解 | `ms-qwen-vl` Skill |
| 通用图像分析 | `mcp__zai-mcp-server__analyze_image` |

---

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
# 使用 GBK 编码和 CRLF 换行符创建 BAT 文件
with open('wordparser.bat', 'w', encoding='gbk', newline='\r\n') as f:
    f.write(bat_content)
```

**最佳实践**：
- BAT 文件避免使用中文提示
- 必须使用 GBK 编码（Windows 系统默认）
- 使用 CRLF 换行符（`\r\n`）
- 在目标平台上测试

### 2. Edit 操作必须精确匹配

**错误示例**：
```python
# old_string 仅匹配方法签名，导致方法体被删除
old_string = "def _normalize_whitespace(self, doc: Document) -> None:"
```

**正确做法**：
```python
# old_string 必须包含完整的待替换代码块
old_string = """def _normalize_whitespace(self, doc: Document) -> None:
    for para in doc.paragraphs:
        for run in para.runs:
            run.text = run.text.strip()"""
```

### 3. 设计规格完整性检查

实现完成后需对照设计规格逐项核对，确保：
- 所有公开 API 都已实现
- 编程接口符合规格定义
- 配置项完整

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
│   │   ├── models.py                # 数据模型
│   │   ├── report.py                # 解析报告
│   │   ├── parser.py                # WordParser 主解析器
│   │   ├── preprocessor.py          # 文档预处理
│   │   ├── structure.py             # 标题/段落/列表解析
│   │   ├── tables.py                # 表格处理
│   │   ├── images.py                # 图片处理
│   │   ├── formulas.py              # OMML→LaTeX
│   │   ├── toc.py                   # 目录生成
│   │   └── postprocess.py           # 后处理
│   └── multimodal/
│       ├── client.py                # OpenAI 兼容客户端
│       ├── parser.py                # 多模态解析器
│       ├── parallel.py              # 并行处理器
│       └── prompts.py               # Prompt 模板
├── wordparser_cli/                  # CLI 工具
│   ├── __init__.py
│   └── main.py                      # typer app 入口
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
| 数据模型 | `core/models.py` | BlockType, TitleNode, ContentBlock, ParsedDocument |
| 解析报告 | `core/report.py` | ParseReport, ParseError, ParseStats |
| 主解析器 | `core/parser.py` | WordParser - 编排整个解析流程 |
| 预处理 | `core/preprocessor.py` | Preprocessor - 清理文档 |
| 结构解析 | `core/structure.py` | StructureParser - 标题/段落/列表 |
| 表格处理 | `core/tables.py` | TableProcessor - 表格转 Markdown |
| 后处理 | `core/postprocess.py` | PostProcessor - 格式规范化 |
| 目录生成 | `core/toc.py` | TOCGenerator - 生成目录 |

### 解析流程

```
输入 .docx
    ↓
[预处理模块] → 清理文档
    ↓
[结构解析模块] → 提取标题/段落/列表
    ↓
[富内容处理模块] → 表格/图片/公式
    ↓
[目录生成模块] → 重建 MD 目录
    ↓
[后处理模块] → 格式规范化
    ↓
输出 .md
```

---

## 编程接口

### 主入口函数

```python
from wordparser import parse_word_to_markdown

# 基础用法
md_content, report = parse_word_to_markdown("document.docx")

# 保存到文件
md_content, report = parse_word_to_markdown("document.docx", "output.md")

# 使用自定义配置
from wordparser.config import ParserConfig

config = ParserConfig(
    max_heading_level=6,
    generate_toc=True,
    encoding="utf-8",
)
md_content, report = parse_word_to_markdown("document.docx", config=config)
```

### 返回值

- `md_content`: Markdown 文本（str）
- `report`: ParseReport 对象
  - `success`: 是否成功
  - `output_path`: 输出文件路径
  - `errors`: 错误列表
  - `stats`: 统计信息（标题数、段落数、表格数等）

---

## CLI 工具

### 使用方式

```bash
# 基础用法
python -m wordparser_cli parse document.docx -o output.md

# 禁用目录
python -m wordparser_cli parse document.docx -o output.md --no-toc

# 限制标题层级
python -m wordparser_cli parse document.docx -o output.md --max-heading 3

# 详细输出
python -m wordparser_cli parse document.docx -o output.md -v
```

### BAT 启动器

用户直接双击 `wordparser.bat`，拖入 .docx 文件即可解析，自动保存为同名 .md 文件。

---

## 待实现功能

根据设计规格，以下功能待实现：

1. **多模态集成**：
   - 图片多模态识别（需要视觉模型 API）
   - 复杂表格视觉识别
   - Chart 图表识别
   - SmartArt 图形识别

2. **LibreOffice 渲染器**：
   - Word 元素渲染为图片
   - 用于复杂表格、图表、SmartArt 的渲染

3. **公式处理**：
   - OMML → LaTeX 转换的完整实现

4. **高级特性**：
   - 脚注处理
   - 批注处理
   - 页眉页脚处理

---

## 依赖项

### Python 依赖

```
python-docx>=1.0     # Word 文档解析
httpx>=0.24          # HTTP 客户端（多模态 API）
pydantic>=2.0        # 数据验证
pdf2image>=1.16      # PDF 转图片
lxml>=4.9            # XML 解析
Pillow>=10.0         # 图片处理
```

### CLI 依赖

```
typer>=0.9           # CLI 框架
rich>=13.0           # 终端输出美化
```

### 系统依赖

- **LibreOffice**：Word 元素渲染为图片（可选，用于高级功能）
- **Poppler**：pdf2image 后端，PDF 转图片（可选）

---

## 多模态配置

### 本地 LM Studio 配置

默认配置使用本地 LM Studio API：

```python
from wordparser.config import VisionModelConfig, MultimodalConfig, ParserConfig

config = ParserConfig(
    multimodal=MultimodalConfig(
        max_concurrent=4,
        model=VisionModelConfig(
            base_url="http://localhost:1234/v1",
            model="qwen3.5-9b",  # 或其他可用模型
            timeout=60,
        ),
    ),
)
```

### 可用模型

- qwen3.5-9b（推荐）
- qwen3-vl-8b-instruct
- 其他 LM Studio 支持的视觉模型

---

## 测试

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_parser.py -v

# 查看覆盖率
pytest --cov=wordparser
```

### 测试文件位置

测试基础设施已移除，如需重新添加测试，参考 `docs/2026-04-22-word-parser-plan.md` 中的测试规范。

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

### 示例

```
feat: add TOCGenerator - markdown TOC with anchor links
fix: restore _normalize_whitespace implementation
docs: update CLAUDE.md with project guidelines
```

---

## 常见问题

### Q: BAT 文件双击闪退？

A: 检查 BAT 文件编码是否为 GBK，确保在 Windows 环境下创建。

### Q: 多模态解析失败？

A: 确认 LM Studio API 服务器正在运行，模型名称正确。

### Q: 如何调试解析过程？

A: 使用 CLI 的 `-v` 参数查看详细输出和统计信息。

---

## 相关文档

- **设计规格**: `docs/2026-04-22-word-parser-design.md`
- **实施计划**: `docs/2026-04-22-word-parser-plan.md`
- **经验教训**: `docs/lessons-learned.md`

---

*最后更新: 2026-04-22*
