# NetNewsWire to Obsidian

Sync your NetNewsWire starred articles to an Obsidian vault as markdown files.

## How it works

This tool reads starred articles directly from NetNewsWire's local SQLite database on macOS and writes them as markdown files (with YAML frontmatter) into a folder of your choice — typically inside your Obsidian vault.

- **One-way sync**: starred articles are exported; un-starring does not delete the file.
- **Idempotent**: if a file already exists, it is skipped.
- **Configurable**: choose which NetNewsWire accounts to sync.

## Requirements

- macOS (NetNewsWire stores its database locally)
- Python 3.10+
- NetNewsWire (with at least one account set up)

## Installation

```bash
pip install .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

1. Copy and edit the config file:

```bash
mkdir -p ~/.config/nnw-obsidian-sync
cp config.example.yaml ~/.config/nnw-obsidian-sync/config.yaml
# Edit output_dir to point to your Obsidian vault folder
```

2. List your NetNewsWire accounts:

```bash
nnw-obsidian-sync --list-accounts
```

3. Run a dry-run to see what would be synced:

```bash
nnw-obsidian-sync --dry-run
```

4. Run the sync:

```bash
nnw-obsidian-sync
```

## Recurring Sync (launchd)

Install a launchd plist to run the sync automatically:

```bash
nnw-obsidian-sync --install-launchd
```

This will sync every 30 minutes (configurable via `interval_minutes` in the config file). To remove it:

```bash
nnw-obsidian-sync --uninstall-launchd
```

Logs are written to `~/Library/Logs/nnw-obsidian-sync.log`.

## CLI Reference

```
nnw-obsidian-sync [OPTIONS]

--output-dir PATH     Override output directory
--accounts NAME       Accounts to sync (repeatable)
--config PATH         Custom config file path
--dry-run             Show what would be synced without writing files
--list-accounts       List available NetNewsWire accounts and exit
--install-launchd     Install/update the launchd plist for recurring sync
--uninstall-launchd   Remove the launchd plist
--verbose, -v         Enable verbose logging
--version             Show version and exit
```

## Output Format

Each article is saved as a markdown file with YAML frontmatter:

```markdown
---
title: "Article Title"
author: "Author Name"
date: 2026-04-01
feed: "Feed Name"
url: https://example.com/article
feed_url: https://example.com/feed.xml
article_id: "abc123"
synced_at: 2026-04-05T10:30:00
---

Article content in markdown...
```

## License

MIT
