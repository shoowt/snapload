# SnapLoad para Android

O aplicativo é nativo (Kotlin) e executa yt-dlp e FFmpeg no próprio aparelho, sem depender da API hospedada no Render. A tela oficial de login do Instagram é a única tela que usa WebView. Requer internet e Android 10 ou superior.

## Instalar

Baixe **SnapLoad-Android.apk** em https://github.com/shoowt/snapload/releases/latest e abra o arquivo. O Android pode solicitar permissão para instalar aplicativos pelo navegador ou gerenciador de arquivos. As próximas versões precisam ser assinadas com a mesma chave para permitir atualização.

Cole um link ou compartilhe um link de outro aplicativo com o SnapLoad. Selecione vídeo ou áudio MP3. O download continua com uma notificação e é salvo em **Downloads/SnapLoad**. O botão **Atualizar extrator** atualiza o yt-dlp diretamente da origem oficial.

Sites podem exigir autenticação ou bloquear downloads. O app não promete remover marcas d'água de qualquer vídeo. O limite por mídia é 1 GB e a operação pode ser interrompida pelo sistema, por falta de espaço ou de rede.

## Instagram pede login ou limita o acesso

Na versão 1.0.3, toque em **Conectar Instagram**, entre na página oficial `https://www.instagram.com` e toque em **Concluir conexão**. Depois volte ao link e toque em **Baixar**. Isso não exige compartilhar sua senha com o desenvolvedor nem com o Render: o login é enviado diretamente ao Instagram.

Se o Instagram recusar o navegador de login, use **Importar sessão do Instagram** e selecione um arquivo `cookies.txt` no formato Netscape exportado de um navegador em que você já entrou na conta. Somente cookies do domínio Instagram são guardados. Não compartilhe esse arquivo e remova a cópia exportada depois da importação. Veja o [formato aceito pelo yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp).

A sessão importada/conectada fica criptografada com Android Keystore no armazenamento privado do aparelho, fora dos backups. Ela é usada apenas em links do Instagram; a cópia temporária necessária ao yt-dlp é apagada ao terminar a operação. A WebView limpa cookies e cache ao fechar. **Remover sessão do Instagram** apaga a sessão local. Para revogar uma sessão remotamente, use os controles do próprio Instagram.

O extrator verifica atualizações uma vez por dia antes de baixar. **Atualizar extrator** continua disponível manualmente. Login não garante acesso: vídeos removidos, privados sem permissão e limites da plataforma podem continuar impedindo o download. O app não repete automaticamente requisições recusadas pelo Instagram.

## Compilar

Use JDK 17, Android SDK 35 e Gradle 8.11.1. Na pasta `android`, execute `gradle :app:assembleDebug` para uma compilação local de desenvolvimento.

A workflow `.github/workflows/android.yml` compila a versão assinada e executa o lint. Tags `v*` publicam automaticamente o APK na página de Releases. A chave de assinatura fica nos Secrets do GitHub e em `signing/` local, ignorado pelo Git. Mantenha uma cópia de segurança privada dessa pasta.

Bibliotecas: https://github.com/yausername/youtubedl-android (wrapper Android), https://github.com/yt-dlp/yt-dlp e FFmpeg. Consulte as respectivas licenças ao redistribuir os componentes.
