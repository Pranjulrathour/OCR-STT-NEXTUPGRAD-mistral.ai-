from app.services.mistral_ocr import _markdown_to_plain_text


def test_strips_heading_marker() -> None:
    assert _markdown_to_plain_text("# Title") == "Title"


def test_strips_bold_and_italic() -> None:
    assert _markdown_to_plain_text("**bold** and _italic_") == "bold and italic"


def test_keeps_link_text_drops_url() -> None:
    assert (
        _markdown_to_plain_text("See [our docs](https://example.com) for more")
        == "See our docs for more"
    )


def test_drops_images_entirely() -> None:
    assert _markdown_to_plain_text("![alt text](img.png) caption") == "caption"


def test_collapses_excess_blank_lines() -> None:
    assert _markdown_to_plain_text("a\n\n\n\nb") == "a\n\nb"
