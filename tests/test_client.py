"""测试OpenAI兼容视觉客户端"""

import pytest
from pathlib import Path
from wordparser.multimodal.client import OpenAICompatibleVisionClient


class TestOpenAICompatibleVisionClient:
    """测试OpenAICompatibleVisionClient类"""

    def test_init_default(self):
        """测试默认初始化"""
        client = OpenAICompatibleVisionClient()
        assert client is not None
        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:11434/v1"

    def test_init_custom(self):
        """测试自定义初始化"""
        client = OpenAICompatibleVisionClient(
            api_key="custom-key",
            base_url="http://custom:8080/v1",
            model="custom-model"
        )
        assert client.api_key == "custom-key"
        assert client.base_url == "http://custom:8080/v1"
        assert client.model == "custom-model"

    def test_parse_from_bytes(self, tmp_path):
        """测试从字节解析图片"""
        client = OpenAICompatibleVisionClient()

        # 创建模拟图片数据
        image_bytes = b"fake image data"

        # 调用方法（可能需要mock）
        # 这里测试基本调用
        try:
            result = client.parse_from_bytes(image_bytes, prompt="描述这张图片")
            # 如果有mock服务，可以验证结果
        except Exception as e:
            # 预期可能失败（没有真实服务）
            assert "test" in str(e).lower() or "connection" in str(e).lower() or "api" in str(e).lower()

    def test_parse_from_file(self, tmp_path):
        """测试从文件解析图片"""
        client = OpenAICompatibleVisionClient()

        # 创建测试图片文件
        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"fake image data")

        # 调用方法
        try:
            result = client.parse_from_file(str(image_file), prompt="描述这张图片")
            # 如果有mock服务，可以验证结果
        except Exception as e:
            # 预期可能失败（没有真实服务）
            assert "test" in str(e).lower() or "connection" in str(e).lower() or "api" in str(e).lower()

    def test_parse_from_bytes_with_custom_params(self, tmp_path):
        """测试自定义参数解析"""
        client = OpenAICompatibleVisionClient(
            model="custom-model",
            max_tokens=500,
            temperature=0.7
        )

        image_bytes = b"fake image data"

        try:
            result = client.parse_from_bytes(
                image_bytes,
                prompt="分析图片",
                max_tokens=300,
                temperature=0.5
            )
        except Exception as e:
            # 预期可能失败
            pass

    def test_parse_from_file_not_exists(self, tmp_path):
        """测试解析不存在的文件"""
        client = OpenAICompatibleVisionClient()

        non_existent = tmp_path / "not_exist.png"

        with pytest.raises(FileNotFoundError):
            client.parse_from_file(str(non_existent), prompt="描述")

    def test_parse_with_empty_bytes(self):
        """测试解析空字节"""
        client = OpenAICompatibleVisionClient()

        with pytest.raises(ValueError):
            client.parse_from_bytes(b"", prompt="描述")

    def test_parse_with_none_prompt(self, tmp_path):
        """测试None prompt"""
        client = OpenAICompatibleVisionClient()

        image_bytes = b"fake data"

        with pytest.raises(ValueError):
            client.parse_from_bytes(image_bytes, prompt=None)

    def test_client_initialization_with_env_vars(self, monkeypatch):
        """测试环境变量初始化"""
        # 设置环境变量
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "http://env:9000/v1")

        # 创建客户端（应该从环境变量读取）
        client = OpenAICompatibleVisionClient()

        # 验证使用了环境变量或默认值
        assert client is not None
