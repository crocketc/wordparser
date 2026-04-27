# WordParser 核心功能规范

## 概述

WordParser 是一个 Python 实现的 Word 文档（.doc/.docx）转 Markdown 解析库，提供编程接口和 CLI 工具。

**版本**: v0.1.0
**状态**: 生产就绪
**所有者**: Document Parsing Team

---

## EXISTING 现有功能

### 功能: 文档解析

将 Word 文档解析为 Markdown 格式，保留文档结构和格式。

#### 场景: 解析 .docx 文件

- **WHEN** 用户提供一个有效的 .docx 文件路径
- **THEN** 系统应成功解析文档并返回 Markdown 内容
- **AND** 返回解析报告包含统计信息（标题数、段落数、表格数、图片数等）
- **AND** Markdown 内容保留原始文档的标题层级结构

#### 场景: 自动转换 .doc 文件

- **WHEN** 用户提供一个 .doc 文件路径
- **THEN** 系统应自动检测文件格式为 .doc
- **AND** 使用 LibreOffice 将其转换为 .docx 后续处理
- **AND** 转换失败时抛出 `UnsupportedFormatError`

#### 场景: 文档不存在

- **WHEN** 提供的文件路径不存在
- **THEN** 系统应抛出 `DocumentError`
- **AND** 错误信息明确指出文件不存在

#### 场景: 文档加密

- **WHEN** 提供的文档受密码保护
- **THEN** 系统应抛出 `DocumentEncryptedError`
- **AND** 错误信息提示文档需要密码

---

### 功能: 预处理

在解析前清理文档，移除无关内容和规范化格式。

#### 场景: 移除空白段落

- **WHEN** 文档包含连续的空白段落
- **THEN** 系统应移除所有空白段落
- **AND** 保留有内容的段落

#### 场景: 清理控制字符

- **WHEN** 文档包含控制字符（如 \x00, \x01 等）
- **THEN** 系统应移除所有控制字符
- **AND** 保留有效的文本内容

#### 场景: 规范化空白字符

- **WHEN** 文档包含不规范的空白字符（如全角空格）
- **THEN** 系统应将其转换为标准空格
- **AND** 保持文本的可读性

---

### 功能: 结构解析

提取文档的结构化信息，包括标题、段落和列表。

#### 场景: 标题层级识别

- **WHEN** 文档包含 1-6 级标题
- **THEN** 系统应正确识别标题层级
- **AND** 将其转换为 Markdown 对应的 # 级别

#### 场景: 自动去除标题序号

- **WHEN** 标题包含自动序号（如 "1.1 章节"）
- **THEN** 系统应自动移除序号
- **AND** 保留标题的文本内容

#### 场景: 列表转换

- **WHEN** 文档包含有序或无序列表
- **THEN** 系统应将其转换为 Markdown 列表格式
- **AND** 保持列表的嵌套层级

---

### 功能: 表格处理

将表格转换为 Markdown 格式，复杂表格支持数据提取和多模态重建。

#### 场景: 简单表格转换

- **WHEN** 表格结构简单（无合并单元格）
- **THEN** 系统应将其转换为 Markdown 表格格式
- **AND** 保留表头和数据行

#### 场景: 复杂表格数据提取

- **WHEN** 表格结构复杂（包含合并单元格）
- **THEN** 系统应提取表格的所有文本数据
- **AND** 调用多模态模型重建 Markdown 表格
- **AND** 模型调用失败时使用渲染降级路径

#### 场景: 表格解析失败

- **WHEN** 表格解析失败且渲染降级被禁用
- **THEN** 系统应在 Markdown 中标记 `[表格解析失败]`
- **AND** 继续处理后续内容

---

### 功能: 图片处理

提取图片并使用多模态模型生成文字描述。

#### 场景: 图片提取和识别

- **WHEN** 文档包含嵌入图片
- **THEN** 系统应提取图片二进制数据
- **AND** 调用多模态模型生成图片描述
- **AND** 将描述以 Markdown 格式插入文档

#### 场景: 图片识别失败

- **WHEN** 多模态模型调用失败
- **AND** `enable_render_fallback=True`
- **THEN** 系统应降级到 LibreOffice 渲染 + 多模态识别
- **AND** 仍然失败时标记 `[图片解析失败]`

#### 场景: 图片识别失败且禁用降级

- **WHEN** 多模态模型调用失败
- **AND** `enable_render_fallback=False`
- **THEN** 系统应直接标记 `[图片解析失败]`
- **AND** 不尝试渲染降级

---

### 功能: Chart 图表处理

提取 Chart XML 数据，使用 LLM 生成语义描述并渲染。

#### 场景: Chart XML 提取

- **WHEN** 文档包含 Chart 对象
- **THEN** 系统应从文档 ZIP 结构中提取 chart XML
- **AND** 解析图表类型、标题、系列数据

#### 场景: Chart 语义理解

- **WHEN** Chart XML 数据提取成功
- **THEN** 系统应调用 LLM 生成图表语义描述
- **AND** 将描述以 Markdown 格式插入文档

#### 场景: Chart 解析失败

