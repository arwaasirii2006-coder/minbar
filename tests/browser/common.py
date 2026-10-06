"""Shared settings for the real-browser suites in tests/browser/.

These scripts drive a running Minbar server with Playwright. They are not
collected by pytest (no test_ prefix); run them one by one, see docs/TESTING.md.

Environment:
  MINBAR_TEST_BASE      backend URL            (default http://127.0.0.1:8765)
  MINBAR_TEST_CODE      broadcast code for KHATAM-2026, must match the server's
                        MINBAR_BROADCAST_CODES (default demo-4821)
  MINBAR_TEST_FRONTEND  static dev server URL  (cross_origin.py only,
                        default http://127.0.0.1:5500/frontend)
  MINBAR_BROWSER        Playwright channel, e.g. msedge or chrome. Default: the
                        bundled Chromium (python -m playwright install chromium),
                        falling back to an installed Microsoft Edge.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = os.getenv("MINBAR_TEST_BASE", "http://127.0.0.1:8765").rstrip("/")
CODE = os.getenv("MINBAR_TEST_CODE", "demo-4821")
FRONTEND = os.getenv("MINBAR_TEST_FRONTEND", "http://127.0.0.1:5500/frontend").rstrip("/")
ROOM = "KHATAM-2026"
OUT = REPO / "tests" / "browser" / "output"  # screenshots for manual review (git-ignored)

FAKE_MIC = ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"]


async def launch(pw, args=()):
    channel = os.getenv("MINBAR_BROWSER")
    if channel:
        return await pw.chromium.launch(channel=channel, args=list(args))
    try:
        return await pw.chromium.launch(args=list(args))
    except Exception:
        return await pw.chromium.launch(channel="msedge", args=list(args))


def out_dir(name: str) -> Path:
    path = OUT / name
    path.mkdir(parents=True, exist_ok=True)
    return path
