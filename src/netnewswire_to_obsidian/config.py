"""Configuration loading and merging."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "nnw-obsidian-sync" / "config.yaml"

NNW_ACCOUNTS_BASE = (
    Path.home()
    / "Library"
    / "Containers"
    / "com.ranchero.NetNewsWire-Evergreen"
    / "Data"
    / "Library"
    / "Application Support"
    / "NetNewsWire"
    / "Accounts"
)


@dataclass
class Config:
    output_dir: Path
    accounts: list[str] = field(default_factory=list)
    interval_minutes: int = 30
    nnw_accounts_base: Path = field(default_factory=lambda: NNW_ACCOUNTS_BASE)


def load_config(
    config_path: Path | None = None,
    cli_output_dir: str | None = None,
    cli_accounts: list[str] | None = None,
) -> Config:
    """Load config from YAML file and merge CLI overrides."""
    path = config_path or DEFAULT_CONFIG_PATH
    data: dict = {}

    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}

    output_dir_str = cli_output_dir or data.get("output_dir")
    if not output_dir_str:
        raise ValueError(
            "output_dir is required. Set it in the config file or pass --output-dir."
        )

    output_dir = Path(output_dir_str).expanduser().resolve()

    accounts = cli_accounts if cli_accounts else data.get("accounts", [])
    interval_minutes = data.get("interval_minutes", 30)

    nnw_base_str = data.get("nnw_accounts_base")
    nnw_base = (
        Path(nnw_base_str).expanduser().resolve()
        if nnw_base_str
        else NNW_ACCOUNTS_BASE
    )

    return Config(
        output_dir=output_dir,
        accounts=accounts,
        interval_minutes=interval_minutes,
        nnw_accounts_base=nnw_base,
    )
