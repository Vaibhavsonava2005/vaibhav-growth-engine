"""
settings.py
-----------
Centralised application settings for VAIBHAV GROWTH ENGINE.

All values are loaded from environment variables or a .env file located in the
project root.  A module-level singleton ``settings`` is exported so that every
module can simply do::

    from src.config.settings import settings

and access any configuration value without re-parsing the environment.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Pydantic BaseSettings that automatically reads environment variables and
    an optional ``.env`` file.  All fields have sensible defaults so the
    application can still start in a development environment without every
    variable being set.
    """

    # ------------------------------------------------------------------ #
    #  External API keys                                                   #
    # ------------------------------------------------------------------ #
    APOLLO_API_KEY: str = ""
    PROSPEO_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    BREVO_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # ------------------------------------------------------------------ #
    #  Email / sender identity                                             #
    # ------------------------------------------------------------------ #
    SENDER_EMAIL: str = "vaibhav@deknek.com"
    SENDER_NAME: str = "Vaibhav Sonava"

    # ------------------------------------------------------------------ #
    #  Operational limits                                                  #
    # ------------------------------------------------------------------ #
    MAX_COMPANIES: int = 10
    MAX_CONTACTS_PER_COMPANY: int = 3
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30

    # ------------------------------------------------------------------ #
    #  Execution flags                                                     #
    # ------------------------------------------------------------------ #
    DRY_RUN: bool = False

    # ------------------------------------------------------------------ #
    #  Logging                                                             #
    # ------------------------------------------------------------------ #
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------ #
    #  Pydantic model configuration                                        #
    # ------------------------------------------------------------------ #
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# ---------------------------------------------------------------------------
# Module-level singleton – import and use directly
# ---------------------------------------------------------------------------
settings: Settings = Settings()
