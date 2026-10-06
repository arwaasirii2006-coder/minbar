from __future__ import annotations

import os
from functools import lru_cache

from services.config import openai_timeout_seconds


class AIUnavailable(RuntimeError):
    """Raised when the OpenAI key is missing; callers degrade instead of crashing."""


@lru_cache(maxsize=1)
def _client(api_key: str):
    from openai import OpenAI

    return OpenAI(api_key=api_key, timeout=openai_timeout_seconds(), max_retries=2)


def get_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise AIUnavailable("OPENAI_API_KEY is not configured.")
    return _client(api_key)
