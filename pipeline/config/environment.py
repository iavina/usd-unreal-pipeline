"""Load local development environment variables for pipeline commands."""

from pathlib import Path

from dotenv import load_dotenv


def load_local_env() -> None:
    """Load project-local environment variables from `.env` when present."""
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
