/* ═══════════════════════════════════════════════════════════
   ViewTube — main.js
   Sidebar toggle, modals, login/register forms
   ═══════════════════════════════════════════════════════════ */

// ─── SIDEBAR ────────────────────────────────────────────────
const sidebar        = document.getElementById('sidebar');
const sidebarToggle  = document.getElementById('sidebarToggle');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const mainContent    = document.getElementById('mainContent');

let sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';

function applySidebar() {
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    sidebar.classList.remove('collapsed');
    mainContent.classList.remove('expanded');
    if (sidebarCollapsed) {
      sidebar.classList.remove('mobile-open');
      sidebarOverlay.classList.remove('visible');
    }
    return;
  }
  if (sidebarCollapsed) {
    sidebar.classList.add('collapsed');
    mainContent.classList.add('expanded');
  } else {
    sidebar.classList.remove('collapsed');
    mainContent.classList.remove('expanded');
  }
}

sidebarToggle?.addEventListener('click', () => {
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    const open = sidebar.classList.toggle('mobile-open');
    sidebarOverlay.classList.toggle('visible', open);
  } else {
    sidebarCollapsed = !sidebarCollapsed;
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed);
    applySidebar();
  }
});

sidebarOverlay?.addEventListener('click', () => {
  sidebar.classList.remove('mobile-open');
  sidebarOverlay.classList.remove('visible');
});

window.addEventListener('resize', applySidebar);
applySidebar();

// ─── USER DROPDOWN ──────────────────────────────────────────
const avatarBtn     = document.getElementById('avatarBtn');
const userDropdown  = document.getElementById('userDropdown');

avatarBtn?.addEventListener('click', (e) => {
  e.stopPropagation();
  userDropdown.classList.toggle('open');
});

document.addEventListener('click', () => {
  userDropdown?.classList.remove('open');
});

// ─── MODALS ──────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
  document.body.style.overflow = '';
}

// Open triggers
document.getElementById('openLogin')?.addEventListener('click', () => openModal('modalLogin'));
document.getElementById('openRegister')?.addEventListener('click', () => openModal('modalRegister'));

// Close buttons
document.querySelectorAll('[data-close]').forEach(btn => {
  btn.addEventListener('click', () => closeModal(btn.dataset.close));
});

// Switch links
document.querySelectorAll('[data-open]').forEach(btn => {
  btn.addEventListener('click', () => {
    const closeId = btn.dataset.closeCurrent;
    if (closeId) closeModal(closeId);
    openModal(btn.dataset.open);
  });
});

// Links de Termos de Uso / Política de Privacidade (abrem por cima do cadastro,
// sem fechar/perder o que já foi digitado no formulário)
document.getElementById('openTermsOfUse')?.addEventListener('click', (e) => {
  e.preventDefault();
  openModal('modalTermsOfUse');
});
document.getElementById('openPrivacyPolicy')?.addEventListener('click', (e) => {
  e.preventDefault();
  openModal('modalPrivacyPolicy');
});

// Click outside modal
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
});

// ESC key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});

// ─── CAPTCHA (Google reCAPTCHA v3) ────────────────────────────
async function getCaptchaToken(acao) {
  if (!window.RECAPTCHA_SITE_KEY || !window.grecaptcha) {
    // Captcha não configurado no .env — segue sem token (o back-end
    // também libera nesse caso, mas avisa no log do servidor).
    return "";
  }
  return new Promise((resolve) => {
    grecaptcha.ready(() => {
      grecaptcha.execute(window.RECAPTCHA_SITE_KEY, { action: acao })
        .then(resolve)
        .catch(() => resolve(""));
    });
  });
}

// ─── LOGIN FORM ──────────────────────────────────────────────
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const err = document.getElementById('loginError');
  err.textContent = '';
  const data = Object.fromEntries(new FormData(e.target));
  data.captcha_token = await getCaptchaToken('login');
  try {
    const res  = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.ok) {
      window.location.href = json.redirect || '/';
    } else {
      err.textContent = json.msg || 'Erro ao entrar.';
    }
  } catch {
    err.textContent = 'Erro de conexão.';
  }
});

// ─── REGISTER FORM — Passo 1: enviar dados e receber código por email ────
let cadastroEmailPendente = '';

document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const err = document.getElementById('registerError');
  err.textContent = '';

  const aceitouTermos = document.getElementById('registerAceiteTermos')?.checked;
  if (!aceitouTermos) {
    err.textContent = 'Você precisa aceitar os Termos de Uso e a Política de Privacidade.';
    return;
  }

  const data = Object.fromEntries(new FormData(e.target));
  data.aceitou_termos = true;
  data.captcha_token = await getCaptchaToken('register');
  try {
    const res  = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.ok) {
      cadastroEmailPendente = json.email;
      document.getElementById('verifyEmailText').textContent = json.email;
      document.getElementById('verifyError').textContent = '';
      document.getElementById('verifyCode').value = '';
      closeModal('modalRegister');
      openModal('modalVerifyEmail');
    } else {
      err.textContent = json.msg || 'Erro ao cadastrar.';
    }
  } catch {
    err.textContent = 'Erro de conexão.';
  }
});

// ─── REGISTER — Passo 2: confirmar código recebido por email ─────────────
document.getElementById('verifyForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const err  = document.getElementById('verifyError');
  const code = document.getElementById('verifyCode').value.trim();
  err.textContent = '';

  if (!code) {
    err.textContent = 'Digite o código recebido por email.';
    return;
  }

  try {
    const res  = await fetch('/auth/register/confirmar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: cadastroEmailPendente, codigo: code }),
    });
    const json = await res.json();
    if (json.ok) {
      window.location.href = json.redirect || '/';
    } else {
      err.textContent = json.msg || 'Erro ao confirmar código.';
    }
  } catch {
    err.textContent = 'Erro de conexão.';
  }
});

// ─── REGISTER — reenviar código ───────────────────────────────────────────
document.getElementById('btnResendCode')?.addEventListener('click', async () => {
  const err = document.getElementById('verifyError');
  err.textContent = '';
  try {
    const res  = await fetch('/auth/register/reenviar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: cadastroEmailPendente }),
    });
    const json = await res.json();
    if (json.ok) {
      err.style.color = 'var(--accent)';
      err.textContent = 'Código reenviado!';
    } else {
      err.style.color = '';
      err.textContent = json.msg || 'Erro ao reenviar código.';
    }
  } catch {
    err.textContent = 'Erro de conexão.';
  }
});

// ─── SEARCH AUTOCOMPLETE (simples) ───────────────────────────
const searchInput = document.getElementById('searchInput');
let searchTimeout;
searchInput?.addEventListener('input', () => {
  clearTimeout(searchTimeout);
  // Só submete se enter — campo padrão já funciona via form
});
