"""WordParser 主解析器测试"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

from wordparser import ParserConfig
from wordparser.core.parser import WordParser
from wordparser.exceptions import DocumentError


class TestFileSizeLimit:
    """测试文件大小限制"""

    def test_file_exceeds_limit_raises_error(self, tmp_path):
        """文件超过限制应抛出 DocumentError"""
        config = ParserConfig(max_file_size_mb=10)
        parser = WordParser(config)

        # 创建一个 15 MB 的测试文件
        test_file = tmp_path / "large.docx"
        test_file.write_bytes(b"x" * (15 * 1024 * 1024))

        with pytest.raises(DocumentError) as exc_info:
            parser._parse_document(test_file)

        assert "文件过大" in str(exc_info.value)
        assert "超过限制 10 MB" in str(exc_info.value)

    def test_file_exceeds_limit_with_doc(self, tmp_path):
        """.doc 文件超过限制应抛出 DocumentError（在转换前检查）"""
        config = ParserConfig(max_file_size_mb=5)
        parser = WordParser(config)

        # 创建一个 8 MB 的 .doc 文件
        test_file = tmp_path / "large.doc"
        test_file.write_bytes(b"x" * (8 * 1024 * 1024))

        with pytest.raises(DocumentError) as exc_info:
            parser._parse_document(test_file)

        assert "文件过大" in str(exc_info.value)

    def test_zero_limit_means_no_restriction(self, tmp_path):
        """max_file_size_mb = 0 表示不限制"""
        config = ParserConfig(max_file_size_mb=0)
        parser = WordParser(config)

        # 创建一个 1 KB 的测试文件（无法创建真正的超大文件用于测试）
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"PK" + b"\x00" * 1000)  # 简单的 ZIP 头部

        # 由于没有有效的 docx 内容，后续处理会失败
        # 但应该不是因为文件大小错误
        try:
            parser._parse_document(test_file)
        except DocumentError as e:
            assert "文件过大" not in str(e)
        except Exception:
            pass

    def test_default_limit_is_200mb(self):
        """默认限制应为 200 MB"""
        config = ParserConfig()
        assert config.max_file_size_mb == 200

    def test_configurable_limit(self):
        """限制应可通过配置修改"""
        config = ParserConfig(max_file_size_mb=50)
        assert config.max_file_size_mb == 50

        config = ParserConfig(max_file_size_mb=0)
        assert config.max_file_size_mb == 0

        config = ParserConfig(max_file_size_mb=1000)
        assert config.max_file_size_mb == 1000

    def test_file_size_check_happens_before_format_check(self, tmp_path):
        """文件大小检查应在格式检查之前执行"""
        config = ParserConfig(max_file_size_mb=1)
        parser = WordParser(config)

        # 创建一个超大的 .txt 文件（不支持的格式）
        test_file = tmp_path / "large.txt"
        test_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2 MB

        # 应该先报文件大小错误，而不是格式错误
        with pytest.raises(DocumentError) as exc_info:
            parser._parse_document(test_file)

        assert "文件过大" in str(exc_info.value)
        assert "不支持的文件格式" not in str(exc_info.value)
