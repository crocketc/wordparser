class WordParserError(Exception):
    pass


class DocumentError(WordParserError):
    pass


class DocumentEncryptedError(DocumentError):
    pass


class DocumentCorruptedError(DocumentError):
    pass


class UnsupportedFormatError(DocumentError):
    pass


class ContentProcessError(WordParserError):
    pass


class TableProcessError(ContentProcessError):
    pass


class ImageProcessError(ContentProcessError):
    pass


class MultimodalAPIError(ContentProcessError):
    pass
