package com.shoowt.snapload

import android.annotation.SuppressLint
import android.app.Activity
import android.os.Bundle
import android.graphics.Color
import android.net.Uri
import android.view.WindowManager
import android.webkit.*
import android.widget.*

/** WebView is used only for the user's official Instagram login, never for downloads. */
class InstagramLoginActivity : Activity() {
    private lateinit var web: WebView
    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(TextView(this).apply {
            text = "Conectar Instagram — https://www.instagram.com\nEntre na página oficial e depois toque em Concluir conexão. A sessão fica neste aparelho."
            setPadding(20, 16, 20, 8); setTextColor(Color.WHITE); setBackgroundColor(Color.rgb(11,15,25))
        })
        val done = Button(this).apply { text = "Concluir conexão" }
        root.addView(done)
        web = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            settings.userAgentString = settings.userAgentString.replace("; wv", "").replace("Version/4.0 ", "")
            CookieManager.getInstance().setAcceptThirdPartyCookies(this, false)
            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                    val uri = request.url
                    val allowed = uri.scheme == "https" && InstagramCookies.isInstagram(uri.toString())
                    if (!allowed) Toast.makeText(this@InstagramLoginActivity, "Use o login do Instagram nesta tela. Para outra forma de acesso, importe os cookies.", Toast.LENGTH_LONG).show()
                    return !allowed
                }
            }
        }
        root.addView(web, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(root)
        CookieManager.getInstance().setAcceptCookie(true)
        web.loadUrl("https://www.instagram.com/accounts/login/")
        done.setOnClickListener {
            try {
                val header = CookieManager.getInstance().getCookie("https://www.instagram.com/").orEmpty()
                InstagramSession.save(this, InstagramCookies.fromHeader(header), web.settings.userAgentString)
                getSharedPreferences("download", MODE_PRIVATE).edit().putString("status", "Instagram conectado. Volte ao link e toque em Baixar.").apply()
                Toast.makeText(this, "Sessão salva neste aparelho.", Toast.LENGTH_LONG).show()
                finish()
            } catch (_: Exception) {
                Toast.makeText(this, "Login ainda não concluído. Entre na sua conta e tente novamente. Se o Instagram recusar, use Importar sessão.", Toast.LENGTH_LONG).show()
            }
        }
    }
    override fun onDestroy() {
        if (::web.isInitialized) {
            web.stopLoading(); web.clearCache(true); web.clearHistory(); web.destroy()
            CookieManager.getInstance().removeAllCookies(null)
            CookieManager.getInstance().flush()
            WebStorage.getInstance().deleteAllData()
        }
        super.onDestroy()
    }
}
