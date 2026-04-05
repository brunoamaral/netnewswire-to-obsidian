"""Tests for HTML to Markdown conversion."""

from netnewswire_to_obsidian.converter import html_to_markdown


def test_basic_html():
    html = "<p>Hello <strong>world</strong></p>"
    md = html_to_markdown(html)
    assert "Hello" in md
    assert "**world**" in md


def test_heading():
    html = "<h1>Title</h1><p>Content</p>"
    md = html_to_markdown(html)
    assert "# Title" in md
    assert "Content" in md


def test_links():
    html = '<p>Visit <a href="https://example.com">here</a></p>'
    md = html_to_markdown(html)
    assert "[here](https://example.com)" in md


def test_empty_html():
    assert html_to_markdown("") == ""
    assert html_to_markdown(None) == ""


def test_script_tags_stripped():
    html = "<p>Before</p><script>alert('xss')</script><p>After</p>"
    md = html_to_markdown(html)
    assert "alert" not in md
    assert "Before" in md
    assert "After" in md


def test_style_tags_stripped():
    html = "<style>body{color:red}</style><p>Content</p>"
    md = html_to_markdown(html)
    assert "color" not in md
    assert "Content" in md


def test_excessive_blank_lines_collapsed():
    html = "<p>One</p><br><br><br><br><p>Two</p>"
    md = html_to_markdown(html)
    # Should not have more than 2 consecutive newlines
    assert "\n\n\n" not in md
