import os
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from .config import APP_NAME, APP_VERSION, FRONTEND_DIR, PLATFORM_INFO
from .sanitizers import sanitize_url, detect_platform, sanitize_filename
from .extractor import extract_video_info
from .downloader import stream_from_cdn, download_via_ytdlp

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API de alta performance para download de vídeos sem marca d'água de redes sociais."
)

# Enable CORS for cross-origin access and mobile PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    url: str


@app.get("/api/health")
async def health_check():
    """Health check and supported platform listing."""
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION,
        "supported_platforms": list(PLATFORM_INFO.keys())
    }


@app.post("/api/info")
async def get_video_info(payload: ExtractRequest):
    """
    Receives social media URL, cleans tracking parameters,
    and returns metadata along with clean, non-watermarked stream options.
    """
    raw_url = payload.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="Por favor, forneça uma URL válida.")

    result = await extract_video_info(raw_url)
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Erro ao processar URL")
        )

    return result


@app.get("/api/download")
async def download_media(
    url: str = Query(..., description="URL original do vídeo"),
    direct_url: Optional[str] = Query(None, description="URL direta da stream CDN extraída"),
    format_id: Optional[str] = Query("best", description="ID do formato ou 'best'"),
    title: Optional[str] = Query("video", description="Título para o nome do arquivo"),
    is_audio: bool = Query(False, description="Baixar apenas áudio"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Streaming proxy route forcing 'Content-Disposition: attachment'
    so mobile browsers immediately save the file into Gallery/Files.
    """
    clean_url = sanitize_url(url)
    if not clean_url:
        raise HTTPException(status_code=400, detail="URL inválida.")

    platform = detect_platform(clean_url)
    ext = "mp3" if is_audio else "mp4"
    safe_name = sanitize_filename(title or "video", ext=ext)

    # If direct_url is supplied and valid, stream via high-performance CDN proxy
    if direct_url and not is_audio and direct_url.startswith("http"):
        media_type = "video/mp4"
        return await stream_from_cdn(
            direct_url=direct_url,
            platform=platform,
            filename=safe_name,
            media_type=media_type
        )

    # Otherwise fallback to yt-dlp download & merge with background file cleanup
    return await download_via_ytdlp(
        url=clean_url,
        title=title or "video",
        format_id=format_id,
        is_audio=is_audio,
        background_tasks=background_tasks
    )


# PWA and Static File Servicing
@app.get("/sw.js")
async def service_worker():
    sw_path = FRONTEND_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(
            sw_path,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"}
        )
    raise HTTPException(status_code=404, detail="Service worker not found")


@app.get("/manifest.json")
async def pwa_manifest():
    manifest_path = FRONTEND_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(
            manifest_path,
            media_type="application/manifest+json"
        )
    raise HTTPException(status_code=404, detail="Manifest not found")


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not found, access /api/health"}
