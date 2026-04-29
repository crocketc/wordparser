# CLAUDE.md 开发准则 - WordParser 项目

## 必须加载的外部规范

开发任务开始前，必须读取并遵循：
- `C:\Users\crock\.claude\DEVELOPMENT.md`（开发铁律、Skill 架构、任务分流、经验沉淀）

---

## 项目定位

**WordParser** 是一个 Python 实现的 Word 文档(.doc/.docx)转 Markdown 解析库。

- **当前版本**: v0.1.0
- **Python 版本**: ≥ 3.10
- **用户入口**: `wordparser.bat`（Windows 双击运行）
- **详细文档**: `README.md` 面向最终用户

---

## 1. OpenSpec 配置

项目已配置 OpenSpec，变更流程遵循 DEVELOPMENT.md 中的任务分级规范。

- 规范目录: `openspec/specs/wordparser-core/spec.md`
- 变更目录: `openspec/changes/`

### 分支策略
- `main`: 主分支，保持稳定
- 功能分支: `feat/xxx` 或 `fix/xxx`
- 大任务使用 Git Worktree 隔离

---

## 2. 代码规范

### Python 编码规范
- 遵循 PEP 8
- 类型提示：公共 API 必须包含类型注解
- 文档字符串：Google 风格

### 命名约定
- 模块名: `lowercase_with_underscores`
- 类名: `CapitalizedWords`
- 函数/方法: `lowercase_with_underscores`
- 常量: `UPPERCASE_WITH_UNDERSCORES`
- 私有成员: `_leading_underscore`

### 注释规范
```python
def parse_document(file_path: str) -> ParsedDocument:
    """解析 Word 文档。

    Args:
        file_path: 文档文件路径

    Returns:
        解析后的文档对象

    Raises:
        DocumentError: 文档格式不支持或损坏
    """
```

---

## 3. 架构原则

### 核心模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| 配置系统 | `config.py` | 所有配置类定义 |
| 异常体系 | `exceptions.py` | 异常类定义 |
| 数据模型 | `core/models.py` | 数据结构定义 |
| 主解析器 | `core/parser.py` | 编排全流程，不实现具体解析逻辑 |
| 结构解析 | `core/structure.py` | 标题/段落/列表识别 |
| 表格处理 | `core/tables.py` | 简单表格 MD 化 + 复杂表格数据提取 |
| Chart 提取 | `core/chart_extractor.py` | XML 数据提取 |
| SmartArt 提取 | `core/smartart_extractor.py` | XML 数据提取 |
| LibreOffice | `core/renderer.py` | .doc 转换 + 页面渲染 |
| 多模态解析 | `multimodal/parser.py` | 两级降级链路 |
| 视觉客户端 | `multimodal/client.py` | OpenAI 兼容客户端 |

### 依赖方向
- `core/parser.py` 依赖所有其他模块
- `core/` 模块不应依赖 `multimodal/`
- `multimodal/` 可依赖 `core/` 的数据模型

### 错误处理策略
- 使用项目定义的异常类（`exceptions.py`）
- 外部 API 调用必须包含重试机制
- 失败时记录详细日志

### 日志规范
- 使用 ELK 友好的 JSON 格式
- 配置文件: `logger_config.py`
- 敏感信息不得写入日志

---

## 4. 测试规范

### 运行测试
```bash
pytest                                    # 所有测试
pytest --cov=wordparser --cov-report=html # 带覆盖率
pytest tests/test_chart_extractor.py -v   # 特定模块
```

### 测试要求
- 核心模块覆盖率 ≥ 80%
- 新功能必须包含测试
- 测试文件命名: `test_<module_name>.py`
- 使用 pytest fixture 管理测试数据

---

## 5. 开发经验沉淀

### BAT 文件编码问题（重要！）

**问题**: 双击 BAT 文件闪退，中文乱码。

**根因**: Unix/Linux 系统用 UTF-8 编码创建 BAT 文件，但 Windows CMD 期望 GBK。

**解决方案**:
```python
with open('wordparser.bat', 'w', encoding='gbk', newline='\r\n') as f:
    f.write(bat_content)
```

### 外部 API 限流处理

多模态 API 调用需实现重试机制，失败时应有降级策略：
- 使用 `parallel.py` 的并发控制
- 失败后记录日志，不中断主流程

### LibreOffice 集成注意事项

- 路径检测: `renderer.py` 的 `_detect_libreoffice()`
- Windows/macOS/Linux 路径差异
- 退出 LibreOffice 进程: `--headless` + `--accept=...`

---

## 6. 关键文件索引

| 类型 | 文件 | 说明 |
|------|------|------|
| 配置 | `pyproject.toml` | 项目依赖和元数据 |
| 配置 | `wordparser/config.py` | 运行时配置类 |
| 配置 | `wordparser/logger_config.py` | 日志配置 |
| 入口 | `wordparser/__init__.py` | 导出 `parse_word_to_markdown` |
| 入口 | `wordparser/core/parser.py` | `WordParser` 主类 |
| 入口 | `wordparser_cli/main.py` | CLI 入口 |
| 测试 | `tests/` | 所有测试文件 |
| 测试 | `tests/fixtures/` | 测试用文档 |

---

## 7. Git 提交规范

```
<type>: <description>

[optional body]
```

类型：`feat` | `fix` | `refactor` | `docs` | `test` | `chore`

---

## 8. 相关资源

- `docs/2026-04-22-word-parser-design.md`: 原始设计规格
- `docs/2026-04-23-libreoffice-multimodal-design.md`: LibreOffice+多模态设计
- `docs/lessons-learned.md`: 经验教训
- `openspec/specs/wordparser-core/spec.md`: 详细功能规格

---

*最后更新: 2026-04-29*
