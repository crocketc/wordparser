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

### OpenSpec 驱动开发

项目已配置 OpenSpec（`openspec/`），变更管理遵循规范驱动流程：

| 变更级别 | 触发条件 | 流程 |
|---------|---------|------|
| **只读** | 分析、解释、代码阅读 | 直接处理；需求模糊时先 `/opsx:explore` 梳理 |
| **轻量** | 单文件修改、明确 bug 修复、配置调整 | `/opsx:propose` → 实现 → 验证 → `/opsx:verify` → `/opsx:archive` |
| **中** | 多文件但边界清晰、新功能 | `/opsx:new` + `/opsx:ff` → brainstorming → 实现 → `/opsx:verify` → `/opsx:archive` |
| **大** | 跨模块、新架构、公共 API 变更 | `/opsx:explore` → `/opsx:new` → `/opsx:continue` → brainstorming → writing-plans → executing-plans → `/opsx:verify` → `/opsx:archive` |

### 强制铁律（项目适配版）

1. **作者不自审** — 代码审查必须为独立上下文，不自审自修改的代码

2. **无证据不称"完成"** — 声明完成前必须满足：
   - ✅ 测试通过（`pytest`）
   - ✅ 无类型错误（如有类型检查）
   - 四个条件缺一不可

3. **模糊先澄清** — 任何模糊需求必须先执行分析，再创建变更提案

4. **危险命令先确认** — `rm -rf`、`DROP TABLE`、`force-push`、`git reset --hard` 等操作前必须明确风险与回滚方案

5. **一个变更一个逻辑单元** — 非极简修改必须通过 `/opsx:propose` 或 `/opsx:new` 创建变更提案

6. **变更前必须 `/opsx:verify`** — 校验完整性、正确性、一致性

### 分支策略
- `main`: 主分支，保持稳定
- 功能分支: `feat/xxx` 或 `fix/xxx`
- 大任务使用 Git Worktree 隔离（见下文）

### 代码审查
- 所有代码变更需经过独立审查
- 使用 `simplify` skill 检查代码质量
- 审查通过后方可提交

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

## 5. 开发经验沉淀

### 通用开发经验

#### Edit 操作精确匹配
`old_string` 仅匹配方法签名会导致方法体被删除，必须包含完整代码块。

#### 设计规格完整性检查
实现后对照设计规格逐项核对，注意公开 API 和编程接口。

#### 变更命名规范
动宾结构，如 `add-logout-button`/`fix-login-redirect`，禁止 `feature-1`/`update`。

#### 调试四阶段
不走瞎猜；严格执行：investigate → analyze → hypothesize → implement。

#### 大任务防漂移
用 executing-plans 的 checkpoint 每步对照 plan 验证。

#### 代码复制粘贴后变量检查
从一个方法复制模式到另一个方法时，必须逐行检查所有变量/参数是否与实际实现匹配。案例：`_parse_images_parallel` 需要 `img_ids` 参数检查，但 `_parse_complex_tables_parallel` 是直接遍历文档，复制时遗留了未定义的 `table_ids` 检查导致运行时错误。

#### 华为 RCA 5-Why 法
修 bug 不止修表面，必须追溯根因：
1. 为什么报错？
2. 为什么有这行？
3. 设计差异在哪？
4. 复制时漏了什么？
5. 根本原因是什么？
避免同类问题复发。

#### TDD 开发方法
红-绿-重构循环，测试先于实现。

### 项目特定经验

#### BAT 文件编码问题（重要！）

**问题**: 双击 BAT 文件闪退，命令被截断，中文乱码。

**根本原因**: 在 Unix/Linux 系统上使用 UTF-8 编码创建 BAT 文件，但 Windows CMD 期望 GBK 编码。

**解决方案**:
```python
with open('wordparser.bat', 'w', encoding='gbk', newline='\r\n') as f:
    f.write(bat_content)
```

#### 外部 API 限流处理

多模态 API 调用需实现重试机制，失败时应有降级策略：
- 实现 `multimodal/config.py` 的重试配置
- 使用 `parallel.py` 的并发控制
- 失败后记录日志，不中断主流程

#### LibreOffice 集成注意事项

- 路径检测: `renderer.py` 的 `_detect_libreoffice()`
- Windows/macOS/Linux 路径差异
- 退出 LibreOffice 进程: `--headless` + `--accept=...`

---

## 6. 安全底线

- 密钥/凭证/API Key 不得硬编码
- 配置通过环境变量或配置文件管理
- 不用不可信输入拼接 shell 命令
- 数据库访问用参数化查询（如有）
- 外部 API 调用必须包含超时和重试机制
- 敏感信息不得写入日志

---

## 7. OpenSpec 工具参考

项目已配置 OpenSpec，常用命令：

| 命令 | 用途 |
|------|------|
| `/opsx:explore` | 需求调研，梳理模糊需求 |
| `/opsx:propose` | 创建轻量变更提案 |
| `/opsx:new` | 创建新变更 |
| `/opsx:ff` | 快速生成功能规范文档 |
| `/opsx:continue` | 分步生成详细需求规格 |
| `/opsx:apply [变更名]` | 切换到指定变更上下文 |
| `/opsx:verify` | 验证规范符合度 |
| `/opsx:archive` | 归档变更 |
| `/opsx:sync` | 同步 specs 到主规范库 |
| `openspec list` | 查看有效变更 |

### OpenSpec 目录结构
- `openspec/specs/`: 功能规范
- `openspec/changes/`: 变更提案
- `openspec/config.yaml`: OpenSpec 配置

---

## 8. 关键文件快速索引

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

## 9. 全局规范引用

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

## 10. Git 提交规范

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

## 11. 相关资源

### 设计文档
- `docs/2026-04-22-word-parser-design.md`: 原始设计规格
- `docs/2026-04-23-libreoffice-multimodal-design.md`: LibreOffice+多模态设计
- `docs/lessons-learned.md`: 经验教训

### OpenSpec 规范
- `openspec/specs/wordparser-core/spec.md`: 详细功能规格

---

*最后更新: 2026-04-29*
