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
