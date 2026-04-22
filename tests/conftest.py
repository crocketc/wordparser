"""共享测试fixtures"""
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "samples"

@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR
