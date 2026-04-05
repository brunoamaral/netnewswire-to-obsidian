"""Convert HTML article content to Markdown."""

import re

from markdownify import markdownify


def html_to_markdown(html: str) -> str:
    """Convert HTML to clean Markdown."""
    if not html:
        return ""

    # Strip script and style tags before conversion
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)

    md = markdownify(cleaned, heading_style="ATX", strip=["img"])
    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()
