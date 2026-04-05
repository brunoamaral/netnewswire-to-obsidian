"""Main sync logic: read starred articles and write markdown files."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from slugify import slugify

from .config import Config
from .converter import html_to_markdown
from .database import Article, discover_accounts, get_starred_articles

logger = logging.getLogger(__name__)


def build_frontmatter(article: Article, synced_at: str) -> str:
    """Build YAML frontmatter for an article."""
    # Escape quotes in title/author for YAML safety
    title = article.title.replace('"', '\\"')
    authors = article.authors.replace('"', '\\"')
    feed_name = article.feed_name.replace('"', '\\"')

    lines = [
        "---",
        f'title: "{title}"',
        f'author: "{authors}"',
        f"date: {article.date_published}",
        f'feed: "{feed_name}"',
        f"url: {article.url}",
        f"feed_url: {article.feed_url}",
        f'article_id: "{article.article_id}"',
        f"synced_at: {synced_at}",
        "---",
    ]
    return "\n".join(lines)


def article_to_filename(article: Article) -> str:
    """Generate a markdown filename from article title."""
    slug = slugify(article.title, max_length=200)
    if not slug:
        slug = slugify(article.article_id, max_length=200)
    return f"{slug}.md"


def sync_articles(config: Config, dry_run: bool = False) -> tuple[int, int]:
    """Sync starred articles to markdown files.

    Returns (synced_count, skipped_count).
    """
    available = discover_accounts(config.nnw_accounts_base)
    if not available:
        logger.warning("No NetNewsWire accounts found at %s", config.nnw_accounts_base)
        return 0, 0

    accounts_to_sync = config.accounts if config.accounts else available
    missing = set(accounts_to_sync) - set(available)
    if missing:
        logger.warning("Accounts not found: %s", ", ".join(sorted(missing)))
        accounts_to_sync = [a for a in accounts_to_sync if a in available]

    if not dry_run:
        config.output_dir.mkdir(parents=True, exist_ok=True)

    synced = 0
    skipped = 0
    synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    for account_name in accounts_to_sync:
        db_path = config.nnw_accounts_base / account_name / "DB.sqlite3"
        logger.info("Reading account: %s", account_name)

        try:
            articles = get_starred_articles(db_path)
        except Exception:
            logger.exception("Failed to read database for account %s", account_name)
            continue

        for article in articles:
            filename = article_to_filename(article)
            filepath = config.output_dir / filename

            if filepath.exists():
                logger.debug("Skipping (exists): %s", filename)
                skipped += 1
                continue

            if dry_run:
                logger.info("[dry-run] Would sync: %s", filename)
                synced += 1
                continue

            frontmatter = build_frontmatter(article, synced_at)
            body = html_to_markdown(article.content_html)
            content = f"{frontmatter}\n\n{body}\n"

            filepath.write_text(content, encoding="utf-8")
            logger.info("Synced: %s", filename)
            synced += 1

    return synced, skipped
