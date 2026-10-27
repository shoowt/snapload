// PWA Service Worker & Install Prompt Logic
let deferredInstallPrompt = null;

window.addEventListener("load", () => {
  // Register Service Worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        console.log("SnapLoad ServiceWorker registrado com sucesso:", registration.scope);
      })
      .catch((err) => {
        console.warn("Falha ao registrar ServiceWorker:", err);
      });
  }

  // Check if running in Standalone (already installed as PWA)
  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  if (isStandalone) {
    const installBtn = document.getElementById("install-btn");
    if (installBtn) installBtn.style.display = "none";
  }
});

// Capture native install prompt
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;

  // Show Install Button in Header & floating pill
  const installBtn = document.getElementById("install-btn");
  if (installBtn) {
    installBtn.classList.remove("hidden");
    installBtn.classList.add("flex");
  }
});

// User clicked Install App button
window.triggerPWAInstall = async function () {
  if (!deferredInstallPrompt) {
    // Show instruction toast for iOS Safari if installation is manual
    showToast("No iPhone/iPad: Toque no botão Compartilhar e selecione 'Adicionar à Tela de Início'", "info");
    return;
  }

  deferredInstallPrompt.prompt();
  const { outcome } = await deferredInstallPrompt.userChoice;
  console.log(`Instalação do PWA: ${outcome}`);

  if (outcome === "accepted") {
    const installBtn = document.getElementById("install-btn");
    if (installBtn) installBtn.style.display = "none";
  }

  deferredInstallPrompt = null;
};

window.addEventListener("appinstalled", () => {
  console.log("SnapLoad instalado na tela inicial!");
  showToast("Aplicativo instalado com sucesso na sua tela inicial!", "success");
  const installBtn = document.getElementById("install-btn");
  if (installBtn) installBtn.style.display = "none";
});
