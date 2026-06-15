/* ─── Menu de 3 pontos nos cards de vídeo ─────────────────────────────────── */

let _menuVideoId   = null;
let _menuVideoTitle = null;
const menu    = document.getElementById('cardContextMenu');
const modal   = document.getElementById('modalSavePlaylist');
let cardToast   = document.getElementById('cardToast');

/* ── abre o menu posicionado perto do botão ── */
function openCardMenu(event, videoId, videoTitle) {
  event.stopPropagation();
  event.preventDefault();

  _menuVideoId    = videoId;
  _menuVideoTitle = videoTitle;

  const btn  = event.currentTarget;
  const rect = btn.getBoundingClientRect();

  menu.style.display = 'block';

  // posiciona à esquerda do botão se ficar fora da tela
  const menuW = 220;
  let left = rect.left + window.scrollX - menuW + rect.width;
  if (left < 8) left = 8;

  menu.style.top  = (rect.bottom + window.scrollY + 6) + 'px';
  menu.style.left = left + 'px';
}

/* ── fecha ao clicar fora ── */
document.addEventListener('click', e => {
  if (!menu.contains(e.target)) menu.style.display = 'none';
});

/* ── SALVAR EM PLAYLIST ── */
document.getElementById('ccmAddPlaylist').addEventListener('click', async () => {
  menu.style.display = 'none';

  const isLoggedIn = document.querySelector('.user-menu') !== null;
  if (!isLoggedIn) { showToast('Faça login para salvar em playlists'); return; }

  const list = document.getElementById('savePlaylistList');
  list.innerHTML = '<p style="color:var(--text-secondary);padding:.5rem 0">Carregando...</p>';
  modal.style.display = 'flex';

  try {
    const res = await fetch('/api/playlists/list');
    const playlists = await res.json();

    if (!playlists.length) {
      list.innerHTML = `
        <p style="color:var(--text-secondary)">Você ainda não tem playlists.</p>
        <a href="/playlists" class="btn-primary" style="margin-top:.75rem;display:inline-block">Criar playlist</a>
      `;
      return;
    }

    list.innerHTML = playlists.map(pl => `
      <button class="ccm-playlist-row" data-id="${pl.id}">
        <span class="ccm-pl-icon">${pl.is_public ? '🌐' : '🔒'}</span>
        <span class="ccm-pl-name">${escapeHtml(pl.name)}</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    `).join('');

    list.querySelectorAll('.ccm-playlist-row').forEach(btn => {
      btn.addEventListener('click', async () => {
        const plId = btn.dataset.id;
        const res  = await fetch(`/api/playlists/${plId}/add-video`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_id: _menuVideoId }),
        });
        const data = await res.json();
        modal.style.display = 'none';
        showToast(data.ok ? 'Vídeo salvo na playlist ✓' : (data.msg || 'Erro ao salvar'));
      });
    });
  } catch (e) {
    list.innerHTML = '<p style="color:var(--text-secondary)">Erro ao carregar playlists.</p>';
  }
});

/* ── fechar modal ── */
document.getElementById('closeSavePlaylist').addEventListener('click', () => {
  modal.style.display = 'none';
});
modal.addEventListener('click', e => {
  if (e.target === modal) modal.style.display = 'none';
});

/* ── COMPARTILHAR ── */
document.getElementById('ccmShare').addEventListener('click', () => {
  menu.style.display = 'none';
  const url = `${location.origin}/watch/${_menuVideoId}`;

  if (navigator.share) {
    navigator.share({ title: _menuVideoTitle, url }).catch(() => {});
  } else {
    navigator.clipboard.writeText(url).then(() => {
      showToast('Link copiado ✓');
    }).catch(() => {
      showToast('Não foi possível copiar o link');
    });
  }
});

/* ── NÃO RECOMENDAR ── */
document.getElementById('ccmNotRecommend').addEventListener('click', () => {
  menu.style.display = 'none';

  // Esconde o card visualmente
  const cards = document.querySelectorAll('.video-card, .video-card-wrapper');
  cards.forEach(card => {
    const titleEl = card.querySelector('.card-title');
    if (titleEl && titleEl.href && titleEl.href.includes(`/watch/${_menuVideoId}`)) {
      card.style.transition = 'opacity .3s, transform .3s';
      card.style.opacity    = '0';
      card.style.transform  = 'scale(.97)';
      setTimeout(() => card.remove(), 320);
    }
  });

  showToast('Vídeo removido das recomendações');
});

/* ── Toast helper ── */
let _toastTimer = null;
function showToast(msg) {
  cardToast.textContent = msg;
  cardToast.style.display = 'block';
  cardToast.classList.add('visible');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => {
    cardToast.classList.remove('visible');
    setTimeout(() => { cardToast.style.display = 'none'; }, 300);
  }, 2800);
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
