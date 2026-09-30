"""Read backend-only local configuration without exposing credential values."""

import os
from pathlib import Path


BACKEND_ENV_PATH = Path(__file__).resolve().parent / ".env"


def get_geoapify_api_key() -> str | None:
    """Use the process environment first, then backend/.env if it exists."""
    value = os.environ.get("GEOAPIFY_API_KEY", "").strip()
    if value:
        return None if value == "your_key_here" else value

    try:
        with BACKEND_ENV_PATH.open(encoding="utf-8") as environment_file:
            for line in environment_file:
                name, separator, raw_value = line.partition("=")
                if not separator or name.strip().removeprefix("export ").strip() != "GEOAPIFY_API_KEY":
                    continue
                value = raw_value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1].strip()
                return value if value and value != "your_key_here" else None
    except (OSError, UnicodeError):
        return None
    return None
