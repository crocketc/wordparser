from wordparser.core.postprocess import PostProcessor


def test_normalize_line_breaks():
    proc = PostProcessor()
    result = proc.process("段落1\n\n\n\n段落2")
    assert result == "段落1\n\n段落2\n"


def test_trim_lines():
    proc = PostProcessor()
    result = proc.process("  行1  \n  行2  ")
    assert "行1" in result
    assert "行2" in result


def test_remove_trailing_whitespace():
    proc = PostProcessor()
    result = proc.process("内容  \n\n  ")
    assert result.strip() == "内容"


def test_ensure_blank_line_before_heading():
    proc = PostProcessor()
    result = proc.process("段落内容\n# 标题")
    assert result == "段落内容\n\n# 标题\n"


def test_ensure_blank_line_after_heading():
    proc = PostProcessor()
    result = proc.process("# 标题\n段落内容")
    assert result == "# 标题\n\n段落内容\n"
