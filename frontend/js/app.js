// SnapLoad Mobile-First Application Logic

// Platform visual metadata
const PLATFORMS = {
  tiktok: { name: "TikTok", color: "#FE2C55", icon: "tiktok" },
  instagram: { name: "Instagram", color: "#E1306C", icon: "instagram" },
  youtube: { name: "YouTube", color: "#FF0000", icon: "youtube" },
  twitter: { name: "X / Twitter", color: "#1DA1F2", icon: "twitter" },
  facebook: { name: "Facebook", color: "#1877F2", icon: "facebook" },
  threads: { name: "Threads", color: "#FFFFFF", icon: "threads" },
  other: { name: "Vídeo", color: "#6366F1", icon: "video" }
};

// Global application state
const state = {
  currentUrl: "",
  isLoading: false,
  videoData: null,
  selectedFormatId: "best"
};

// DOM Elements
const urlInput = document.getElementById("url-input");
const pasteBtn = document.getElementById("paste-btn");
const clearBtn = document.getElementById("clear-btn");
const submitBtn = document.getElementById("submit-btn");
const submitText = document.getElementById("submit-text");
const submitSpinner = document.getElementById("submit-spinner");
const searchIcon = document.getElementById("search-icon");
const skeletonCard = document.getElementById("skeleton-card");
const resultCard = document.getElementById("result-card");
const errorBanner = document.getElementById("error-banner");
const errorText = document.getElementById("error-text");
const toastContainer = document.getElementById("toast-container");
const platformPills = document.querySelectorAll(".platform-pill");

// Utility: Trigger Device Haptic Feedback
function triggerHaptic() {
  if (navigator.vibrate) {
    try {
      navigator.vibrate(20);
    } catch (_) {}
  }
}

