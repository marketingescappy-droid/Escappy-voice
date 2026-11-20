from dataclasses import dataclass, field
from os import environ
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def database_path() -> Path:
    local_config = dotenv_values(PROJECT_ROOT / ".env")
    configured = environ.get("ESCAPPY_DB_PATH") or local_config.get("ESCAPPY_DB_PATH")
    return PROJECT_ROOT / Path(configured or "data/escappy.sqlite3").expanduser()


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str = field(repr=False)
    model: str = "gpt-4.1-mini"


def openai_settings() -> OpenAISettings:
    local = dotenv_values(PROJECT_ROOT / ".env")
    return OpenAISettings(
        api_key=(environ.get("OPENAI_API_KEY", local.get("OPENAI_API_KEY")) or "").strip(),
        model=(environ.get("ESCAPPY_AI_MODEL", local.get("ESCAPPY_AI_MODEL")) or "").strip()
        or "gpt-4.1-mini",
    )
