"""Tests for the sync orchestrator."""

import sqlite3

import pytest

from netnewswire_to_obsidian.config import Config
from netnewswire_to_obsidian.sync import article_to_filename, build_frontmatter, sync_articles
from netnewswire_to_obsidian.database import Article


@pytest.fixture
def sample_article():
    return Article(
        article_id="art1",
        title="My Test Article",
        content_html="<p>Hello world</p>",
        url="https://example.com/1",
        date_published="2026-04-01",
        authors="Alice",
        feed_id="feed1",
        feed_name="Test Feed",
        feed_url="https://example.com/feed.xml",
    )


@pytest.fixture
def nnw_db(tmp_path):
    """Create a test NNW database structure."""
    account_dir = tmp_path / "accounts" / "TestAccount"
    account_dir.mkdir(parents=True)
    db_path = account_dir / "DB.sqlite3"

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE feeds (feedID TEXT PRIMARY KEY, name TEXT, url TEXT)"
    )
    conn.execute(
        """CREATE TABLE articles (
            articleID TEXT PRIMARY KEY, feedID TEXT, title TEXT,
            contentHTML TEXT, url TEXT, datePublished TEXT,
            dateModified TEXT, authors TEXT, starred INTEGER DEFAULT 0
        )"""
    )
    conn.execute("INSERT INTO feeds VALUES (?, ?, ?)", ("f1", "My Feed", "https://example.com/feed"))
    conn.execute(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("a1", "f1", "First Article", "<p>Content one</p>", "https://example.com/1", "2026-04-01", "", "Author", 1),
    )
    conn.execute(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("a2", "f1", "Second Article", "<p>Content two</p>", "https://example.com/2", "2026-04-02", "", "", 1),
    )
    conn.commit()
    conn.close()
    return tmp_path


def test_article_to_filename(sample_article):
    assert article_to_filename(sample_article) == "my-test-article.md"


def test_article_to_filename_empty_title():
    art = Article(
        article_id="abc123", title="", content_html="", url="",
        date_published="", authors="", feed_id="", feed_name="", feed_url="",
    )
    # Falls back to article_id slug
    filename = article_to_filename(art)
    assert filename == "abc123.md"


def test_build_frontmatter(sample_article):
    fm = build_frontmatter(sample_article, "2026-04-05T10:30:00")
    assert "---" in fm
    assert 'title: "My Test Article"' in fm
    assert 'author: "Alice"' in fm
    assert "date: 2026-04-01" in fm
    assert 'feed: "Test Feed"' in fm
    assert "url: https://example.com/1" in fm
    assert 'article_id: "art1"' in fm
    assert "synced_at: 2026-04-05T10:30:00" in fm


def test_sync_creates_files(nnw_db, tmp_path):
    output_dir = tmp_path / "output"
    config = Config(
        output_dir=output_dir,
        accounts=["TestAccount"],
        nnw_accounts_base=nnw_db / "accounts",
    )
    synced, skipped = sync_articles(config)
    assert synced == 2
    assert skipped == 0
    assert (output_dir / "first-article.md").exists()
    assert (output_dir / "second-article.md").exists()


def test_sync_skips_existing(nnw_db, tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    # Pre-create one file
    (output_dir / "first-article.md").write_text("existing")

    config = Config(
        output_dir=output_dir,
        accounts=["TestAccount"],
        nnw_accounts_base=nnw_db / "accounts",
    )
    synced, skipped = sync_articles(config)
    assert synced == 1
    assert skipped == 1
    # Existing file should not be overwritten
    assert (output_dir / "first-article.md").read_text() == "existing"


def test_sync_dry_run(nnw_db, tmp_path):
    output_dir = tmp_path / "output"
    config = Config(
        output_dir=output_dir,
        accounts=["TestAccount"],
        nnw_accounts_base=nnw_db / "accounts",
    )
    synced, skipped = sync_articles(config, dry_run=True)
    assert synced == 2
    assert skipped == 0
    # No files should be created in dry-run mode
    assert not output_dir.exists()


def test_sync_no_accounts(tmp_path):
    config = Config(
        output_dir=tmp_path / "output",
        nnw_accounts_base=tmp_path / "nonexistent",
    )
    synced, skipped = sync_articles(config)
    assert synced == 0
    assert skipped == 0


def test_sync_file_content(nnw_db, tmp_path):
    output_dir = tmp_path / "output"
    config = Config(
        output_dir=output_dir,
        accounts=["TestAccount"],
        nnw_accounts_base=nnw_db / "accounts",
    )
    sync_articles(config)
    content = (output_dir / "first-article.md").read_text()
    assert content.startswith("---")
    assert 'title: "First Article"' in content
    assert "Content one" in content
