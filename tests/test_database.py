"""Tests for database reading."""

import sqlite3
from pathlib import Path

import pytest

from netnewswire_to_obsidian.database import discover_accounts, get_starred_articles


@pytest.fixture
def nnw_db(tmp_path):
    """Create a test SQLite DB matching NetNewsWire schema."""
    account_dir = tmp_path / "TestAccount"
    account_dir.mkdir()
    db_path = account_dir / "DB.sqlite3"

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE feeds (
            feedID TEXT PRIMARY KEY,
            name TEXT,
            url TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE articles (
            articleID TEXT PRIMARY KEY,
            feedID TEXT,
            title TEXT,
            contentHTML TEXT,
            url TEXT,
            datePublished TEXT,
            dateModified TEXT,
            authors TEXT,
            starred INTEGER DEFAULT 0,
            FOREIGN KEY (feedID) REFERENCES feeds(feedID)
        )
        """
    )
    conn.execute(
        "INSERT INTO feeds VALUES (?, ?, ?)",
        ("feed1", "Test Feed", "https://example.com/feed.xml"),
    )
    conn.execute(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "art1",
            "feed1",
            "Starred Article",
            "<p>Hello <strong>world</strong></p>",
            "https://example.com/1",
            "2026-04-01",
            "2026-04-01",
            "Alice",
            1,
        ),
    )
    conn.execute(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "art2",
            "feed1",
            "Unstarred Article",
            "<p>Not starred</p>",
            "https://example.com/2",
            "2026-04-02",
            "2026-04-02",
            "Bob",
            0,
        ),
    )
    conn.execute(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "art3",
            "feed1",
            "Another Starred",
            "<h1>Title</h1><p>Content</p>",
            "https://example.com/3",
            "2026-04-03",
            "2026-04-03",
            "",
            1,
        ),
    )
    conn.commit()
    conn.close()
    return tmp_path


def test_discover_accounts(nnw_db):
    accounts = discover_accounts(nnw_db)
    assert accounts == ["TestAccount"]


def test_discover_accounts_empty(tmp_path):
    accounts = discover_accounts(tmp_path)
    assert accounts == []


def test_discover_accounts_nonexistent():
    accounts = discover_accounts(Path("/nonexistent/path"))
    assert accounts == []


def test_get_starred_articles(nnw_db):
    db_path = nnw_db / "TestAccount" / "DB.sqlite3"
    articles = get_starred_articles(db_path)
    assert len(articles) == 2
    titles = {a.title for a in articles}
    assert titles == {"Starred Article", "Another Starred"}


def test_starred_article_fields(nnw_db):
    db_path = nnw_db / "TestAccount" / "DB.sqlite3"
    articles = get_starred_articles(db_path)
    art = next(a for a in articles if a.article_id == "art1")
    assert art.title == "Starred Article"
    assert art.content_html == "<p>Hello <strong>world</strong></p>"
    assert art.url == "https://example.com/1"
    assert art.date_published == "2026-04-01"
    assert art.authors == "Alice"
    assert art.feed_name == "Test Feed"
    assert art.feed_url == "https://example.com/feed.xml"
