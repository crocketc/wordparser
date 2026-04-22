"""共享测试fixtures"""
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "samples"

@pytest.fixture(scope="session")
def fixtures_dir():
    return FIXTURES_DIR


from docx import Document
from docx.shared import Pt


@pytest.fixture
def simple_docx(tmp_path):
    """创建一个简单的测试用Word文档"""
    doc = Document()
    doc.add_heading("测试标题", level=1)
    doc.add_paragraph("这是第一个段落。")
    doc.add_paragraph("这是第二个段落。")
    path = tmp_path / "simple.docx"
    doc.save(str(path))
    return path


@pytest.fixture
def docx_with_blank_paragraphs(tmp_path):
    """创建含空白段落的Word文档"""
    doc = Document()
    doc.add_paragraph("有内容")
    doc.add_paragraph("")
    doc.add_paragraph("   ")
    doc.add_paragraph("\t")
    doc.add_paragraph("也有内容")
    path = tmp_path / "blanks.docx"
    doc.save(str(path))
    return path
