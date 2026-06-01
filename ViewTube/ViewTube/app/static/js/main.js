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

// ─── LOGIN FORM ──────────────────────────────────────────────
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const err = document.getElementById('loginError');
  err.textContent = '';
  const data = Object.fromEntries(new FormData(e.target));
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

// ─── REGISTER FORM ───────────────────────────────────────────
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const err = document.getElementById('registerError');
  err.textContent = '';
  const data = Object.fromEntries(new FormData(e.target));
  try {
    const res  = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.ok) {
      window.location.href = json.redirect || '/';
    } else {
      err.textContent = json.msg || 'Erro ao cadastrar.';
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
