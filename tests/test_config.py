from wordparser.config import (
    ParserConfig,
    VisionModelConfig,
    MultimodalConfig,
    TOCPosition,
)


def test_parser_config_defaults():
    config = ParserConfig()
    assert config.max_heading_level == 6
    assert config.encoding == "utf-8"
    assert config.multimodal is None
    assert config.libreoffice_path is None
    assert config.generate_toc is True
    assert config.toc_position == TOCPosition.AFTER_TITLE
    assert config.include_header_footer is False
    assert config.include_comments is False


def test_vision_model_config_defaults():
    config = VisionModelConfig()
    assert config.base_url == "http://localhost:1234/v1"
    assert config.api_key is None
    assert config.model == "qwen2-vl-7b"
    assert config.timeout == 60
    assert config.temperature == 0.0


def test_multimodal_config_defaults():
    config = MultimodalConfig()
    assert config.max_concurrent == 4
    assert config.batch_delay == 0.1
    assert config.retry_on_failure is True
    assert isinstance(config.model, VisionModelConfig)


def test_parser_config_with_multimodal():
    config = ParserConfig(
        multimodal=MultimodalConfig(
            model=VisionModelConfig(base_url="http://custom:8080/v1")
        )
    )
    assert config.multimodal.model.base_url == "http://custom:8080/v1"
