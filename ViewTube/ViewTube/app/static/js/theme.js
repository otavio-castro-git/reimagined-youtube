/* ═══════════════════════════════════════════════════════════
   ViewTube — theme.js
   Alterna entre modo escuro (padrão) e modo claro, salvando a
   preferência em localStorage.
   ═══════════════════════════════════════════════════════════ */

(function () {
  const STORAGE_KEY = "vt_tema";

  const btn      = document.getElementById("btnToggleTheme");
  const iconSun   = document.getElementById("themeIconSun");
  const iconMoon  = document.getElementById("themeIconMoon");

  function aplicarTema(modo) {
    if (modo === "claro") {
      document.documentElement.setAttribute("data-tema", "claro");
      if (iconSun)  iconSun.style.display  = "block";
      if (iconMoon) iconMoon.style.display = "none";
    } else {
      document.documentElement.removeAttribute("data-tema");
      if (iconSun)  iconSun.style.display  = "none";
      if (iconMoon) iconMoon.style.display = "block";
    }
    localStorage.setItem(STORAGE_KEY, modo);
  }

  // Aplica o tema salvo assim que o script carrega (antes do toggle)
  const salvo = localStorage.getItem(STORAGE_KEY) || "escuro";
  aplicarTema(salvo);

  btn?.addEventListener("click", () => {
    const atual = localStorage.getItem(STORAGE_KEY) || "escuro";
    aplicarTema(atual === "claro" ? "escuro" : "claro");
  });
})();
