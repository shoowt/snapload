# SnapLoad ⚡

> **Web App / PWA Mobile-First** para download de vídeos de redes sociais públicas (**TikTok, Instagram Reels, YouTube Shorts, X/Twitter e Facebook**) em alta qualidade e **sem marca d'água** direto na galeria do celular.

---

## 📱 Destaques de UI/UX & Mobile-First

- **Dark Mode Moderno:** Estética inspirada em OLED slate (`#070B14`) com efeito *Glassmorphism*, iluminação ambiente sutil e tipografia limpa (*Plus Jakarta Sans*).
- **Ergonomia para Uma Mão (Thumb-Zone):** Todos os controles essenciais (campo de input, botão de colar, ação principal e cards de download) estão centralizados e acessíveis pelo polegar, com áreas de toque ampliadas (>= 52px).
- **Botão "Colar" com 1 Toque:** Integração com a **Clipboard API** nativa (`navigator.clipboard.readText()`), permitindo colar e acionar a busca instantaneamente, com feedback háptico (`navigator.vibrate`) em dispositivos móveis compatíveis.
- **Detecção Automática de Plataforma:** Ao colar a URL, o app identifica visualmente a rede social correspondente e destaca o respectivo selo (TikTok, Instagram, YouTube, X, Facebook).
- **Skeleton Loader & Shimmer:** Feedback visual de carregamento animado simulando o card do vídeo antes da renderização final.
- **Card de Resultados Completo:**
  - Thumbnail em alta proporção com tempo de duração (`MM:SS`).
  - **Destaque Principal:** Botão em gradiente verde/ciano para download do **Vídeo Sem Marca d'Água (Original/HD)**.
  - **Seletor de Resolução:** Alternativas de qualidade (1080p, 720p, etc.).
  - **Download de Áudio:** Opção dedicada para extrair **Apenas Áudio (MP3)**.
- **Download Direto na Galeria/Arquivos:** A rota de download força o cabeçalho HTTP `Content-Disposition: attachment; filename="..."`, garantindo que o navegador móvel baixe o arquivo para a galeria ou pasta de downloads, em vez de abrir um player de vídeo em uma nova aba.
- **PWA (Progressive Web App):** Manifesto configurado (`manifest.json`) e Service Worker (`sw.js`) permitindo instalação na tela de início com comportamento nativo em Android (Chrome) e iOS (Safari).

---

## 🛠️ Arquitetura e Back-end

- **FastAPI (Python):** Roteamento assíncrono de alto desempenho, streaming direto de chunks HTTP (sem sobrecarregar memória RAM).
- **yt-dlp:** Configurado especificamente para priorizar streams limpos de CDNs sem marca d'água (ex: `download_addr` no TikTok, streams diretos de MP4 no Instagram Reels e Twitter).
- **Sanitização de URLs:** Remoção proativa de todos os parâmetros de rastreamento e telemetria (`?igsh=`, `?is_from_webapp=`, `?utm_source=`, `?si=`, etc.).
- **User-Agent & Headers:** Injeção de cabeçalhos de navegadores modernos para evitar detecção por bots e bloqueios por rate limit.
- **FFmpeg Ready:** Suporte para mesclagem de vídeo e áudio em altíssimas resoluções (1080p+, 4K) e conversão de áudio para MP3 via background task com auto-limpeza de arquivos temporários.

---

## 📂 Estrutura do Projeto

```text
download-mp4/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Aplicação FastAPI, rotas REST e montagem estática
│   │   ├── config.py            # User-agents, parâmetros de rede e plataformas
│   │   ├── sanitizers.py        # Limpeza de tracking de URL e detecção de plataforma
│   │   ├── extractor.py         # Extração via yt-dlp e priorização sem marca d'água
│   │   └── downloader.py        # Proxy de streaming e download direto attachment
│   ├── requirements.txt         # Dependências Python
│   └── tests/
│       └── test_sanitizer.py    # Testes unitários de sanitização de URLs
├── frontend/
│   ├── index.html               # Interface mobile-first dark mode
│   ├── manifest.json            # Configuração PWA
│   ├── sw.js                    # Service Worker para cache da aplicação
│   ├── css/
│   │   └── style.css            # Estilos customizados, glassmorphism e animações
│   ├── js/
│   │   ├── app.js               # Lógica de input, colar da clipboard e downloads
│   │   └── pwa.js               # Registro do Service Worker e prompt de instalação
│   └── icons/
│       ├── icon.svg             # Ícone principal em vetor
│       ├── icon-192.svg         # Ícone PWA 192px
│       ├── icon-512.svg         # Ícone PWA 512px
│       └── favicon.svg          # Favicon
├── Dockerfile                   # Build de produção com Python + FFmpeg
├── docker-compose.yml           # Orquestração do container
├── run.py                       # Script de inicialização rápida local
└── README.md                    # Documentação do projeto
```

---

## 🚀 Como Executar

### Opção 1: Via Docker (Recomendado)

O Docker já vem configurado com **Python**, **FFmpeg** e todas as dependências do sistema:

```bash
# Construir e iniciar a aplicação
docker compose up --build
```

Acesse em seu celular ou navegador:
👉 **`http://localhost:8000`**

---

### Opção 2: Execução Local com Python

1. **Instale as dependências:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Inicie a aplicação:**
   ```bash
   python run.py
   ```

3. **Acesse:**
   - Interface Web / Mobile PWA: **`http://localhost:8000`**
   - Documentação Interativa da API (Swagger): **`http://localhost:8000/docs`**

---

## 🧪 Executar Testes Unitários

Para validar os sanitizadores de URL e a remoção de tracking:

```bash
python -m backend.tests.test_sanitizer
```

---

## 📡 Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/health` | Status de saúde da aplicação e plataformas suportadas. |
| `POST` | `/api/info` | Recebe `{ "url": "..." }`, sanitiza e retorna metadados e streams limpos. |
| `GET` | `/api/download` | Realiza o stream proxy forçando o download direto (`attachment; filename=...`). |
| `GET` | `/manifest.json` | Manifesto do PWA. |
| `GET` | `/sw.js` | Service Worker do PWA. |
