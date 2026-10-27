package com.shoowt.snapload

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import org.json.JSONObject
import java.io.File
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Persistent session is encrypted with a non-exportable Android Keystore key. */
object InstagramSession {
    private const val ALIAS = "snapload_instagram_session"
    private fun file(context: Context) = File(context.noBackupFilesDir, "instagram-session.enc")
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(ALIAS, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    fun exists(context: Context) = file(context).isFile
    @Synchronized fun save(context: Context, cookies: String, userAgent: String = "") {
        val valid = InstagramCookies.validate(cookies)
        val data = JSONObject().put("cookies", valid).put("userAgent", userAgent).toString().toByteArray(Charsets.UTF_8)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        val encrypted = cipher.doFinal(data)
        val destination = file(context)
        val temporary = File(context.noBackupFilesDir, "instagram-session.new")
        try {
            temporary.writeBytes(cipher.iv + encrypted)
            check(temporary.renameTo(destination)) { "Não foi possível salvar a sessão." }
        } finally { temporary.delete() }
    }
    @Synchronized fun materialize(context: Context, directory: File): Pair<File, String>? {
        if (!exists(context)) return null
        val bytes = file(context).readBytes()
        require(bytes.size >= 29) { "Sessão inválida. Conecte o Instagram novamente." }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, bytes.copyOfRange(0, 12)))
        }
        val json = JSONObject(String(cipher.doFinal(bytes.copyOfRange(12, bytes.size)), Charsets.UTF_8))
        val cookies = InstagramCookies.validate(json.getString("cookies"))
        val output = File(directory, "instagram-cookies.txt")
        output.writeText(cookies)
        return output to json.optString("userAgent")
    }
    @Synchronized fun clear(context: Context) { file(context).delete() }
}