- **WHEN** Chart XML 提取失败
- **AND** `enable_render_fallback=True`
- **THEN** 系统应降级到 LibreOffice 渲染 + 多模态识别
- **AND** 仍然失败时标记 `[图表解析失败]`

---

### 功能: SmartArt 处理

提取 SmartArt XML 数据，使用 LLM 生成语义描述并渲染。

#### 场景: SmartArt XML 提取

- **WHEN** 文档包含 SmartArt 对象
- **THEN** 系统应从文档 ZIP 结构中提取 SmartArt XML
- **AND** 构建节点树结构

#### 场景: SmartArt 语义理解

- **WHEN** SmartArt XML 数据提取成功
- **THEN** 系统应调用 LLM 生成 SmartArt 语义描述
- **AND** 将描述以 Markdown 格式插入文档

#### 场景: SmartArt 解析失败

- **WHEN** SmartArt XML 提取失败
- **AND** `enable_render_fallback=True`
- **THEN** 系统应降级到 LibreOffice 渲染 + 多模态识别
- **AND** 仍然失败时标记 `[SmartArt 解析失败]`

---

### 功能: 公式处理

将 OMML 格式的公式转换为 LaTeX 格式。

#### 场景: OMML 转 LaTeX

- **WHEN** 文档包含 OMML 格式公式
- **THEN** 系统应将其转换为 LaTeX 格式
- **AND** 使用 `$...$` 行内公式或 `$$...$$` 独立公式格式

#### 场景: 公式分隔符处理

- **WHEN** 公式内容包含公式分隔符（如 ∂、∆ 等）
- **THEN** 系统应将其转换为 LaTeX 对应的命令
- **AND** 确保转换后的公式可正确渲染

---

### 功能: 目录生成

自动生成带锚点的 Markdown 目录。

#### 场景: 生成目录

- **WHEN** `generate_toc=True`
- **THEN** 系统应生成完整的 Markdown 目录
- **AND** 每个目录项包含锚点链接

#### 场景: 目录位置控制

- **WHEN** `toc_position=BEFORE_TITLE`
- **THEN** 目录应插入在文档标题之前
- **WHEN** `toc_position=AFTER_TITLE`
- **THEN** 目录应插入在文档标题之后

#### 场景: 禁用目录

- **WHEN** `generate_toc=False`
- **THEN** 系统不生成目录
- **AND** 文档直接从标题开始

---

### 功能: 后处理

规范化 Markdown 格式，统一换行和格式。

#### 场景: 换行规范化

- **WHEN** Markdown 内容包含不一致的换行
- **THEN** 系统应统一换行格式
- **AND** 确保段落之间只有一个空行

#### 场景: 代码块保护

- **WHEN** Markdown 内容包含代码块
- **THEN** 系统应避免在代码块内插入换行
- **AND** 保持代码块的完整性

---

### 功能: 配置管理

提供灵活的配置选项控制解析行为。

#### 场景: 使用默认配置

- **WHEN** 用户不提供配置
- **THEN** 系统应使用 `ParserConfig` 的默认值
- **AND** 所有配置项使用预定义默认值

#### 场景: 自定义配置

- **WHEN** 用户提供自定义 `ParserConfig`
- **THEN** 系统应使用用户指定的配置
- **AND** 未指定的配置项使用默认值

#### 场景: 多模态配置

- **WHEN** 用户提供自定义 `MultimodalConfig`
- **THEN** 系统应使用指定的 API 地址、模型名称和并发数
- **AND** 按照配置调用多模态 API

---

### 功能: 编程接口

提供 Python API 供开发者调用。

#### 场景: 基础解析

- **WHEN** 调用 `parse_word_to_markdown(docx_path)`
- **THEN** 系统应返回 `(markdown_content, report)` 元组
- **AND** `markdown_content` 是解析后的 Markdown 文本
- **AND** `report` 是包含解析统计和错误的 `ParseReport` 对象

#### 场景: 保存到文件

- **WHEN** 调用 `parse_word_to_markdown(docx_path, output_path)`
- **THEN** 系统应将 Markdown 内容保存到指定文件
- **AND** `report.output_path` 包含输出文件路径

---

### 功能: CLI 工具

提供命令行工具供终端用户使用。

#### 场景: 基础解析

- **WHEN** 执行 `wordparser parse document.docx`
- **THEN** 系统应将 Markdown 输出到 stdout
- **AND** 解析失败时返回退出码 1

#### 场景: 保存到文件

- **WHEN** 执行 `wordparser parse document.docx -o output.md`
- **THEN** 系统应将 Markdown 保存到指定文件
- **AND** 显示保存路径（使用 `--verbose`）

#### 场景: 禁用目录

- **WHEN** 执行 `wordparser parse document.docx --no-toc`
- **THEN** 系统不生成目录
- **AND** 直接输出文档内容

#### 场景: 限制标题层级

- **WHEN** 执行 `wordparser parse document.docx --max-heading 3`
- **THEN** 系统只解析 1-3 级标题
- **AND** 更深层级的标题转换为普通段落

#### 场景: 详细输出

- **WHEN** 执行 `wordparser parse document.docx -v`
- **THEN** 系统应显示解析进度和统计信息
- **AND** 显示解析错误（如有）