// Utility: Show Floating Toast Notification
function showToast(message, type = "info") {
  if (!toastContainer) return;

  const toast = document.createElement("div");
  const bgColors = {
    info: "bg-slate-800 text-cyan-400 border-cyan-500/30",
    success: "bg-slate-800 text-emerald-400 border-emerald-500/30",
    error: "bg-slate-800 text-rose-400 border-rose-500/30",
    warning: "bg-slate-800 text-amber-400 border-amber-500/30"
  };

  toast.className = `flex items-center gap-3 px-4 py-3 rounded-2xl border shadow-xl text-sm font-medium transform transition-all duration-300 translate-y-3 opacity-0 backdrop-blur-md ${bgColors[type] || bgColors.info}`;
  
  const icon = type === "success" 
    ? `<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`
    : type === "error"
    ? `<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`
    : `<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;

  toast.innerHTML = `${icon}<span>${message}</span>`;
  toastContainer.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.remove("translate-y-3", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");
  });

  // Auto remove
  setTimeout(() => {
    toast.classList.remove("translate-y-0", "opacity-100");
    toast.classList.add("-translate-y-3", "opacity-0");
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// URL Platform Detector for UI highlighting
function detectPlatformFromUrl(url) {
  if (!url) return null;
  const lower = url.toLowerCase();
  if (lower.includes("tiktok.com")) return "tiktok";
  if (lower.includes("instagram.com")) return "instagram";
  if (lower.includes("youtube.com") || lower.includes("youtu.be")) return "youtube";
  if (lower.includes("twitter.com") || lower.includes("x.com")) return "twitter";
  if (lower.includes("facebook.com") || lower.includes("fb.watch")) return "facebook";
  if (lower.includes("threads.net")) return "threads";
  return null;
}

// Highlight the matching platform icon above input
function updatePlatformHighlight(platformKey) {
  platformPills.forEach((pill) => {
    const pillPlatform = pill.getAttribute("data-platform");
    if (platformKey && pillPlatform === platformKey) {
      pill.classList.add("ring-2", "ring-cyan-400", "scale-105", "opacity-100");
      pill.classList.remove("opacity-60");
    } else {
      pill.classList.remove("ring-2", "ring-cyan-400", "scale-105");
      pill.classList.add("opacity-60");
    }
  });
}

// Input change handler
urlInput.addEventListener("input", (e) => {
  const val = e.target.value.trim();
  if (val.length > 0) {
    clearBtn.classList.remove("hidden");
    const detected = detectPlatformFromUrl(val);
    updatePlatformHighlight(detected);
  } else {
    clearBtn.classList.add("hidden");
    updatePlatformHighlight(null);
  }
});

// Clear input button
clearBtn.addEventListener("click", () => {
  triggerHaptic();
  urlInput.value = "";
  clearBtn.classList.add("hidden");
  updatePlatformHighlight(null);
  urlInput.focus();
});

// Clipboard API: Paste button
pasteBtn.addEventListener("click", async () => {
  triggerHaptic();
  try {
    if (!navigator.clipboard || !navigator.clipboard.readText) {
      showToast("Área de transferência indisponível no navegador.", "warning");
      return;
    }

    const text = await navigator.clipboard.readText();
    if (!text || !text.trim()) {
      showToast("Área de transferência vazia.", "warning");
      return;
    }

    urlInput.value = text.trim();
    clearBtn.classList.remove("hidden");
    const detected = detectPlatformFromUrl(text.trim());
    updatePlatformHighlight(detected);

    showToast("Link colado da área de transferência!", "success");

    // Auto submit if it's a recognized video link
    if (detected) {
      handleSearch();
    }
  } catch (err) {
    console.warn("Clipboard access denied or error:", err);
    showToast("Permissão para colar negada. Cole manualmente no campo.", "warning");
    urlInput.focus();
  }
});

// Enter key in input triggers search
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleSearch();
  }
});

submitBtn.addEventListener("click", () => {
  handleSearch();
});

// Main Search & Extract Handler
async function handleSearch() {
  if (state.isLoading) return;

  const url = urlInput.value.trim();
  if (!url) {
    showToast("Por favor, cole um link de vídeo primeiro.", "warning");
    urlInput.focus();
    return;
  }

  triggerHaptic();
  setLoadingState(true);
  hideError();
  hideResultCard();
  showSkeleton();

  try {
    const response = await fetch("/api/info", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url: url })
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      const errMsg = data.detail || data.error || "Não foi possível carregar as informações do vídeo.";
      throw new Error(errMsg);
    }

    state.videoData = data;
    renderResultCard(data);
    showToast("Vídeo localizado! Pronto para download.", "success");
  } catch (err) {
    console.error("Erro na busca:", err);
    showError(err.message || "Erro de conexão ao buscar vídeo. Tente novamente.");
  } finally {
    setLoadingState(false);
    hideSkeleton();
  }
}

// UI State Toggles
function setLoadingState(loading) {
  state.isLoading = loading;
  if (loading) {
    submitBtn.disabled = true;
    submitBtn.classList.add("opacity-80", "cursor-not-allowed");
    submitSpinner.classList.remove("hidden");
    searchIcon.classList.add("hidden");
    submitText.innerText = "Buscando Stream...";
  } else {
    submitBtn.disabled = false;
    submitBtn.classList.remove("opacity-80", "cursor-not-allowed");
    submitSpinner.classList.add("hidden");
    searchIcon.classList.remove("hidden");
    submitText.innerText = "Buscar Vídeo";
  }
}

function showSkeleton() {
  skeletonCard.classList.remove("hidden");
  skeletonCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideSkeleton() {
  skeletonCard.classList.add("hidden");
}

function showError(message) {
  errorText.innerText = message;
  errorBanner.classList.remove("hidden");
  errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  showToast(message, "error");
}

function hideError() {
  errorBanner.classList.add("hidden");
}

function hideResultCard() {
  resultCard.classList.add("hidden");
}

// Render Result Card with clean stream options
function renderResultCard(data) {
  const thumbElem = document.getElementById("video-thumbnail");
  const titleElem = document.getElementById("video-title");
  const authorElem = document.getElementById("video-author");
  const durationElem = document.getElementById("video-duration");
  const platformBadge = document.getElementById("video-platform-badge");
  const platformIconElem = document.getElementById("video-platform-icon");
  const primaryDownloadBtn = document.getElementById("primary-download-btn");
  const primaryQualityText = document.getElementById("primary-quality-text");
  const audioDownloadBtn = document.getElementById("audio-download-btn");
  const formatSelect = document.getElementById("format-select");
  const secondaryDownloadBtn = document.getElementById("secondary-download-btn");
  const formatSelectContainer = document.getElementById("format-select-container");

  // Populate metadata
  thumbElem.src = data.thumbnail || "/static/icons/icon.svg";
  titleElem.innerText = data.title || "Vídeo sem título";
  authorElem.innerText = `@${data.author || data.platform_name}`;
  durationElem.innerText = data.duration || "";

  // Platform Badge
  platformBadge.innerText = `${data.platform_name} • Sem Marca d'Água`;
  platformBadge.style.borderColor = data.platform_color ? `${data.platform_color}66` : "rgba(6, 182, 212, 0.4)";

  // Filter video & audio formats
  const formats = data.formats || [];
  const videoFormats = formats.filter((f) => f.type === "video");
  const audioFormats = formats.filter((f) => f.type === "audio");

  // Identify Best Clean Format
  const primaryFormat = videoFormats.find((f) => f.is_primary) || videoFormats[0] || null;

  if (primaryFormat) {
    primaryQualityText.innerText = `${primaryFormat.label} ${primaryFormat.filesize_readable ? `(${primaryFormat.filesize_readable})` : ""}`;
    primaryDownloadBtn.onclick = () => {
      triggerDownload({
        url: data.original_url,
        directUrl: primaryFormat.url,
        formatId: primaryFormat.format_id,
        title: data.title,
        isAudio: false
      });
    };
  } else {
    primaryDownloadBtn.onclick = () => {
      triggerDownload({
        url: data.original_url,
        formatId: "best",
        title: data.title,
        isAudio: false
      });
    };
  }

  // Populate Format Dropdown for alternative resolutions (720p, 480p, etc.)
  formatSelect.innerHTML = "";
  if (videoFormats.length > 1) {
    videoFormats.forEach((fmt) => {
      const opt = document.createElement("option");
      opt.value = fmt.format_id;
      opt.dataset.directUrl = fmt.url || "";
      opt.innerText = `${fmt.label} ${fmt.filesize_readable ? `— ${fmt.filesize_readable}` : ""}`;
      formatSelect.appendChild(opt);
    });
    formatSelectContainer.classList.remove("hidden");

    secondaryDownloadBtn.onclick = () => {
      const selectedOption = formatSelect.options[formatSelect.selectedIndex];
      const selectedDirectUrl = selectedOption ? selectedOption.dataset.directUrl : null;
      triggerDownload({
        url: data.original_url,
        directUrl: selectedDirectUrl,
        formatId: formatSelect.value,
        title: data.title,
        isAudio: false
      });
    };
  } else {
    formatSelectContainer.classList.add("hidden");
  }

  // Audio Download Option
  const bestAudio = audioFormats[0];
  audioDownloadBtn.onclick = () => {
    triggerDownload({
      url: data.original_url,
      directUrl: bestAudio ? bestAudio.url : null,
      formatId: bestAudio ? bestAudio.format_id : "bestaudio",
      title: `${data.title} [Audio]`,
      isAudio: true
    });
  };

  // Reveal card with animation
  resultCard.classList.remove("hidden");
  resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Trigger streaming direct download to gallery
function triggerDownload({ url, directUrl, formatId, title, isAudio }) {
  triggerHaptic();

  showToast("Iniciando download direto para a sua galeria...", "info");

  // Build the streaming proxy URL
  const params = new URLSearchParams();
  params.set("url", url);
  if (directUrl && !isAudio) {
    params.set("direct_url", directUrl);
  }
  if (formatId) {
    params.set("format_id", formatId);
  }
  if (title) {
    params.set("title", title);
  }
  if (isAudio) {
    params.set("is_audio", "true");
  }

  const downloadUrl = `/api/download?${params.toString()}`;

  // Create an invisible anchor tag to trigger native download without navigating away
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.setAttribute("download", "");
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Secondary confirmation toast
  setTimeout(() => {
    showToast("Download em andamento! Verifique sua pasta de Downloads.", "success");
  }, 2000);
}
