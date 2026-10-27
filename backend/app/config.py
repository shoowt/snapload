import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
TEMP_DOWNLOAD_DIR = BASE_DIR / "temp_downloads"
TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Application settings
APP_NAME = "SnapLoad API"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Streaming proxy settings
STREAM_CHUNK_SIZE = 1024 * 128  # 128 KB
DOWNLOAD_TIMEOUT_SECONDS = 300

# Common User Agents to bypass platform restrictions and bot checks
USER_AGENTS = [
    # Chrome Mobile (Android)
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    # Safari Mobile (iOS iPhone)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    # Chrome Desktop (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Mac Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
]

DEFAULT_USER_AGENT = USER_AGENTS[0]

# Platform Identifiers
PLATFORM_INFO = {
    "tiktok": {
        "name": "TikTok",
        "icon": "tiktok",
        "color": "#FE2C55",
        "clean_watermark_supported": True,
        "default_referer": "https://www.tiktok.com/"
    },
    "instagram": {
        "name": "Instagram",
        "icon": "instagram",
        "color": "#E1306C",
        "clean_watermark_supported": True,
        "default_referer": "https://www.instagram.com/"
    },
    "youtube": {
        "name": "YouTube",
        "icon": "youtube",
        "color": "#FF0000",
        "clean_watermark_supported": True,
        "default_referer": "https://www.youtube.com/"
    },
    "twitter": {
        "name": "X / Twitter",
        "icon": "twitter",
        "color": "#1DA1F2",
        "clean_watermark_supported": True,
        "default_referer": "https://twitter.com/"
    },
    "facebook": {
        "name": "Facebook",
        "icon": "facebook",
        "color": "#1877F2",
        "clean_watermark_supported": True,
        "default_referer": "https://www.facebook.com/"
    },
    "threads": {
        "name": "Threads",
        "icon": "threads",
        "color": "#000000",
        "clean_watermark_supported": True,
        "default_referer": "https://www.threads.net/"
    },
    "other": {
        "name": "Outro",
        "icon": "video",
        "color": "#6366F1",
        "clean_watermark_supported": True,
        "default_referer": ""
    }
}