#### 场景: 自定义多模态配置

- **WHEN** 执行 `wordparser parse document.docx --vision-url http://localhost:1234/v1`
- **THEN** 系统应使用指定的 API 地址
- **AND** 调用多模态模型

---

### 功能: 异常处理

提供明确的异常类型供错误处理。

#### 场景: 文档错误

- **WHEN** 文档不存在、格式不支持或损坏
- **THEN** 系统应抛出 `DocumentError` 或其子类
- **AND** 错误信息明确说明问题原因

#### 场景: 内容处理错误

- **WHEN** 内容处理失败（表格、图片、多模态 API）
- **THEN** 系统应抛出 `ContentProcessError` 或其子类
- **AND** 错误记录到报告但不中断解析（除非致命）

---

## 配置项规格

### ParserConfig

| 配置项 | 类型 | 默认值 | 描述 |
|-------|------|--------|------|
| `max_heading_level` | int | 6 | 最大解析的标题层级（1-6） |
| `encoding` | str | "utf-8" | 输出 Markdown 的编码 |
| `multimodal` | MultimodalConfig | None | 多模态配置 |
| `libreoffice_path` | str\|None | None | LibreOffice 可执行文件路径 |
| `enable_render_fallback` | bool | True | 是否启用渲染降级 |
| `generate_toc` | bool | True | 是否生成目录 |
| `toc_position` | TOCPosition | AFTER_TITLE | 目录位置 |
| `include_header_footer` | bool | False | 是否包含页眉页脚 |
| `include_comments` | bool | False | 是否包含批注 |
| `include_footnotes` | bool | False | 是否包含脚注 |

### MultimodalConfig

| 配置项 | 类型 | 默认值 | 描述 |
|-------|------|--------|------|
| `max_concurrent` | int | 6 | 最大并发请求数 |
| `batch_delay` | float | 0.1 | 批处理延迟（秒） |
| `retry_on_failure` | bool | True | 失败时是否重试 |
| `model` | VisionModelConfig | 默认 | 视觉模型配置 |

### VisionModelConfig

| 配置项 | 类型 | 默认值 | 描述 |
|-------|------|--------|------|
| `base_url` | str | "http://localhost:1234/v1" | API 基础地址 |
| `api_key` | str\|None | None | API 密钥 |
| `model` | str | "qwen3.5-4b" | 模型名称 |
| `timeout` | int | 600 | 请求超时时间（秒） |
| `temperature` | float | 0.0 | 采样温度 |

---

## 解析报告规格

### ParseReport

| 字段 | 类型 | 描述 |
|------|------|------|
| `success` | bool | 是否成功解析 |
| `output_path` | Path\|None | 输出文件路径 |
| `errors` | list[ErrorEntry] | 错误列表 |
| `stats` | ParseStats | 解析统计 |

### ParseStats

| 字段 | 类型 | 描述 |
|------|------|------|
| `total_headings` | int | 标题总数 |
| `total_paragraphs` | int | 段落总数 |
| `total_tables` | int | 表格总数 |
| `total_images` | int | 图片总数 |
| `total_charts` | int | 图表总数 |
| `total_smartarts` | int | SmartArt 总数 |
| `total_formulas` | int | 公式总数 |

---

## 外部依赖

### 必需依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `python-docx` | >=1.0 | Word 文档解析 |
| `httpx` | >=0.24 | HTTP 客户端 |
| `pydantic` | >=2.0 | 数据验证 |
| `lxml` | >=4.9 | XML 解析 |
| `Pillow` | >=10.0 | 图片处理 |
| `openpyxl` | >=3.0 | 读取 Chart 内嵌 Excel |
| `openai` | 最新 | OpenAI SDK |

### 可选依赖

| 依赖 | 用途 |
|------|------|
| `LibreOffice` | .doc 格式转换 + 渲染降级 |
| `Poppler` | PDF 转图片（渲染降级后端） |
| `typer` | CLI 框架 |
| `rich` | 终端输出美化 |

---

## 非功能需求

### 性能

- 支持多模态 API 并发调用（默认 6 并发）
- 复杂文档（>100 页）解析时间 <60 秒
- 内存占用 <500MB

### 可靠性

- 多模态 API 调用失败自动重试
- 支持渲染降级路径
- 部分内容解析失败不影响整体流程

### 可扩展性

- 支持自定义配置
- 支持插件式处理器扩展
- API 设计支持新功能添加

---

## 限制和已知问题

### 限制

1. **页眉页脚**: 当前版本不支持页眉页脚提取（配置项存在但未实现）
2. **批注**: 当前版本不支持批注提取（配置项存在但未实现）
3. **脚注**: 当前版本不支持脚注提取（配置项存在但未实现）
4. **样式**: 不保留原始文档的样式信息（字体、颜色等）
5. **宏**: 不支持 VBA 宏

### 已知问题

1. 复杂嵌套表格的 Markdown 重建可能不完美
2. 多模态模型依赖外部 API，可用性取决于模型服务
3. LibreOffice 转换可能丢失某些格式信息

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-04-22 | 初始发布 |
