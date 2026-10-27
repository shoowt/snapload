package com.shoowt.snapload

import org.junit.Assert.*
import org.junit.Test

class InstagramCookiesTest {
    @Test fun headerPreservesEncodedValues() {
        val contents = InstagramCookies.fromHeader("csrftoken=csrf; sessionid=123%3Aabc==; ds_user_id=123")
        assertTrue(contents.contains("\tsessionid\t123%3Aabc==\n"))
        assertTrue(contents.startsWith("# Netscape HTTP Cookie File\n"))
    }
    @Test fun onlyInstagramCookiesAreImported() {
        val contents = InstagramCookies.validate(".example.com\tTRUE\t/\tTRUE\t0\tsecret\tother-site\n#HttpOnly_.instagram.com\tTRUE\t/\tTRUE\t0\tsessionid\ttest-session\n")
        assertFalse(contents.contains("other-site"))
        assertTrue(contents.contains("#HttpOnly_.instagram.com"))
    }
    @Test(expected = IllegalArgumentException::class) fun rejectsMissingSession() {
        InstagramCookies.fromHeader("csrftoken=csrf")
    }
    @Test(expected = IllegalArgumentException::class) fun rejectsExpiredSession() {
        InstagramCookies.validate(".instagram.com\tTRUE\t/\tTRUE\t1\tsessionid\texpired\n")
    }
    @Test(expected = IllegalArgumentException::class) fun rejectsLookalikeDomains() {
        InstagramCookies.validate(".evilinstagram.com\tTRUE\t/\tTRUE\t0\tsessionid\tinvalid\n")
    }
    @Test(expected = IllegalArgumentException::class) fun rejectsMalformedCookieFile() {
        InstagramCookies.validate("sessionid=plain-header")
    }
    @Test fun matchesOnlyInstagramLinks() {
        assertTrue(InstagramCookies.isInstagram("https://www.instagram.com/reel/example/"))
        assertFalse(InstagramCookies.isInstagram("https://instagram.com.evil.example/reel/example/"))
        assertFalse(InstagramCookies.isInstagram("https://example.com/?url=https://instagram.com/"))
    }
    @Test fun instagramLoginErrorsGiveAnActionWithoutDumpingSecrets() {
        val raw = "ERROR [Instagram] rate-limit reached or login required. sessionid=must-not-be-shown"
        val message = DownloadMessages.error(raw, true, false)
        assertTrue(message.contains("Conectar Instagram"))
        assertFalse(message.contains("must-not-be-shown"))
        assertFalse(message.contains("yt-dlp"))
    }
    @Test fun importedSessionsCanStillBeRateLimited() {
        val message = DownloadMessages.error("HTTP 429 login required", true, true)
        assertTrue(message.contains("aguarde"))
        assertTrue(message.contains("Reconecte"))
    }
    @Test fun genericErrorsDoNotExposeRawDiagnostics() {
        val message = DownloadMessages.error("internal failure /private/token-file", false, false)
        assertFalse(message.contains("/private/"))
        assertTrue(message.contains("Atualize"))
    }
}
