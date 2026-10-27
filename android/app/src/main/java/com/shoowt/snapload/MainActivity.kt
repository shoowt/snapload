package com.shoowt.snapload

import android.app.Activity
import android.app.AlertDialog
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
    private lateinit var sessionStatus: TextView
    private val sessionButtons = mutableListOf<Button>()
    private var importing = false
    private val handler = Handler(Looper.getMainLooper())
    private val refresh = object : Runnable {
        override fun run() {
            val prefs = getSharedPreferences("download", MODE_PRIVATE)
            status.text = prefs.getString("status", "Cole um link público para começar.")
            val idle = !DownloadService.busy.get() && !importing
            download.isEnabled = idle
            sessionButtons.forEach { it.isEnabled = idle }
            sessionStatus.text = if (InstagramSession.exists(this@MainActivity)) "Instagram: sessão salva no aparelho" else "Instagram: sem sessão (acesso anônimo)"
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
        sessionStatus = label("", 14f)
        Button(this).apply {
            text = "Conectar Instagram"; layout.addView(this); sessionButtons.add(this)
            setOnClickListener { startActivity(Intent(this@MainActivity, InstagramLoginActivity::class.java)) }
        }
        Button(this).apply {
            text = "Importar sessão do Instagram"; layout.addView(this); sessionButtons.add(this)
            setOnClickListener {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("Importar cookies do Instagram")
                    .setMessage("Selecione um arquivo cookies.txt no formato Netscape, exportado de um navegador em que você entrou no Instagram. O app guarda apenas os cookies do Instagram, criptografados neste aparelho. Não compartilhe esse arquivo: ele permite acesso à sua conta. Remova a cópia exportada depois de importar.")
                    .setNegativeButton("Cancelar", null)
                    .setPositiveButton("Selecionar arquivo") { _, _ ->
                        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                            addCategory(Intent.CATEGORY_OPENABLE); type = "*/*"
                        }, 20)
                    }.show()
            }
        }
        Button(this).apply {
            text = "Remover sessão do Instagram"; layout.addView(this); sessionButtons.add(this)
            setOnClickListener {
                InstagramSession.clear(this@MainActivity)
                getSharedPreferences("download", MODE_PRIVATE).edit().putString("status", "Sessão removida deste aparelho.").apply()
            }
        }
        label("Arquivos salvos em Downloads/SnapLoad. A extração e conversão são feitas neste aparelho; não dependem do site.", 14f)
        Button(this).apply {
            text = "Atualizar extrator"; layout.addView(this); sessionButtons.add(this)
            setOnClickListener { startForegroundService(Intent(this@MainActivity, DownloadService::class.java).putExtra("update", true)) }
        }
        label("Use conteúdo público que você tem autorização para baixar. Algumas plataformas podem exigir login ou bloquear o acesso.", 13f)
        setContentView(scroll)
        if (intent.action == Intent.ACTION_SEND) url.setText(extractLink(intent.getStringExtra(Intent.EXTRA_TEXT).orEmpty()))
        if (Build.VERSION.SDK_INT >= 33) requestPermissions(arrayOf("android.permission.POST_NOTIFICATIONS"), 10)
    }
    @Deprecated("Uses the platform document picker without an extra UI framework")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != 20 || resultCode != RESULT_OK || DownloadService.busy.get()) return
        val uri = data?.data ?: return
        importing = true
        Thread {
            val message = try {
                val bytes = contentResolver.openInputStream(uri)?.use { stream ->
                    val buffer = ByteArray(1024 * 1024 + 1)
                    var count = 0
                    while (count < buffer.size) {
                        val read = stream.read(buffer, count, buffer.size - count)
                        if (read < 0) break
                        count += read
                    }
                    buffer.copyOf(count)
                }
                    ?: error("Não foi possível abrir o arquivo.")
                require(bytes.size <= 1024 * 1024) { "Arquivo de sessão muito grande." }
                InstagramSession.save(this, String(bytes, Charsets.UTF_8))
                "Sessão do Instagram importada neste aparelho. Toque em Baixar para tentar novamente."
            } catch (e: IllegalArgumentException) { e.message ?: "Arquivo de sessão inválido." }
            catch (_: Exception) { "Não foi possível importar a sessão. Selecione cookies.txt no formato Netscape." }
            getSharedPreferences("download", MODE_PRIVATE).edit().putString("status", message).apply()
            runOnUiThread { importing = false; Toast.makeText(this, message, Toast.LENGTH_LONG).show() }
        }.start()
    }
    private fun extractLink(value: String) = Regex("https?://[^\\s]+").find(value)?.value ?: value.trim()
    override fun onResume() { super.onResume(); handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh); super.onPause() }
}
