import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
import yt_dlp
from curl_cffi.requests import AsyncSession, RequestsError

from .config import DEFAULT_USER_AGENT, PLATFORM_INFO
from .sanitizers import sanitize_url, detect_platform

logger = logging.getLogger(__name__)

# Try importing ImpersonateTarget for anti-bot bypass
try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
    HAS_IMPERSONATION = True
except ImportError:
    HAS_IMPERSONATION = False


def format_duration(seconds: Optional[float]) -> str:
    """Formats numeric seconds into MM:SS or HH:MM:SS."""
    if seconds is None or seconds <= 0:
        return "N/A"
    
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    sec = total_sec % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def format_filesize(bytes_val: Optional[int]) -> str:
    """Converts bytes to readable MB / KB representation."""
    if not bytes_val or bytes_val <= 0:
        return ""
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024 * 1024):.1f} GB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    return f"{bytes_val / 1024:.0f} KB"


def build_ydl_opts(platform: str, user_agent: Optional[str] = None) -> Dict[str, Any]:
    """
    Builds yt-dlp extraction options optimized for fast metadata retrieval,
    anti-bot impersonation (curl-cffi), and clean watermark-free streams.
    """
    ua = user_agent or DEFAULT_USER_AGENT
    http_headers = {
        "User-Agent": ua,
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Mode": "navigate",
    }

    platform_data = PLATFORM_INFO.get(platform, {})
    referer = platform_data.get("default_referer")
    if referer:
        http_headers["Referer"] = referer

    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": False,
        "skip_download": True,
        "socket_timeout": 20,
        "http_headers": http_headers,
        "extractor_args": {
            "tiktok": {
                "app_version": ["current"],
            },
            "youtube": {
                "player_client": ["android", "web"],
            }
        }
    }

    if HAS_IMPERSONATION:
        try:
            opts["impersonate"] = ImpersonateTarget("chrome")
        except Exception:
            pass

    return opts


