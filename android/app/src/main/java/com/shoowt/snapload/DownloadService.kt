package com.shoowt.snapload

import android.app.*
import android.content.*
import android.os.*
import android.provider.MediaStore
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import com.yausername.ffmpeg.FFmpeg
import java.io.File
import java.util.concurrent.atomic.AtomicBoolean

class DownloadService : Service() {
    companion object { val busy = AtomicBoolean(false) }
    private fun notification(text: String): Notification = Notification.Builder(this, "downloads")
        .setSmallIcon(android.R.drawable.stat_sys_download)
        .setContentTitle("SnapLoad").setContentText(text)
        .setContentIntent(PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE))
        .setOngoing(true).build()
    private fun status(text: String) {
        getSharedPreferences("download", MODE_PRIVATE).edit().putString("status", text).apply()
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).notify(1, notification(text))
    }
    override fun onCreate() {
        super.onCreate()
        (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(
            NotificationChannel("downloads", "Downloads", NotificationManager.IMPORTANCE_LOW))
    }
    override fun onBind(intent: Intent?) = null
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(1, notification("Preparando…"))
        if (!busy.compareAndSet(false, true)) return START_NOT_STICKY
        Thread {
            val wake = (getSystemService(POWER_SERVICE) as PowerManager).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SnapLoad:download")
            val directory = File(cacheDir, "download-${System.currentTimeMillis()}")
            try {
                wake.acquire(60 * 60 * 1000L)
                status("Preparando o extrator no aparelho…")
                YoutubeDL.getInstance().init(this)
                FFmpeg.getInstance().init(this)
                if (intent?.getBooleanExtra("update", false) == true) {
                    status("Atualizando extrator…")
                    YoutubeDL.getInstance().updateYoutubeDL(this)
                    status("Extrator atualizado.")
                } else {
                    val link = intent?.getStringExtra("url") ?: error("Link ausente")
                    val audio = intent.getBooleanExtra("audio", false)
                    directory.mkdirs()
                    val request = YoutubeDLRequest(link)
                    request.addOption("--no-playlist")
                    request.addOption("--socket-timeout", "30")
                    request.addOption("--max-filesize", "1G")
                    request.addOption("--no-mtime")
                    request.addOption("-o", File(directory, "%(title).120B [%(id)s].%(ext)s").absolutePath)
                    if (audio) {
                        request.addOption("-x")
                        request.addOption("--audio-format", "mp3")
                    } else {
                        request.addOption("-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b")
                        request.addOption("--merge-output-format", "mp4")
                    }
                    status("Conectando à plataforma…")
                    var lastUpdate = 0L
                    YoutubeDL.getInstance().execute(request, "snapload", false) { progress, _, _ ->
                        val now = System.currentTimeMillis()
                        if (now - lastUpdate > 700) { status("Baixando: ${progress.toInt()}% — aguarde a conversão"); lastUpdate = now }
                    }
                    val files = directory.listFiles()?.filter { it.isFile && it.extension.lowercase() in listOf("mp4", "mp3", "m4a", "webm", "mkv", "ogg", "opus") }.orEmpty()
                    check(files.isNotEmpty()) { "O extrator não gerou um arquivo de mídia." }
                    status("Salvando em Downloads/SnapLoad…")
                    files.forEach { saveDownload(it) }
                    status("Concluído! ${files.size} arquivo(s) em Downloads/SnapLoad.")
                }
            } catch (e: Exception) {
                status("Falha: ${e.message?.takeLast(650) ?: "Não foi possível baixar. Tente atualizar o extrator."}")
            } finally {
                directory.deleteRecursively()
                if (wake.isHeld) wake.release()
                busy.set(false)
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }.start()
        return START_NOT_STICKY
    }
    override fun onTimeout(startId: Int, fgsType: Int) {
        Thread { YoutubeDL.getInstance().destroyProcessById("snapload") }.start()
        getSharedPreferences("download", MODE_PRIVATE).edit()
            .putString("status", "Download interrompido pelo limite de execução do Android. Tente novamente.").apply()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }
    private fun saveDownload(file: File) {
        val mime = when(file.extension.lowercase()) {
            "mp3" -> "audio/mpeg"; "m4a" -> "audio/mp4"; "webm" -> "video/webm"
            "mkv" -> "video/x-matroska"; "ogg" -> "audio/ogg"; "opus" -> "audio/opus"; else -> "video/mp4"
        }
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, file.name)
            put(MediaStore.Downloads.MIME_TYPE, mime)
            put(MediaStore.Downloads.RELATIVE_PATH, "Download/SnapLoad")
            put(MediaStore.Downloads.IS_PENDING, 1)
        }
        val uri = contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values) ?: error("Não foi possível criar o arquivo.")
        try {
            val output = contentResolver.openOutputStream(uri) ?: error("Não foi possível abrir o arquivo.")
            output.use { dest -> file.inputStream().use { it.copyTo(dest) } }
            values.clear(); values.put(MediaStore.Downloads.IS_PENDING, 0)
            contentResolver.update(uri, values, null, null)
        } catch (e: Exception) { contentResolver.delete(uri, null, null); throw e }
    }
}
