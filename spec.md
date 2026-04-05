# Spec — NetNewsWire to Obsidian Sync

## Context

NetNewsWire users who manage their RSS feeds via iCloud sync have no built-in way to export starred articles. This tool bridges that gap by reading starred articles directly from NetNewsWire's SQLite database and writing them as markdown files into an Obsidian vault folder, enabling a personal knowledge management workflow.

## Overview

A Python CLI tool that periodically syncs starred articles from NetNewsWire's local SQLite database to a specified Obsidian vault folder as markdown files with YAML frontmatter.

## Decisions

| Area | Decision |
|------|----------|
| Platform | macOS only |
| Data source | SQLite (DB.sqlite3) directly |
| Output format | Full article content + YAML frontmatter |
| Scheduling | launchd plist (cron-style) |
| Language | Python 3.10+ |
| Un-starred handling | Keep the markdown file (no deletion) |
| Accounts | Configurable (user specifies which accounts to sync) |
| Filename format | Title slug only (e.g., `my-article-title.md`) |
| Duplicate titles | Skip if file already exists |
| Configuration | YAML config file + CLI argument overrides |

## Data Source

**Database path pattern:**
```
~/Library/Containers/com.ranchero.NetNewsWire-Evergreen/Data/Library/Application Support/NetNewsWire/Accounts/<AccountName>/DB.sqlite3
```

The tool discovers accounts by listing subdirectories, lets users configure which to include (default: all), and queries each account's DB for starred articles.

## Output Format

Each starred article becomes a markdown file:

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

Full article content converted from HTML to markdown...
```

## Configuration

Config file: `~/.config/nnw-obsidian-sync/config.yaml`

See `config.example.yaml` for a template.

CLI flags override config values. Run `nnw-obsidian-sync --help` for all options.

## Out of Scope (v1)

- Linux support
- Deleting/archiving files when articles are un-starred
- Two-way sync (Obsidian → NetNewsWire)
- Image downloading / local caching
- Tag/folder structure mirroring from NetNewsWire
