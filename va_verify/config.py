"""
Configuration for VA API clients.

Set credentials via environment variables or a .env file:
  VA_API_KEY          - API key for the Veteran Confirmation API
  VA_ENV              - "sandbox" (default) or "production"
"""

import os

# Base URLs per environment
_BASE_URLS = {
    "sandbox": "https://sandbox-api.va.gov",
    "production": "https://api.va.gov",
}


def get_env() -> str:
    """Return the active environment name."""
    env = os.environ.get("VA_ENV", "sandbox").lower()
    if env not in _BASE_URLS:
        raise ValueError(f"VA_ENV must be 'sandbox' or 'production', got: {env!r}")
    return env


def get_base_url() -> str:
    return _BASE_URLS[get_env()]


def get_api_key() -> str | None:
    """Return the API key, or None if not set."""
    return os.environ.get("VA_API_KEY")


def require_api_key() -> str:
    """Return the API key, raising if not configured."""
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "VA_API_KEY environment variable is not set.\n"
            "Set it before running:\n"
            "  export VA_API_KEY=your_key_here\n"
            "or add it to a .env file and load it first."
        )
    return key