def filter_and_label_formats(raw_formats: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
    """
    Filters and prioritizes watermark-free video streams and audio streams.
    Generates user-friendly labels (e.g. '1080p Sem Marca d'Água', '720p HD', 'Áudio MP3').
    """
    if not raw_formats:
        return []

    video_formats = []
    audio_formats = []

    for fmt in raw_formats:
        fmt_id = str(fmt.get("format_id", ""))
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        height = fmt.get("height")
        filesize = fmt.get("filesize") or fmt.get("filesize_approx")
        url = fmt.get("url")
        note = fmt.get("format_note", "") or ""

        if not url:
            continue

        is_video = vcodec != "none" and vcodec is not None
        is_audio = acodec != "none" and acodec is not None
        is_watermarked = "watermark" in fmt_id.lower() or "watermark" in note.lower()

        # Reject watermarked streams for TikTok
        if platform == "tiktok" and is_watermarked:
            continue

        if is_video:
            res_str = f"{height}p" if height else "HD"
            label = f"{res_str} - MP4"
            if platform in ("tiktok", "instagram"):
                label = f"{res_str} Sem Marca d'Água"

            video_formats.append({
                "format_id": fmt_id,
                "type": "video",
                "label": label,
                "resolution": res_str,
                "height": height or 0,
                "ext": "mp4",
                "filesize_bytes": filesize,
                "filesize_readable": format_filesize(filesize),
                "is_clean": not is_watermarked,
                "has_audio": is_audio,
                "fps": fmt.get("fps"),
                "url": url,
            })
        elif is_audio and not is_video:
            abr = fmt.get("abr")
            abr_str = f"{int(abr)}kbps" if abr else "128kbps"
            audio_formats.append({
                "format_id": fmt_id,
                "type": "audio",
                "label": f"Áudio MP3 / M4A ({abr_str})",
                "resolution": "Áudio",
                "height": 0,
                "ext": "mp3",
                "filesize_bytes": filesize,
                "filesize_readable": format_filesize(filesize),
                "is_clean": True,
                "has_audio": True,
                "url": url,
            })

    # Sort video formats by height descending
    video_formats.sort(key=lambda x: (x["height"], x["filesize_bytes"] or 0), reverse=True)

    seen_heights = set()
    cleaned_videos = []
    
    if video_formats:
        best_format = dict(video_formats[0])
        best_format["label"] = "Sem Marca d'Água (Original / HD)"
        best_format["is_primary"] = True
        cleaned_videos.append(best_format)
        seen_heights.add(best_format["height"])

    for vf in video_formats:
        h = vf["height"]
        if h and h not in seen_heights and h >= 360:
            seen_heights.add(h)
            vf["is_primary"] = False
            cleaned_videos.append(vf)

    # Sort audio by bitrate descending
    audio_formats.sort(key=lambda x: x["filesize_bytes"] or 0, reverse=True)
    cleaned_audios = audio_formats[:1] if audio_formats else []
    if not cleaned_audios:
        cleaned_audios.append({
            "format_id": "bestaudio/best",
            "type": "audio",
            "label": "Áudio do Vídeo (MP3)",
            "resolution": "Áudio",
            "height": 0,
            "ext": "mp3",
            "filesize_bytes": None,
            "filesize_readable": "",
            "is_clean": True,
            "has_audio": True,
            "url": None
        })

    return cleaned_videos + cleaned_audios


def _extract_sync(url: str, platform: str) -> Dict[str, Any]:
    """Synchronous worker function to run yt-dlp in a separate thread."""
    ydl_opts = build_ydl_opts(platform)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


async def extract_tiktok_fallback(url: str) -> Optional[Dict[str, Any]]:
    """
    Direct API fallback for TikTok in case of aggressive ByteDance challenge cookies.
    Extracts 100% clean, watermark-free HD stream directly from CDN.
    """
    try:
        async with AsyncSession(timeout=12.0, impersonate="chrome") as client:
            vdata = None
            # HD can be unavailable while the provider prepares the video.
            # Retry once at standard quality instead of discarding a valid link.
            for method, hd in (("GET", 1), ("POST", 0)):
                if hd == 0:
                    await asyncio.sleep(1.1)
                try:
                    params = {"url": url, "hd": hd}
                    resp = await client.request(
                        method, "https://www.tikwm.com/api/",
                        **({"params": params} if method == "GET" else {"data": params}),
                        headers={"Referer": "https://www.tikwm.com/"}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    candidate = data.get("data")
                    if data.get("code") == 0 and isinstance(candidate, dict) and (
                        candidate.get("hdplay") or candidate.get("play")
                    ):
                        vdata = candidate
                        break
                    logger.warning("TikTok fallback %s hd=%s rejected: code=%s message=%s",
                                   method, hd, data.get("code"), str(data.get("msg", ""))[:300])
                except (httpx.HTTPError, RequestsError, ValueError) as exc:
                    logger.warning("TikTok fallback %s hd=%s failed: %s", method, hd, exc)
            if vdata is None:
                return None

            clean_video_url = vdata.get("hdplay") or vdata.get("play")
            music_url = vdata.get("music")
            author = vdata.get("author", {}).get("nickname") or vdata.get("author", {}).get("unique_id") or "TikToker"
            title = vdata.get("title") or "Vídeo TikTok"
            duration = vdata.get("duration", 0)
            cover = vdata.get("cover") or vdata.get("origin_cover")

            formats = [
                {
                    "format_id": "hdplay" if vdata.get("hdplay") else "play",
                    "type": "video",
                    "label": "Sem Marca d'Água (Original / HD)",
                    "resolution": "HD",
                    "height": 1080 if vdata.get("hdplay") else 720,
                    "ext": "mp4",
                    "filesize_bytes": vdata.get("size"),
                    "filesize_readable": format_filesize(vdata.get("size")),
                    "is_clean": True,
                    "has_audio": True,
                    "is_primary": True,
                    "url": clean_video_url
                }
            ]

            if music_url:
                formats.append({
                    "format_id": "music",
                    "type": "audio",
                    "label": f"Áudio Original (MP3)",
                    "resolution": "Áudio",
                    "height": 0,
                    "ext": "mp3",
                    "filesize_bytes": None,
                    "filesize_readable": "",
                    "is_clean": True,
                    "has_audio": True,
                    "url": music_url
                })

            return {
                "success": True,
                "id": str(vdata.get("id")),
                "title": title,
                "description": title,
                "thumbnail": cover,
                "duration": format_duration(duration),
                "duration_seconds": duration,
                "platform": "tiktok",
                "platform_name": "TikTok",
                "platform_color": "#FE2C55",
                "platform_icon": "tiktok",
                "author": author,
                "original_url": url,
                "formats": formats
            }
    except Exception as e:
        print(f"TikTok fallback error: {e}")
        return None


async def extract_video_info(raw_url: str) -> Dict[str, Any]:
    """
    Async wrapper for URL extraction with anti-bot bypass and multi-tier fallback.
    """
    clean_url = sanitize_url(raw_url)
    if not clean_url:
        raise ValueError("A URL informada está vazia.")

    platform = detect_platform(clean_url)
    platform_data = PLATFORM_INFO.get(platform, PLATFORM_INFO["other"])

    # Attempt 1: yt-dlp with impersonation
    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, _extract_sync, clean_url, platform)

        if info:
            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            title = info.get("title") or "Vídeo sem título"
            duration_sec = info.get("duration")
            thumbnail = info.get("thumbnail") or ""
            author = info.get("uploader") or info.get("channel") or info.get("creator") or platform_data["name"]
            description = info.get("description") or ""
            if len(description) > 150:
                description = description[:147] + "..."

            raw_formats = info.get("formats", [])
            formats = filter_and_label_formats(raw_formats, platform)

            if not formats and info.get("url"):
                formats = [{
                    "format_id": "best",
                    "type": "video",
                    "label": "Download Direto (Sem Marca d'Água)",
                    "resolution": "HD",
                    "height": info.get("height", 720),
                    "ext": info.get("ext", "mp4"),
                    "filesize_bytes": info.get("filesize"),
                    "filesize_readable": format_filesize(info.get("filesize")),
                    "is_clean": True,
                    "has_audio": True,
                    "is_primary": True,
                    "url": info.get("url"),
                }]

            return {
                "success": True,
                "id": info.get("id"),
                "title": title,
                "description": description,
                "thumbnail": thumbnail,
                "duration": format_duration(duration_sec),
                "duration_seconds": duration_sec,
                "platform": platform,
                "platform_name": platform_data["name"],
                "platform_color": platform_data["color"],
                "platform_icon": platform_data["icon"],
                "author": author,
                "original_url": clean_url,
                "formats": formats
            }

    except Exception as ytdlp_err:
        print(f"yt-dlp primary extraction failed: {ytdlp_err}")

        # Attempt 2: If TikTok, trigger direct clean stream fallback
        if platform == "tiktok":
            fallback_result = await extract_tiktok_fallback(clean_url)
            if fallback_result:
                return fallback_result

        # Parse error for user friendly feedback
        msg = str(ytdlp_err)
        lower_msg = msg.lower()
        if any(marker in lower_msg for marker in ("429", "too many requests", "rate-limit", "rate limit")):
            friendly_error = "A plataforma limitou temporariamente as requisições. Aguarde alguns minutos antes de tentar novamente."
        elif any(marker in lower_msg for marker in ("bot", "blocked", "403", "forbidden", "challenge")):
            friendly_error = "A plataforma bloqueou o acesso automático a este vídeo. Tentar novamente em instantes pode não resolver."
        elif "status code 0" in lower_msg or "timed out" in lower_msg or "connection" in lower_msg:
            friendly_error = "Não foi possível conectar à plataforma do vídeo. Verifique a conexão e tente novamente mais tarde."
        elif "private video" in lower_msg or "private account" in lower_msg or "login" in lower_msg:
            friendly_error = "Este vídeo é de uma conta privada ou restrita. Apenas vídeos de perfis públicos podem ser baixados."
        elif "Video unavailable" in msg or "not found" in msg.lower() or "deleted" in msg.lower():
            friendly_error = "O vídeo não foi encontrado. Pode ter sido removido ou o link está incorreto."
        elif "Unsupported URL" in msg or "not a valid URL" in msg.lower():
            friendly_error = "Link não suportado ou inválido. Verifique o link e tente novamente."
        else:
            friendly_error = "Não foi possível processar o vídeo. Verifique se o link é público e tente novamente."

        return {
            "success": False,
            "error": friendly_error,
            "details": msg,
            "platform": platform
        }
