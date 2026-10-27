package com.shoowt.snapload

/** Only Instagram cookies are retained, even when a browser exports other sites. */
object InstagramCookies {
    private fun allowedDomain(domain: String): Boolean {
        val host = domain.removePrefix(".").lowercase()
        return host == "instagram.com" || host.endsWith(".instagram.com")
    }
    fun fromHeader(header: String): String {
        val expiry = System.currentTimeMillis() / 1000 + 30 * 24 * 60 * 60
        val lines = header.split(';').mapNotNull { item ->
            val pair = item.trim().split('=', limit = 2)
            if (pair.size != 2 || pair[0].isBlank() || pair.any { it.contains('\n') || it.contains('\r') || it.contains('\t') }) null
            else ".instagram.com\tTRUE\t/\tTRUE\t$expiry\t${pair[0]}\t${pair[1]}"
        }
        return validate("# Netscape HTTP Cookie File\n" + lines.joinToString("\n"))
    }
    fun validate(contents: String): String {
        require(contents.length <= 1024 * 1024) { "Arquivo de sessão muito grande." }
        val rows = contents.lineSequence().map { it.trimEnd('\r') }.filter {
            it.isNotBlank() && (!it.startsWith('#') || it.startsWith("#HttpOnly_"))
        }.mapNotNull { line ->
            val fields = line.removePrefix("#HttpOnly_").split('\t')
            if (fields.size != 7 || !allowedDomain(fields[0])) null
            else {
                require(fields[1] in listOf("TRUE", "FALSE") && fields[3] in listOf("TRUE", "FALSE") && fields[4].toLongOrNull() != null) {
                    "Formato inválido. Importe cookies no formato Netscape (.txt)."
                }
                line
            }
        }.toList()
        require(rows.any {
            val parts = it.removePrefix("#HttpOnly_").split('\t')
            parts[5] == "sessionid" && parts[6].isNotBlank() && (parts[4] == "0" || parts[4].toLong() > System.currentTimeMillis() / 1000)
        }) { "Sessão do Instagram ausente ou vencida. Entre na sua conta e exporte os cookies novamente." }
        return "# Netscape HTTP Cookie File\n" + rows.joinToString("\n") + "\n"
    }
    fun isInstagram(link: String): Boolean = try {
        val host = java.net.URI(link).host?.lowercase().orEmpty()
        host == "instagram.com" || host.endsWith(".instagram.com")
    } catch (_: Exception) { false }
}
