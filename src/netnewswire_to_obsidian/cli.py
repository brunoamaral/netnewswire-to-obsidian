"""CLI entry point for nnw-obsidian-sync."""

import argparse
import logging
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from . import __version__
from .config import load_config, NNW_ACCOUNTS_BASE
from .database import discover_accounts
from .sync import sync_articles

LAUNCHD_LABEL = "com.nnw-obsidian-sync"
LAUNCHD_PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nnw-obsidian-sync",
        description="Sync NetNewsWire starred articles to Obsidian as markdown files.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument(
        "--accounts", action="append", help="Account name to sync (repeatable)"
    )
    parser.add_argument("--config", help="Path to config YAML file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without writing files",
    )
    parser.add_argument(
        "--list-accounts",
        action="store_true",
        help="List available NetNewsWire accounts and exit",
    )
    parser.add_argument(
        "--install-launchd",
        action="store_true",
        help="Install/update the launchd plist for recurring sync",
    )
    parser.add_argument(
        "--uninstall-launchd",
        action="store_true",
        help="Remove the launchd plist",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    return parser


def cmd_list_accounts() -> None:
    accounts = discover_accounts(NNW_ACCOUNTS_BASE)
    if not accounts:
        print(f"No accounts found at {NNW_ACCOUNTS_BASE}")
        print("Is NetNewsWire installed and has been opened at least once?")
        sys.exit(1)
    print("Available NetNewsWire accounts:")
    for name in accounts:
        print(f"  - {name}")


def cmd_install_launchd(config_path: Path | None, interval_minutes: int) -> None:
    nnw_sync_bin = shutil.which("nnw-obsidian-sync")
    if not nnw_sync_bin:
        print("Error: nnw-obsidian-sync not found in PATH.", file=sys.stderr)
        print("Install the package first: pip install .", file=sys.stderr)
        sys.exit(1)

    args = [nnw_sync_bin]
    if config_path:
        args.extend(["--config", str(config_path)])

    args_xml = "\n        ".join(f"<string>{a}</string>" for a in args)
    interval_seconds = interval_minutes * 60

    plist = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{LAUNCHD_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
                {args_xml}
            </array>
            <key>StartInterval</key>
            <integer>{interval_seconds}</integer>
            <key>StandardOutPath</key>
            <string>{Path.home() / "Library" / "Logs" / "nnw-obsidian-sync.log"}</string>
            <key>StandardErrorPath</key>
            <string>{Path.home() / "Library" / "Logs" / "nnw-obsidian-sync.log"}</string>
            <key>RunAtLoad</key>
            <true/>
        </dict>
        </plist>
    """)

    LAUNCHD_PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Unload existing plist if present
    if LAUNCHD_PLIST_PATH.exists():
        subprocess.run(
            ["launchctl", "unload", str(LAUNCHD_PLIST_PATH)],
            capture_output=True,
        )

    LAUNCHD_PLIST_PATH.write_text(plist)
    subprocess.run(["launchctl", "load", str(LAUNCHD_PLIST_PATH)], check=True)
    print(f"Installed and loaded launchd plist at {LAUNCHD_PLIST_PATH}")
    print(f"Sync will run every {interval_minutes} minutes.")


def cmd_uninstall_launchd() -> None:
    if not LAUNCHD_PLIST_PATH.exists():
        print("No launchd plist found. Nothing to uninstall.")
        return
    subprocess.run(
        ["launchctl", "unload", str(LAUNCHD_PLIST_PATH)],
        capture_output=True,
    )
    LAUNCHD_PLIST_PATH.unlink()
    print(f"Removed launchd plist at {LAUNCHD_PLIST_PATH}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.list_accounts:
        cmd_list_accounts()
        return

    if args.uninstall_launchd:
        cmd_uninstall_launchd()
        return

    config_path = Path(args.config) if args.config else None

    if args.install_launchd:
        # Load config to get interval_minutes
        try:
            config = load_config(
                config_path=config_path,
                cli_output_dir=args.output_dir,
                cli_accounts=args.accounts,
            )
        except ValueError:
            # output_dir not strictly needed for install, use default interval
            config = None

        interval = config.interval_minutes if config else 30
        cmd_install_launchd(config_path, interval)
        return

    try:
        config = load_config(
            config_path=config_path,
            cli_output_dir=args.output_dir,
            cli_accounts=args.accounts,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    synced, skipped = sync_articles(config, dry_run=args.dry_run)

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}Done: {synced} synced, {skipped} skipped (already exist).")


if __name__ == "__main__":
    main()
