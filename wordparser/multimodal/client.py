"""OpenAI兼容视觉客户端模块

提供与OpenAI API兼容的多模态视觉客户端，用于：
- 调用视觉模型解析图片
- 支持字节流和文件输入
- 灵活的配置选项
"""

import os
from typing import Optional
from pathlib import Path
from base64 import b64encode
from openai import OpenAI


class OpenAICompatibleVisionClient:
    """OpenAI兼容的视觉客户端

    封装OpenAI SDK，提供与OpenAI API兼容的图片解析功能。

    Attributes:
        api_key: API密钥
        base_url: API基础URL
        model: 使用的模型名称
        max_tokens: 最大生成token数
        temperature: 温度参数
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "llava",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        timeout: int = 600,
    ):
        """初始化客户端

        Args:
            api_key: API密钥，默认从环境变量或使用测试密钥
            base_url: API基础URL，默认从环境变量或使用localhost
            model: 模型名称
            max_tokens: 最大生成token数
            temperature: 温度参数
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "test-key")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def parse_from_bytes(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """从字节流解析图片

        Args:
            image_bytes: 图片字节流
            prompt: 提示词
            max_tokens: 覆盖默认的最大token数
            temperature: 覆盖默认的温度参数

        Returns:
            模型的解析结果文本

        Raises:
            ValueError: 如果image_bytes为空或prompt为None
        """
        if not image_bytes:
            raise ValueError("image_bytes不能为空")

        if prompt is None:
            raise ValueError("prompt不能为None")

        # 编码图片为base64
        base64_image = b64encode(image_bytes).decode("utf-8")

        # 调用API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
        )

        # 返回结果
        return response.choices[0].message.content

    def parse_from_file(
        self,
        image_path: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """从文件解析图片

        Args:
            image_path: 图片文件路径
            prompt: 提示词
            max_tokens: 覆盖默认的最大token数
            temperature: 覆盖默认的温度参数

        Returns:
            模型的解析结果文本

        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果prompt为None
        """
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {image_path}")

        # 读取文件
        with open(path, "rb") as f:
            image_bytes = f.read()

        # 调用字节流方法
        return self.parse_from_bytes(
            image_bytes,
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def parse_text(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """纯文本对话，用于 LLM 解析结构化数据

        Args:
            prompt: 完整的提示词（包含数据）
            max_tokens: 覆盖默认的最大 token 数
            temperature: 覆盖默认的温度参数

        Returns:
            模型的回复文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
        )

        return response.choices[0].message.content
