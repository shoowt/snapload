package com.shoowt.snapload

import android.app.Activity
import android.os.Bundle
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.content.Intent
import android.content.ClipboardManager
import android.graphics.Color
import android.view.View
import android.widget.*

class MainActivity : Activity() {
    private lateinit var url: EditText
    private lateinit var status: TextView
    private lateinit var download: Button
    private val handler = Handler(Looper.getMainLooper())
    private val refresh = object : Runnable {
        override fun run() {
            val prefs = getSharedPreferences("download", MODE_PRIVATE)
            status.text = prefs.getString("status", "Cole um link público para começar.")
            download.isEnabled = !DownloadService.busy.get()
            handler.postDelayed(this, 700)
        }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 48, 24, 24)
            setBackgroundColor(Color.rgb(11, 15, 25))
        }
        val scroll = ScrollView(this).apply { addView(layout) }
        fun label(text: String, size: Float) = TextView(this).apply {
            this.text = text; textSize = size; setTextColor(Color.WHITE)
            setPadding(0, 14, 0, 14); layout.addView(this)
        }
        label("SnapLoad ↓", 32f)
        label("Baixe vídeos e áudio direto no celular", 18f)
        url = EditText(this).apply {
            hint = "Cole o link do vídeo"; setTextColor(Color.WHITE)
            setHintTextColor(Color.LTGRAY); inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_URI
            minHeight = 64; layout.addView(this)
        }
        Button(this).apply {
            text = "Colar link"; layout.addView(this)
            setOnClickListener {
                val clip = (getSystemService(CLIPBOARD_SERVICE) as ClipboardManager).primaryClip
                if (clip != null && clip.itemCount > 0) url.setText(clip.getItemAt(0).coerceToText(this@MainActivity))
            }
        }
        val audio = Switch(this).apply {
            text = "Somente áudio (MP3)"; setTextColor(Color.WHITE); minHeight = 64; layout.addView(this)
        }
        download = Button(this).apply {
            text = "Baixar"; layout.addView(this)
            setOnClickListener {
                val value = extractLink(url.text.toString())
                val uri = android.net.Uri.parse(value)
                if (uri.scheme !in listOf("http", "https") || uri.host.isNullOrBlank()) {
                    Toast.makeText(this@MainActivity, "Informe um link válido.", Toast.LENGTH_LONG).show()
                } else {
                    startForegroundService(Intent(this@MainActivity, DownloadService::class.java)
                        .putExtra("url", value).putExtra("audio", audio.isChecked))
                }
            }
        }
        status = label("", 16f)
        label("Arquivos salvos em Downloads/SnapLoad. A extração e conversão são feitas neste aparelho; não dependem do site.", 14f)
        Button(this).apply {
            text = "Atualizar extrator"; layout.addView(this)
            setOnClickListener { startForegroundService(Intent(this@MainActivity, DownloadService::class.java).putExtra("update", true)) }
        }
        label("Use conteúdo público que você tem autorização para baixar. Algumas plataformas podem exigir login ou bloquear o acesso.", 13f)
        setContentView(scroll)
        if (intent.action == Intent.ACTION_SEND) url.setText(extractLink(intent.getStringExtra(Intent.EXTRA_TEXT).orEmpty()))
        if (Build.VERSION.SDK_INT >= 33) requestPermissions(arrayOf("android.permission.POST_NOTIFICATIONS"), 10)
    }
    private fun extractLink(value: String) = Regex("https?://[^\\s]+").find(value)?.value ?: value.trim()
    override fun onResume() { super.onResume(); handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh); super.onPause() }
}
