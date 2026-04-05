"""Tests for configuration loading."""

from pathlib import Path

import pytest
import yaml

from netnewswire_to_obsidian.config import load_config


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file."""
    config_path = tmp_path / "config.yaml"

    def _write(data):
        config_path.write_text(yaml.dump(data))
        return config_path

    return _write


def test_load_config_from_file(config_file, tmp_path):
    output_dir = tmp_path / "output"
    path = config_file({"output_dir": str(output_dir), "accounts": ["iCloud"]})
    config = load_config(config_path=path)
    assert config.output_dir == output_dir
    assert config.accounts == ["iCloud"]
    assert config.interval_minutes == 30


def test_load_config_cli_overrides(config_file, tmp_path):
    output_dir = tmp_path / "output"
    cli_dir = tmp_path / "cli_output"
    path = config_file({"output_dir": str(output_dir), "accounts": ["iCloud"]})
    config = load_config(
        config_path=path,
        cli_output_dir=str(cli_dir),
        cli_accounts=["OnMyMac"],
    )
    assert config.output_dir == cli_dir
    assert config.accounts == ["OnMyMac"]


def test_load_config_missing_output_dir(config_file):
    path = config_file({})
    with pytest.raises(ValueError, match="output_dir is required"):
        load_config(config_path=path)


def test_load_config_nonexistent_file(tmp_path):
    path = tmp_path / "nonexistent.yaml"
    with pytest.raises(ValueError, match="output_dir is required"):
        load_config(config_path=path)


def test_load_config_expands_tilde(config_file):
    path = config_file({"output_dir": "~/some/path"})
    config = load_config(config_path=path)
    assert "~" not in str(config.output_dir)
    assert config.output_dir == Path.home() / "some" / "path"


def test_load_config_custom_interval(config_file, tmp_path):
    path = config_file({
        "output_dir": str(tmp_path / "output"),
        "interval_minutes": 60,
    })
    config = load_config(config_path=path)
    assert config.interval_minutes == 60


def test_load_config_default_accounts_empty(config_file, tmp_path):
    path = config_file({"output_dir": str(tmp_path / "output")})
    config = load_config(config_path=path)
    assert config.accounts == []
