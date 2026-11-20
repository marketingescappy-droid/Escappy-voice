from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def database_path() -> Path:
    from os import getenv

    local_config = dotenv_values(PROJECT_ROOT / ".env")
    configured = getenv("ESCAPPY_DB_PATH") or local_config.get("ESCAPPY_DB_PATH")
    return PROJECT_ROOT / Path(configured or "data/escappy.sqlite3").expanduser()
