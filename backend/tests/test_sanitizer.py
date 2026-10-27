from backend.app.sanitizers import sanitize_url, detect_platform, sanitize_filename


def test_sanitize_instagram_url():
    url = "https://www.instagram.com/reel/C7oBvNpxyz/?igsh=MWF2NmRoMzN3Z3lhYg==&utm_source=qr"
    clean = sanitize_url(url)
    assert "igsh" not in clean
    assert "utm_source" not in clean
    assert "https://www.instagram.com/reel/C7oBvNpxyz/" in clean
    assert detect_platform(clean) == "instagram"


def test_sanitize_tiktok_url():
    url = "https://www.tiktok.com/@user/video/7381234567890123456?is_from_webapp=1&sender_device=pc&share_id=123456"
    clean = sanitize_url(url)
    assert "is_from_webapp" not in clean
    assert "sender_device" not in clean
    assert "share_id" not in clean
    assert "https://www.tiktok.com/@user/video/7381234567890123456" in clean
    assert detect_platform(clean) == "tiktok"


def test_sanitize_youtube_url():
    url = "https://youtu.be/dQw4w9WgXcQ?si=abcdef123456&t=30"
    clean = sanitize_url(url)
    assert "si=" not in clean
    assert "t=30" in clean  # Timestamp preserved
    assert detect_platform(clean) == "youtube"


def test_sanitize_filename():
    unsafe_title = 'Vídeo Épico! / Como Fazer? <Tutorial> *2026* | #shorts'
    clean_name = sanitize_filename(unsafe_title, ext="mp4")
    assert "/" not in clean_name
    assert "?" not in clean_name
    assert "<" not in clean_name
    assert ">" not in clean_name
    assert "*" not in clean_name
    assert "|" not in clean_name
    assert clean_name.endswith(".mp4")


if __name__ == "__main__":
    test_sanitize_instagram_url()
    test_sanitize_tiktok_url()
    test_sanitize_youtube_url()
    test_sanitize_filename()
    print("Todos os testes de sanitização passaram com sucesso!")
