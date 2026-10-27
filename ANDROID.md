# SnapLoad para Android

O aplicativo é nativo (Kotlin) e executa yt-dlp e FFmpeg no próprio aparelho. Não usa WebView nem depende da API hospedada no Render. Requer internet e Android 10 ou superior.

## Instalar

Baixe **SnapLoad-Android.apk** em https://github.com/shoowt/snapload/releases/latest e abra o arquivo. O Android pode solicitar permissão para instalar aplicativos pelo navegador ou gerenciador de arquivos. As próximas versões precisam ser assinadas com a mesma chave para permitir atualização.

Cole um link ou compartilhe um link de outro aplicativo com o SnapLoad. Selecione vídeo ou áudio MP3. O download continua com uma notificação e é salvo em **Downloads/SnapLoad**. O botão **Atualizar extrator** atualiza o yt-dlp diretamente da origem oficial.

Sites podem exigir autenticação ou bloquear downloads. O app não promete remover marcas d'água de qualquer vídeo. O limite por mídia é 1 GB e a operação pode ser interrompida pelo sistema, por falta de espaço ou de rede.

## Compilar

Use JDK 17, Android SDK 35 e Gradle 8.11.1. Na pasta `android`, execute `gradle :app:assembleDebug` para uma compilação local de desenvolvimento.

A workflow `.github/workflows/android.yml` compila a versão assinada e executa o lint. Tags `v*` publicam automaticamente o APK na página de Releases. A chave de assinatura fica nos Secrets do GitHub e em `signing/` local, ignorado pelo Git. Mantenha uma cópia de segurança privada dessa pasta.

Bibliotecas: https://github.com/yausername/youtubedl-android (wrapper Android), https://github.com/yt-dlp/yt-dlp e FFmpeg. Consulte as respectivas licenças ao redistribuir os componentes.
