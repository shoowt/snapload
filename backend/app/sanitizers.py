import re
import unicodedata
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

TRACKING_QUERY_PARAMS = {
    # Generic analytics
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "ref", "ref_src", "ref_url", "_ga", "_gl",
    # Instagram
    "igsh", "img_index", "ig_rid", "ig_mid",
    # TikTok
    "is_from_webapp", "sender_device", "share_id", "_r", "_d", "checksum",
    "tt_from", "source", "u_code", "preview_pb",
    # YouTube
    "si", "feature", "pp", "app",
    # Twitter / X
    "s", "t", "cn",
    # Facebook
    "mibextid", "extid", "context"
}

PLATFORM_PATTERNS = [
    ("tiktok", re.compile(r"(?:https?:\/\/)?(?:www\.|vt\.|vm\.|m\.)?tiktok\.com\/.*", re.IGNORECASE)),
    ("instagram", re.compile(r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:reel|p|tv|stories)\/.*", re.IGNORECASE)),
    ("youtube", re.compile(r"(?:https?:\/\/)?(?:www\.|m\.)?(?:youtube\.com|youtu\.be)\/.*", re.IGNORECASE)),
    ("twitter", re.compile(r"(?:https?:\/\/)?(?:www\.|mobile\.)?(?:twitter\.com|x\.com)\/.*", re.IGNORECASE)),
    ("facebook", re.compile(r"(?:https?:\/\/)?(?:www\.|m\.|web\.)?(?:facebook\.com|fb\.watch)\/.*", re.IGNORECASE)),
    ("threads", re.compile(r"(?:https?:\/\/)?(?:www\.)?threads\.net\/.*", re.IGNORECASE)),
]


def sanitize_url(raw_url: str) -> str:
    """
    Cleans leading/trailing characters and removes all known tracking and referral parameters.
    """
    if not raw_url:
        return ""
    
    # Trim and remove wrapping quotes or angle brackets commonly pasted from messaging apps
    url = raw_url.strip().strip("<>\"' \t\r\n")

    # Add https:// if scheme is missing but looks like a domain
    if not re.match(r"^https?:\/\/", url, re.IGNORECASE):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return raw_url.strip()

        # Parse query params, filtering out tracking tokens
        query_dict = parse_qs(parsed.query, keep_blank_values=False)
        clean_query_dict = {
            k: v for k, v in query_dict.items()
            if k.lower() not in TRACKING_QUERY_PARAMS
        }

        # Handle YouTube timestamp (t parameter) if present so we don't accidentally remove time offset
        if "t" in query_dict and ("youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc):
            clean_query_dict["t"] = query_dict["t"]

        clean_query = urlencode(clean_query_dict, doseq=True)
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            clean_query,
            ""  # remove fragment like #_=_
        ))
        return clean_url
    except Exception:
        return raw_url.strip()


def detect_platform(url: str) -> str:
    """
    Identifies the target social platform from the URL.
    """
    if not url:
        return "other"
    
    for platform_key, pattern in PLATFORM_PATTERNS:
        if pattern.search(url):
            return platform_key
            
    return "other"


def sanitize_filename(title: str, ext: str = "mp4", max_len: int = 60) -> str:
    """
    Produces a safe, clean filename for mobile download and Content-Disposition headers.
    """
    if not title:
        title = "video"

    # Normalize unicode to ASCII equivalent or remove unsafe characters
    title = unicodedata.normalize("NFKD", title)
    title = title.encode("ascii", "ignore").decode("ascii")

    # Replace invalid filesystem characters with underscores
    clean = re.sub(r'[\\/*?:"<>|#%&{}\\<>*?/$!\'":@+`|=]', " ", title)
    # Collapse multiple whitespaces
    clean = re.sub(r"\s+", " ", clean).strip()

    if not clean:
        clean = "snapload_video"

    # Truncate if too long
    if len(clean) > max_len:
        clean = clean[:max_len].rstrip()

    clean_ext = ext.lstrip(".")
    return f"{clean}.{clean_ext}"
