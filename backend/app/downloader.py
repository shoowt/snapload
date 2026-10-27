import os
import uuid
import asyncio
from typing import AsyncGenerator, Optional
import httpx
from fastapi import HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
import yt_dlp

from .config import (
    DEFAULT_USER_AGENT,
    STREAM_CHUNK_SIZE,
    DOWNLOAD_TIMEOUT_SECONDS,
    TEMP_DOWNLOAD_DIR,
    PLATFORM_INFO
)
from .sanitizers import sanitize_url, detect_platform, sanitize_filename


def cleanup_file(path: str):
    """Deletes temporary file safely after streaming completes."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


async def stream_from_cdn(
    direct_url: str,
    platform: str,
    filename: str,
    media_type: str = "video/mp4"
) -> StreamingResponse:
    """
    Proxies and streams direct CDN bytes to client with forced attachment header.
    Allows mobile browsers to directly save into files/gallery.
    """
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
    }
    
    platform_data = PLATFORM_INFO.get(platform, {})
    referer = platform_data.get("default_referer")
    if referer:
        headers["Referer"] = referer

    client = httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=True)

    try:
        req = client.build_request("GET", direct_url, headers=headers)
        response = await client.send(req, stream=True)

        if response.status_code >= 400:
            await response.aclose()
            await client.aclose()
            raise HTTPException(
                status_code=502,
                detail=f"Servidor upstream retornou erro HTTP {response.status_code}"
            )

        content_length = response.headers.get("content-length")

        async def stream_generator() -> AsyncGenerator[bytes, None]:
            try:
                async for chunk in response.aiter_bytes(chunk_size=STREAM_CHUNK_SIZE):
                    yield chunk
            finally:
                await response.aclose()
                await client.aclose()

        response_headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
        if content_length:
            response_headers["Content-Length"] = content_length

        return StreamingResponse(
            stream_generator(),
            media_type=media_type,
            headers=response_headers
        )

    except httpx.RequestError as e:
        await client.aclose()
        raise HTTPException(
            status_code=502,
            detail=f"Falha de conexão com CDN de mídia: {str(e)}"
        )


def _download_and_merge_sync(
    url: str,
    output_template: str,
    format_id: Optional[str] = None,
    is_audio: bool = False
) -> str:
    """Synchronous worker that downloads and merges with yt-dlp."""
    platform = detect_platform(url)
    platform_data = PLATFORM_INFO.get(platform, {})
    referer = platform_data.get("default_referer")

    http_headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
    }
    if referer:
        http_headers["Referer"] = referer

    if is_audio:
        ydl_format = "bestaudio/best"
    elif format_id and format_id != "best":
        # Format id specified, combine with best audio if video-only
        ydl_format = f"{format_id}+bestaudio/best"
    else:
        # Best clean video and best audio merged into mp4
        ydl_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

    ydl_opts = {
        "format": ydl_format,
        "outtmpl": output_template,
        "merge_output_format": "mp4" if not is_audio else "mp3",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "http_headers": http_headers,
    }

    if is_audio:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the generated file (extension might differ depending on postprocessing)
    base_stem = os.path.splitext(output_template)[0]
    parent_dir = os.path.dirname(output_template)
    for fname in os.listdir(parent_dir):
        if fname.startswith(os.path.basename(base_stem)):
            return os.path.join(parent_dir, fname)

    return output_template


async def download_via_ytdlp(
    url: str,
    title: str,
    format_id: Optional[str] = None,
    is_audio: bool = False,
    background_tasks: Optional[BackgroundTasks] = None
) -> FileResponse:
    """
    Downloads via yt-dlp (merging with ffmpeg if available), saves to temp file,
    and returns a FileResponse with auto-deletion background task.
    """
    clean_url = sanitize_url(url)
    ext = "mp3" if is_audio else "mp4"
    filename = sanitize_filename(title, ext=ext)

    unique_id = uuid.uuid4().hex
    target_pattern = str(TEMP_DOWNLOAD_DIR / f"{unique_id}.%(ext)s")

    loop = asyncio.get_running_loop()
    try:
        final_file_path = await loop.run_in_executor(
            None,
            _download_and_merge_sync,
            clean_url,
            target_pattern,
            format_id,
            is_audio
        )

        if not os.path.exists(final_file_path):
            raise HTTPException(
                status_code=500,
                detail="Erro ao processar arquivo para download."
            )

        if background_tasks:
            background_tasks.add_task(cleanup_file, final_file_path)

        media_type = "audio/mpeg" if is_audio else "video/mp4"

        return FileResponse(
            path=final_file_path,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Não foi possível baixar esta mídia: {str(e)}"
        )
