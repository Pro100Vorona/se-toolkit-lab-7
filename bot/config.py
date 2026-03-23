"""Configuration loader - reads secrets from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_config() -> dict:
    """Load configuration from .env.bot.secret file.
    
    Returns a dict with keys: BOT_TOKEN, LMS_API_URL, LMS_API_KEY, LLM_API_KEY
    """
    # Find the .env.bot.secret file (look in parent directory from bot/)
    env_path = Path(__file__).parent.parent / ".env.bot.secret"
    
    if env_path.exists():
        load_dotenv(env_path)
    
    return {
        "BOT_TOKEN": os.getenv("BOT_TOKEN", ""),
        "LMS_API_URL": os.getenv("LMS_API_URL", "http://localhost:42002"),
        "LMS_API_KEY": os.getenv("LMS_API_KEY", ""),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
    }
