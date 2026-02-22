from __future__ import annotations

import configparser
from pathlib import Path

from repo import git_dir


def _config_path(repo_root: Path) -> Path:
    return git_dir(repo_root) / "config"


def _load_config(repo_root: Path) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    path = _config_path(repo_root)
    if path.exists():
        config.read(path, encoding="utf-8")
    return config


def _write_config(repo_root: Path, config: configparser.ConfigParser) -> None:
    path = _config_path(repo_root)
    with path.open("w", encoding="utf-8") as handle:
        config.write(handle)


def _remote_section(name: str) -> str:
    return f'remote "{name}"'


def list_remotes(repo_root: Path) -> dict[str, str]:
    config = _load_config(repo_root)
    remotes: dict[str, str] = {}
    for section in config.sections():
        if not section.startswith('remote "') or not section.endswith('"'):
            continue
        name = section[len('remote "') : -1]
        url = config.get(section, "url", fallback="").strip()
        if url:
            remotes[name] = url
    return remotes


def add_remote(repo_root: Path, name: str, url: str) -> None:
    config = _load_config(repo_root)
    section = _remote_section(name)
    if config.has_section(section):
        raise ValueError(f"remote '{name}' already exists")
    config.add_section(section)
    config.set(section, "url", url)
    _write_config(repo_root, config)


def remove_remote(repo_root: Path, name: str) -> None:
    config = _load_config(repo_root)
    section = _remote_section(name)
    if not config.remove_section(section):
        raise ValueError(f"remote '{name}' does not exist")
    _write_config(repo_root, config)


def get_remote_url(repo_root: Path, name: str) -> str:
    remotes = list_remotes(repo_root)
    url = remotes.get(name)
    if not url:
        raise ValueError(f"remote '{name}' does not exist")
    return url

