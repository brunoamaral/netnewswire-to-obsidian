"""Read starred articles from NetNewsWire's SQLite database."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Article:
    article_id: str
    title: str
    content_html: str
    url: str
    date_published: str
    authors: str
    feed_id: str
    feed_name: str
    feed_url: str


def discover_accounts(accounts_base: Path) -> list[str]:
    """List available NetNewsWire account names."""
    if not accounts_base.is_dir():
        return []
    return [
        d.name
        for d in sorted(accounts_base.iterdir())
        if d.is_dir() and (d / "DB.sqlite3").exists()
    ]


def get_starred_articles(db_path: Path) -> list[Article]:
    """Query starred articles from a NetNewsWire DB.sqlite3 file."""
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row

    try:
        articles = []
        # Query articles joined with feeds for feed name/URL.
        # NetNewsWire schema: articles table has feedID referencing feeds table.
        cursor = conn.execute(
            """
            SELECT
                a.articleID,
                a.title,
                a.contentHTML,
                a.url,
                a.datePublished,
                COALESCE(a.authors, '') as authors,
                a.feedID,
                COALESCE(f.name, '') as feedName,
                COALESCE(f.url, '') as feedURL
            FROM articles a
            LEFT JOIN feeds f ON a.feedID = f.feedID
            WHERE a.starred = 1
            """
        )
        for row in cursor:
            articles.append(
                Article(
                    article_id=row["articleID"],
                    title=row["title"] or "Untitled",
                    content_html=row["contentHTML"] or "",
                    url=row["url"] or "",
                    date_published=row["datePublished"] or "",
                    authors=row["authors"],
                    feed_id=row["feedID"],
                    feed_name=row["feedName"],
                    feed_url=row["feedURL"],
                )
            )
        return articles
    finally:
        conn.close()
