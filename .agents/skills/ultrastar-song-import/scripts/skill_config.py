"""Defaults for the song import skill, read from the skill's .env file.

Precedence: command-line flag, then process environment, then .env. The file is
optional. Values may use %VAR% or $VAR references, which are expanded when read.
"""

from __future__ import annotations

import os
from pathlib import Path

from chart_core import ChartError, safe_name

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = SKILL_DIR / ".env"
LIBRARY_KEY = "ULTRASTAR_LIBRARY"
WORK_ROOT_KEY = "ULTRASTAR_WORK_ROOT"
DEFAULT_WORK_ROOT = r"%LOCALAPPDATA%\UltraStarSongImport"


def parse_env(text: str) -> dict[str, str]:
    values = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def read_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    if not path.is_file():
        return {}
    return parse_env(path.read_text(encoding="utf-8-sig"))


def setting(name: str, file_values: dict[str, str]) -> str | None:
    raw = os.environ.get(name) or file_values.get(name)
    if not raw:
        return None
    expanded = os.path.expandvars(raw)
    if "%" in expanded:
        raise ChartError(f"{name} refers to an unset variable: {raw}")
    return expanded


def library_folder(flag: str | None, file_values: dict[str, str]) -> Path:
    raw = flag or setting(LIBRARY_KEY, file_values)
    if not raw:
        raise ChartError(f"No song library given; pass --library or set {LIBRARY_KEY} in {ENV_FILE.name}")
    library = Path(raw)
    if not library.is_dir():
        raise ChartError(f"Song library folder not found: {library}")
    return library


def work_root(file_values: dict[str, str]) -> Path:
    raw = setting(WORK_ROOT_KEY, file_values) or os.path.expandvars(DEFAULT_WORK_ROOT)
    if "%" in raw:
        raise ChartError(f"Set {WORK_ROOT_KEY} in {ENV_FILE.name}; the default needs LOCALAPPDATA")
    return Path(raw)


def default_work_folder(artist: str, title: str, file_values: dict[str, str]) -> Path:
    return work_root(file_values) / safe_name(f"{artist}-{title}")
