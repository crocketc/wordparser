"""DocumentRenderer 测试"""
import pytest
from pathlib import Path
from wordparser.core.renderer import DocumentRenderer


class TestDocumentRenderer:
    def test_detect_libreoffice_returns_string_or_none(self):
        renderer = DocumentRenderer()
        result = renderer._detect_libreoffice()
        assert result is None or isinstance(result, str)

    def test_is_available_without_libreoffice(self):
        renderer = DocumentRenderer(libreoffice_path="/nonexistent/soffice")
        assert renderer.is_available() is False

    def test_is_doc_detection(self):
        renderer = DocumentRenderer()
        assert renderer.is_doc(Path("test.doc")) is True
        assert renderer.is_doc(Path("test.docx")) is False
        assert renderer.is_doc(Path("test.DOC")) is True
