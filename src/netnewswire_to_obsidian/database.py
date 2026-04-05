"""Read starred articles from NetNewsWire's SQLite database."""

import sqlite3
import xml.etree.ElementTree as ET
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


def load_feed_names(account_dir: Path) -> dict[str, str]:
    """Parse Subscriptions.opml to return {feed_url: feed_name}."""
    opml_path = account_dir / "Subscriptions.opml"
    if not opml_path.exists():
        return {}
    try:
        tree = ET.parse(opml_path)
    except ET.ParseError:
        return {}
    result = {}
    for outline in tree.iter("outline"):
        xml_url = outline.get("xmlUrl")
        name = outline.get("title") or outline.get("text") or xml_url
        if xml_url and name:
            result[xml_url] = name
    return result


def get_starred_articles(db_path: Path) -> list[Article]:
    """Query starred articles from a NetNewsWire DB.sqlite3 file."""
    feed_names = load_feed_names(db_path.parent)
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row

    try:
        articles = []
        cursor = conn.execute(
            """
            SELECT
                a.articleID,
                a.title,
                a.contentHTML,
                a.url,
                a.datePublished,
                GROUP_CONCAT(au.name, ', ') as authors,
                a.feedID
            FROM articles a
            JOIN statuses s ON a.articleID = s.articleID
            LEFT JOIN authorsLookup al ON a.articleID = al.articleID
            LEFT JOIN authors au ON al.authorID = au.authorID
            WHERE s.starred = 1
            GROUP BY a.articleID
            """
        )
        for row in cursor:
            feed_id = row["feedID"]
            articles.append(
                Article(
                    article_id=row["articleID"],
                    title=row["title"] or "Untitled",
                    content_html=row["contentHTML"] or "",
                    url=row["url"] or "",
                    date_published=row["datePublished"] or "",
                    authors=row["authors"] or "",
                    feed_id=feed_id,
                    feed_name=feed_names.get(feed_id, feed_id),
                    feed_url=feed_id,
                )
            )
        return articles
    finally:
        conn.close()
