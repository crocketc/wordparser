from wordparser.core.report import ParseReport, ParseError, ParseStats


def test_parse_stats_defaults():
    stats = ParseStats()
    assert stats.total_headings == 0
    assert stats.total_paragraphs == 0
    assert stats.total_tables == 0
    assert stats.total_images == 0
    assert stats.multimodal_calls == 0
    assert stats.multimodal_failures == 0
    assert stats.processing_time == 0.0


def test_parse_error():
    err = ParseError(type="table", message="合并单元格过多")
    assert err.type == "table"
    assert err.message == "合并单元格过多"
    assert err.fatal is False
    assert err.location is None


def test_parse_report_no_errors():
    report = ParseReport(success=True, output_path=None, errors=[], stats=ParseStats())
    assert report.has_errors() is False
    assert report.has_fatal_errors() is False


def test_parse_report_with_errors():
    errors = [
        ParseError(type="image", message="解析失败", fatal=False),
        ParseError(type="document", message="损坏", fatal=True),
    ]
    report = ParseReport(success=False, output_path=None, errors=errors, stats=ParseStats())
    assert report.has_errors() is True
    assert report.has_fatal_errors() is True
