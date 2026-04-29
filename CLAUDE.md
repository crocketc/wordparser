# CLAUDE.md 开发准则 - WordParser 项目

## 项目定位

**WordParser** 是一个 Python 实现的 Word 文档(.doc/.docx)转 Markdown 解析库。

- **当前版本**: v0.1.0
- **Python 版本**: ≥ 3.10
- **用户入口**: `wordparser.bat`（Windows 双击运行）
- **详细文档**: `README.md` 面向最终用户

---

## 1. 开发工作流

遵循 **研究 → 计划 → 实施 → 验证 → 提交** 五阶段流程。

### 分支策略
- `main`: 主分支，保持稳定
- 功能分支: `feat/xxx` 或 `fix/xxx`
- 提交前必须通过测试

### 代码审查
- 所有代码变更需经过自我审查
- 使用 `simplify` skill 检查代码质量

---

## 2. 代码规范

### 语言规范（绝对强制）
- **必须使用简体中文**编写所有注释、文档和用户交互内容
- 代码变量/函数名使用英文

### Python 编码规范
- 遵循 PEP 8
- 类型提示：公共 API 必须包含类型注解
- 文档字符串：Google 风格或 NumPy 风格

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
- 日志级别: DEBUG/INFO/WARNING/ERROR/CRITICAL
- 敏感信息不得写入日志

---

## 4. 测试规范

### 运行测试
```bash
# 所有测试
pytest

# 带覆盖率
pytest --cov=wordparser --cov-report=html

# 特定模块
pytest tests/test_chart_extractor.py -v
```

### 测试编写规范
- 单元测试: 测试单个函数/方法
- 集成测试: 测试模块间协作
- 使用 pytest fixture 管理测试数据
- 测试文件命名: `test_<module_name>.py`

### 测试覆盖率要求
- 核心模块覆盖率 ≥ 80%
- 新功能必须包含测试

---

## 5. 项目特定经验沉淀

### BAT 文件编码问题（重要！）

**问题**: 双击 BAT 文件闪退，命令被截断，中文乱码。

**根本原因**: 在 Unix/Linux 系统上使用 UTF-8 编码创建 BAT 文件，但 Windows CMD 期望 GBK 编码。

**解决方案**:
```python
with open('wordparser.bat', 'w', encoding='gbk', newline='\r\n') as f:
    f.write(bat_content)
```

### Edit 操作必须精确匹配

使用 Edit 工具时，`old_string` 必须包含完整的待替换代码块，不能只匹配方法签名。

### 外部 API 限流处理

多模态 API 调用需实现重试机制，失败时应有降级策略：
- 实现 `multimodal/config.py` 的重试配置
- 使用 `parallel.py` 的并发控制
- 失败后记录日志，不中断主流程

### LibreOffice 集成注意事项

- 路径检测: `renderer.py` 的 `_detect_libreoffice()`
- Windows/macOS/Linux 路径差异
- 退出 LibreOffice 进程: `--headless` + `--accept=...`

### 设计规格完整性检查

实现完成后需对照 `docs/` 下的设计规格逐项核对，确保所有公开 API 和配置项完整。

---

## 6. 关键文件快速索引

### 配置文件
- `pyproject.toml`: 项目依赖和元数据
- `wordparser/config.py`: 运行时配置类
- `wordparser/logger_config.py`: 日志配置

### 核心入口
- `wordparser/__init__.py`: 导出 `parse_word_to_markdown`
- `wordparser/core/parser.py`: `WordParser` 主类
- `wordparser_cli/main.py`: CLI 入口

### 测试
- `tests/`: 所有测试文件
- `tests/fixtures/`: 测试用文档

### 文档
- `README.md`: 用户文档
- `docs/`: 设计文档和实施计划

---

## 7. 全局规范引用

以下规范来自全局 CLAUDE.md，项目必须遵守：

### 语言规范
**必须使用简体中文**

### 图片/视觉处理规范
| 任务类型 | 优先工具 |
|---------|---------|
| OCR 文字识别 | `paddleocr-vl` Skill |
| 图像分析/理解 | `ms-qwen-vl` Skill |

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

## 8. Git 提交规范

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
feat: 添加批注提取功能

实现 Word 批注的提取和转换逻辑
```

---

## 9. 相关资源

### 设计文档
- `docs/2026-04-22-word-parser-design.md`: 原始设计规格
- `docs/2026-04-23-libreoffice-multimodal-design.md`: LibreOffice+多模态设计
- `docs/lessons-learned.md`: 经验教训

### OpenSpec 规范
- `openspec/specs/wordparser-core/spec.md`: 详细功能规格

---

*最后更新: 2026-04-29*
