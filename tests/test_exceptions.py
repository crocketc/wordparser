import pytest
from wordparser.exceptions import (
    WordParserError,
    DocumentError,
    DocumentEncryptedError,
    DocumentCorruptedError,
    UnsupportedFormatError,
    ContentProcessError,
    TableProcessError,
    ImageProcessError,
    MultimodalAPIError,
)


def test_exception_hierarchy():
    assert issubclass(DocumentError, WordParserError)
    assert issubclass(DocumentEncryptedError, DocumentError)
    assert issubclass(DocumentCorruptedError, DocumentError)
    assert issubclass(UnsupportedFormatError, DocumentError)
    assert issubclass(ContentProcessError, WordParserError)
    assert issubclass(TableProcessError, ContentProcessError)
    assert issubclass(ImageProcessError, ContentProcessError)
    assert issubclass(MultimodalAPIError, ContentProcessError)


def test_document_encrypted_is_fatal():
    with pytest.raises(DocumentEncryptedError):
        raise DocumentEncryptedError("test.docx")
