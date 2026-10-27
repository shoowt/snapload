package com.shoowt.snapload

import android.content.Intent
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import com.yausername.ffmpeg.FFmpeg
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class SessionDeviceTest {
    @Test fun encryptedSessionRoundTripAndErase() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val directory = File(context.cacheDir, "session-device-test").apply { mkdirs() }
        try {
            val cookies = InstagramCookies.fromHeader("sessionid=synthetic-test-only; csrftoken=synthetic-csrf")
            InstagramSession.save(context, cookies, "SnapLoad-device-test")
            assertTrue(InstagramSession.exists(context))
            val encrypted = File(context.noBackupFilesDir, "instagram-session.enc").readBytes()
            assertFalse(String(encrypted, Charsets.ISO_8859_1).contains("synthetic-test-only"))
            val (file, agent) = InstagramSession.materialize(context, directory)!!
            assertEquals(cookies, file.readText())
            assertEquals("SnapLoad-device-test", agent)
            // Replacing a connected session must also work.
            InstagramSession.save(context, cookies, "replacement")
            assertEquals("replacement", InstagramSession.materialize(context, directory)!!.second)
            InstagramSession.clear(context)
            assertFalse(InstagramSession.exists(context))
            assertNull(InstagramSession.materialize(context, directory))
        } finally { InstagramSession.clear(context); directory.deleteRecursively() }
    }
    @Test fun bundledNativeExtractorRunsWithoutNetwork() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        YoutubeDL.getInstance().init(context)
        FFmpeg.getInstance().init(context)
        val request = YoutubeDLRequest("https://example.com/")
        request.addOption("--version")
        val response = YoutubeDL.getInstance().execute(request, "device-test", false, null)
        assertTrue(response.out.trim().isNotEmpty())
    }
    @Test fun loginActivityOpensAndCloses() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val activity = instrumentation.startActivitySync(Intent(instrumentation.targetContext, InstagramLoginActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        assertTrue(activity is InstagramLoginActivity)
        instrumentation.runOnMainSync { activity.finish() }
        instrumentation.waitForIdleSync()
    }
}
