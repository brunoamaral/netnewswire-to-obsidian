"""Tests for database reading."""

import sqlite3
from pathlib import Path

import pytest

from netnewswire_to_obsidian.database import discover_accounts, get_starred_articles


@pytest.fixture
def nnw_db(tmp_path):
    """Create a test SQLite DB matching the real NetNewsWire schema."""
    account_dir = tmp_path / "TestAccount"
    account_dir.mkdir()
    db_path = account_dir / "DB.sqlite3"

    # OPML for feed name lookup (feedID == xmlUrl)
    (account_dir / "Subscriptions.opml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<opml version="1.1"><head><title>Test</title></head><body>'
        '<outline text="Test Feed" title="Test Feed" type="rss"'
        ' xmlUrl="https://example.com/feed.xml"/>'
        '</body></opml>'
    )

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE articles (
            articleID TEXT PRIMARY KEY, feedID TEXT NOT NULL,
            uniqueID TEXT NOT NULL DEFAULT '', title TEXT, contentHTML TEXT,
            contentText TEXT, url TEXT, externalURL TEXT, summary TEXT,
            imageURL TEXT, bannerImageURL TEXT, datePublished DATE,
            dateModified DATE, searchRowID INTEGER, markdown TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE statuses (
            articleID TEXT NOT NULL PRIMARY KEY, read BOOL NOT NULL DEFAULT 0,
            starred BOOL NOT NULL DEFAULT 0, dateArrived DATE NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE authors (
            authorID TEXT NOT NULL PRIMARY KEY, name TEXT, url TEXT,
            avatarURL TEXT, emailAddress TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE authorsLookup (
            authorID TEXT NOT NULL, articleID TEXT NOT NULL,
            PRIMARY KEY(authorID, articleID)
        )
        """
    )
    conn.execute(
        "INSERT INTO articles (articleID, feedID, title, contentHTML, url, datePublished) VALUES (?, ?, ?, ?, ?, ?)",
        ("art1", "https://example.com/feed.xml", "Starred Article", "<p>Hello <strong>world</strong></p>", "https://example.com/1", "2026-04-01"),
    )
    conn.execute(
        "INSERT INTO articles (articleID, feedID, title, contentHTML, url, datePublished) VALUES (?, ?, ?, ?, ?, ?)",
        ("art2", "https://example.com/feed.xml", "Unstarred Article", "<p>Not starred</p>", "https://example.com/2", "2026-04-02"),
    )
    conn.execute(
        "INSERT INTO articles (articleID, feedID, title, contentHTML, url, datePublished) VALUES (?, ?, ?, ?, ?, ?)",
        (
            "art3",
            "https://example.com/feed.xml",
            "Another Starred",
            "<h1>Title</h1><p>Content</p>",
            "https://example.com/3",
            "2026-04-03",
        ),
    )
    conn.execute("INSERT INTO statuses (articleID, starred) VALUES (?, ?)", ("art1", 1))
    conn.execute("INSERT INTO statuses (articleID, starred) VALUES (?, ?)", ("art2", 0))
    conn.execute("INSERT INTO statuses (articleID, starred) VALUES (?, ?)", ("art3", 1))
    conn.execute("INSERT INTO authors (authorID, name) VALUES (?, ?)", ("author1", "Alice"))
    conn.execute("INSERT INTO authorsLookup (authorID, articleID) VALUES (?, ?)", ("author1", "art1"))
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
    assert art.feed_name == "Test Feed"  # resolved from Subscriptions.opml
    assert art.feed_url == "https://example.com/feed.xml"  # feedID IS the URL
