package com.shoowt.snapload

object DownloadMessages {
    fun error(raw: String, instagram: Boolean, authenticated: Boolean): String {
        val message = raw.lowercase()
        if (instagram && listOf("login", "rate-limit", "rate limit", "429", "cookies", "checkpoint", "challenge", "session", "sessão").any { it in message }) {
            return if (authenticated) "O Instagram recusou a sessão ou limitou o acesso. Reconecte em Conectar Instagram. Se continuar, aguarde antes de tentar novamente e confira se o vídeo abre na sua conta."
            else "O Instagram pediu login ou limitou o acesso anônimo. Toque em Conectar Instagram, entre na sua conta e tente novamente. Você também pode usar Importar sessão."
        }
        return when {
            listOf("private", "unavailable", "not available", "not found", "removed", "deleted").any { it in message } -> "Vídeo indisponível ou sem acesso. Confira se o link abre na sua conta e se você tem autorização para baixar."
            listOf("unsupported url", "invalid url").any { it in message } -> "Link não suportado. Compartilhe ou cole o endereço completo do vídeo."
            listOf("timed out", "network", "resolve", "connection", "unable to download").any { it in message } -> "Falha de conexão com a plataforma. Verifique a internet e tente novamente mais tarde."
            listOf("space", "enospc").any { it in message } -> "Falta espaço no aparelho. Libere armazenamento e tente novamente."
            else -> "Não foi possível concluir o download. Atualize o extrator e confira o link. A plataforma pode estar bloqueando o acesso."
        }
    }
}
