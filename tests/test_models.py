from wordparser.core.models import (
    BlockType, TitleNode, ContentBlock, ParsedDocument
)


def test_block_type_values():
    assert BlockType.HEADING.value == "heading"
    assert BlockType.PARAGRAPH.value == "paragraph"
    assert BlockType.TABLE.value == "table"
    assert BlockType.IMAGE.value == "image"
    assert BlockType.FORMULA.value == "formula"
    assert BlockType.LIST.value == "list"
    assert BlockType.TOC.value == "toc"
    assert BlockType.TABLE_PENDING.value == "table_pending"
    assert BlockType.IMAGE_PENDING.value == "image_pending"


def test_title_node_defaults():
    node = TitleNode(level=1, text="Hello", anchor="hello")
    assert node.level == 1
    assert node.text == "Hello"
    assert node.anchor == "hello"
    assert node.children == []


def test_title_node_tree():
    child = TitleNode(level=2, text="Child", anchor="child")
    parent = TitleNode(level=1, text="Parent", anchor="parent", children=[child])
    assert len(parent.children) == 1
    assert parent.children[0].text == "Child"


def test_content_block():
    block = ContentBlock(type=BlockType.PARAGRAPH, content="Hello world")
    assert block.type == BlockType.PARAGRAPH
    assert block.content == "Hello world"
    assert block.metadata == {}


def test_content_block_with_metadata():
    block = ContentBlock(
        type=BlockType.TABLE,
        content="| a | b |",
        metadata={"rows": 2, "cols": 2}
    )
    assert block.metadata["rows"] == 2


def test_parsed_document_defaults():
    doc = ParsedDocument()
    assert doc.metadata == {}
    assert doc.title_tree == []
    assert doc.content_blocks == []


def test_parsed_document_with_data():
    heading = TitleNode(level=1, text="Title", anchor="title")
    block = ContentBlock(type=BlockType.HEADING, content=heading)
    doc = ParsedDocument(
        title_tree=[heading],
        content_blocks=[block]
    )
    assert len(doc.title_tree) == 1
    assert len(doc.content_blocks) == 1
