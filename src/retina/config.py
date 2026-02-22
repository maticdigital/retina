"""Application configuration loaded from environment variables.

The .env file is the primary source of truth. Empty environment variables
(e.g., from parent shells) are cleared so the .env values take precedence.
"""

from __future__ import annotations

import os

from dotenv import dotenv_values
from pydantic_settings import BaseSettings

# Pre-load .env values and clear empty env vars so .env file wins
_dotenv_vals = dotenv_values(".env")
for _key, _val in _dotenv_vals.items():
    if _val and os.environ.get(_key, None) == "":
        del os.environ[_key]


class Settings(BaseSettings):
    """Retina configuration — loads API keys and settings from .env file."""

    # API keys
    pagespeed_api_key: str
    builtwith_api_key: str
    anthropic_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Claude analysis settings
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 8192

    # API base URLs
    pagespeed_base_url: str = (
        "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
    )
    builtwith_base_url: str = "https://api.builtwith.com/v21/api.json"

    # Screenshot settings
    screenshots_dir: str = "./screenshots"
    screenshot_timeout: int = 30

    # Request settings
    request_timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    max_concurrent_requests: int = 4

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
