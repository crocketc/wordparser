# 开发经验教训

## BAT文件编码问题

### 问题现象
- 双击BAT文件闪退
- 错误信息显示乱码：`'dParser'`（应该是`WordParser`）
- 中文提示变成乱码：`'鍏ocx鏂囦欢...'`

### 根本原因
在Unix/Linux系统上使用UTF-8编码创建BAT文件，但Windows CMD期望GBK编码，导致：
1. 多字节UTF-8字符被错误解析
2. 命令关键字被截断
3. 中文完全乱码

### 解决方案
```python
# 使用GBK编码和CRLF换行符创建BAT文件
with open('wordparser.bat', 'w', encoding='gbk', newline='\r\n') as f:
    f.write(bat_content)
```

### 最佳实践
- BAT文件避免使用中文提示
- 必须使用GBK编码（Windows系统默认）
- 使用CRLF换行符（`\r\n`）
- 在目标平台上测试（不要在Unix上创建Windows脚本）

## 其他教训

### Edit操作必须精确匹配
old_string必须包含完整的待替换代码块，否则可能删除不该删除的内容。

### 设计规格完整性检查
实现完成后需对照设计规格逐项核对，确保所有公开API都已实现。

---

## 技术债务

### ParallelMultimodalProcessor 类未被使用

**创建日期**: 2026-04-27

**问题描述**:
`wordparser/multimodal/parallel.py` 中的 `ParallelMultimodalProcessor` 类在设计阶段规划为统一的多模态内容并行处理接口，但在实际实施中未被使用。`parser.py` 选择直接使用 `ThreadPoolExecutor` 实现并行处理。

**影响范围**:
- `wordparser/multimodal/parallel.py` 整个文件
- 相关测试用例（如有）

**技术背景**:
- **设计初衷**: 封装 `MultimodalParser`，提供统一的批量处理接口（支持 table/image/chart/smartart 四种类型）
- **设计文档**: `docs/2026-04-22-word-parser-design.md:272`
- **实施状态**: 代码已实现且功能完整（commit dff51c3），但未集成到主解析流程

**未被使用的原因**:
1. 各类内容处理逻辑差异较大（图片直接传 bytes，表格需提取数据，Chart/SmartArt 需 XML 解析）
2. 统一接口反而增加抽象层复杂度
3. 直接使用 `ThreadPoolExecutor` 代码更简洁直观
4. 开发进度优先，先落地核心功能

**决策建议**:

| 选项 | 操作 | 适用场景 |
|------|------|----------|
| **保留** | 维持现状，添加 TODO 标记 | 未来可能需要统一接口的场景 |
| **删除** | 移除该文件及相关测试 | 确定未来不需要统一接口 |
| **集成** | 重构 parser.py 使用此类 | 需要在多个模块复用并行逻辑 |

**当前状态**: 已在代码中添加 TODO 注释，等待业务需求触发决策点

**更新记录**:
- 2026-04-27: 初始记录，标记为技术债务

