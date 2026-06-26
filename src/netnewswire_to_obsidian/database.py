"""Read starred articles from NetNewsWire's SQLite database."""

import json
import logging
import sqlite3
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_EXPECTED_SCHEMA_FILE = Path(__file__).parent / "expected_schema.sql"


def _get_schema(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
    ).fetchall()
    return "\n".join(sorted(r[0] for r in rows)) + "\n"


def check_schema(db_path: Path) -> None:
    """Warn if the database schema differs from the saved baseline."""
    if not _EXPECTED_SCHEMA_FILE.exists():
        return
    expected = _EXPECTED_SCHEMA_FILE.read_text()
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        actual = _get_schema(conn)
    finally:
        conn.close()
    if actual != expected:
        logger.warning(
            "NetNewsWire database schema has changed — queries may fail.\n"
            "\n--- expected schema ---\n%s\n--- actual schema ---\n%s",
            expected.strip(),
            actual.strip(),
        )


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
    check_schema(db_path)
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
                COALESCE(NULLIF(a.url, ''), a.externalURL) as url,
                a.datePublished,
                a.authors,
                a.feedID
            FROM articles a
            JOIN statuses s ON a.articleID = s.articleID
            WHERE s.starred = 1
            """
        )
        for row in cursor:
            feed_id = row["feedID"]
            raw_authors = row["authors"]
            try:
                authors_str = ", ".join(a["name"] for a in json.loads(raw_authors) if "name" in a) if raw_authors else ""
            except (json.JSONDecodeError, TypeError):
                authors_str = raw_authors or ""
            articles.append(
                Article(
                    article_id=row["articleID"],
                    title=row["title"] or "Untitled",
                    content_html=row["contentHTML"] or "",
                    url=row["url"] or "",
                    date_published=row["datePublished"] or "",
                    authors=authors_str,
                    feed_id=feed_id,
                    feed_name=feed_names.get(feed_id, feed_id),
                    feed_url=feed_id,
                )
            )
        return articles
    finally:
        conn.close()
