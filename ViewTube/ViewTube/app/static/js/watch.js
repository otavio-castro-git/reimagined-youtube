/* ═══════════════════════════════════════════════════════════
   ViewTube — watch.js  (Custom Player + Like + Comments)
   ═══════════════════════════════════════════════════════════ */

// ─── CUSTOM PLAYER ──────────────────────────────────────────
const wrap       = document.getElementById('vtPlayerWrap');
const video      = document.getElementById('videoPlayer');
const overlay    = document.getElementById('vtPlayOverlay');
const controls   = document.getElementById('vtControls');
const progress   = document.getElementById('vtProgress');
const buffered   = document.getElementById('vtBuffered');
const played     = document.getElementById('vtPlayed');
const thumb      = document.getElementById('vtThumb');
const playPause  = document.getElementById('vtPlayPause');
const iconPlay   = document.getElementById('vtIconPlay');
const iconPause  = document.getElementById('vtIconPause');
const muteBtn    = document.getElementById('vtMute');
const volSlider  = document.getElementById('vtVolume');
const timeEl     = document.getElementById('vtTime');
const fsBtn      = document.getElementById('vtFullscreen');
const iconFs     = document.getElementById('vtIconFs');
const iconFsExit = document.getElementById('vtIconFsExit');
const speedBtn   = document.getElementById('vtSpeedBtn');
const speedMenu  = document.getElementById('vtSpeedMenu');
const settingsBtn    = document.getElementById('vtSettings');
const settingsMenu   = document.getElementById('vtSettingsMenu');
const loopToggle     = document.getElementById('vtLoopToggle');
const loopState      = document.getElementById('vtLoopState');
const autoplayToggle = document.getElementById('vtAutoplayToggle');
const autoplayState  = document.getElementById('vtAutoplayState');
const downloadBtn    = document.getElementById('vtDownload');
const toast          = document.getElementById('vtToast');

let controlsTimer;
let isDragging  = false;
let isLoop      = false;
let isAutoplay  = true;
let lastVol     = 1;
let hasStarted  = false; // ← flag: autoplay só roda UMA vez

// ── Helpers ─────────────────────────────────────────────────
function fmtTime(s) {
  if (isNaN(s)) return '0:00';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h) return `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
  return `${m}:${String(sec).padStart(2,'0')}`;
}

function setPct(pct) {
  played.style.width = `${pct}%`;
  thumb.style.left   = `${pct}%`;
}

function showControls() {
  wrap.classList.add('controls-visible');
  clearTimeout(controlsTimer);
  if (!video.paused) {
    controlsTimer = setTimeout(() => wrap.classList.remove('controls-visible'), 3000);
  }
}

function showToast(msg, duration = 3000) {
  toast.textContent = msg;
  toast.classList.add('visible');
  setTimeout(() => toast.classList.remove('visible'), duration);
}

function closeAllMenus() {
  speedMenu.classList.remove('open');
  settingsMenu.classList.remove('open');
}

// ── Spinner de buffering ─────────────────────────────────────
const spinner = document.createElement('div');
spinner.className = 'vt-spinner';
spinner.innerHTML = `<div class="vt-spinner-ring"></div>`;
wrap.appendChild(spinner);

video.addEventListener('waiting', () => spinner.classList.add('visible'));
video.addEventListener('playing', () => spinner.classList.remove('visible'));
video.addEventListener('seeked',  () => spinner.classList.remove('visible'));

// ── Play / Pause ─────────────────────────────────────────────
function togglePlay() {
  if (video.paused) { video.play(); } else { video.pause(); }
}

video.addEventListener('play', () => {
  iconPlay.style.display  = 'none';
  iconPause.style.display = '';
  overlay.style.display   = 'none';
  showControls();
});
video.addEventListener('pause', () => {
  iconPlay.style.display  = '';
  iconPause.style.display = 'none';
  overlay.style.display   = 'flex';
  wrap.classList.add('controls-visible');
  clearTimeout(controlsTimer);
});
video.addEventListener('ended', () => {
  iconPlay.style.display  = '';
  iconPause.style.display = 'none';
  overlay.style.display   = 'flex';
  hasStarted = false; // permite autoplay se o vídeo reiniciar
});

playPause.addEventListener('click', togglePlay);
overlay.addEventListener('click', togglePlay);
video.addEventListener('click', togglePlay);
wrap.addEventListener('dblclick', toggleFullscreen);

// ── Autoplay — dispara APENAS na carga inicial ───────────────
// Usa loadedmetadata em vez de canplay — não re-dispara após seek
video.addEventListener('loadedmetadata', () => {
  timeEl.textContent = `0:00 / ${fmtTime(video.duration)}`;

  // Salva duração no banco se ainda não tiver
  if (IS_AUTH && VIDEO_ID && video.duration) {
    fetch(`/api/videos/${VIDEO_ID}/duration`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seconds: Math.round(video.duration) }),
    }).catch(() => {});
  }

  // Autoplay inicial — só uma vez, nunca após seek
  if (isAutoplay && !hasStarted) {
    hasStarted = true;
    video.play().catch(() => {});
  }
});

// ── Progress ─────────────────────────────────────────────────
video.addEventListener('timeupdate', () => {
  if (!isDragging && video.duration) {
    const pct = (video.currentTime / video.duration) * 100;
    setPct(pct);
    timeEl.textContent = `${fmtTime(video.currentTime)} / ${fmtTime(video.duration)}`;
  }
});

video.addEventListener('progress', () => {
  if (video.duration && video.buffered.length) {
    const end = video.buffered.end(video.buffered.length - 1);
    buffered.style.width = `${(end / video.duration) * 100}%`;
  }
});

function seekFromEvent(e) {
  const rect = progress.getBoundingClientRect();
  const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  video.currentTime = pct * video.duration;
  setPct(pct * 100);
}

progress.addEventListener('mousedown', (e) => {
  isDragging = true;
  seekFromEvent(e);
});
document.addEventListener('mousemove', (e) => { if (isDragging) seekFromEvent(e); });
document.addEventListener('mouseup',   ()  => { isDragging = false; });

// Touch support for progress
progress.addEventListener('touchstart', (e) => {
  isDragging = true;
  seekFromEvent(e.touches[0]);
}, { passive: true });
document.addEventListener('touchmove', (e) => { if (isDragging) seekFromEvent(e.touches[0]); }, { passive: true });
document.addEventListener('touchend',  ()  => { isDragging = false; });

// ── Volume ───────────────────────────────────────────────────
function updateVolIcon() {
  const v    = video.volume;
  const muted = video.muted || v === 0;
  const wave1 = document.getElementById('vtVolWave1');
  const wave2 = document.getElementById('vtVolWave2');
  if (muted) {
    wave1 && (wave1.style.display = 'none');
    wave2 && (wave2.style.display = 'none');
  } else if (v < 0.5) {
    wave1 && (wave1.style.display = '');
    wave2 && (wave2.style.display = 'none');
  } else {
    wave1 && (wave1.style.display = '');
    wave2 && (wave2.style.display = '');
  }
}

muteBtn.addEventListener('click', () => {
  video.muted = !video.muted;
  volSlider.value = video.muted ? 0 : video.volume;
  updateVolIcon();
});

volSlider.addEventListener('input', () => {
  video.volume = parseFloat(volSlider.value);
  video.muted  = video.volume === 0;
  lastVol = video.volume || lastVol;
  updateVolIcon();
});

// ── Speed ────────────────────────────────────────────────────
speedBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  settingsMenu.classList.remove('open');
  speedMenu.classList.toggle('open');
});

speedMenu.querySelectorAll('[data-speed]').forEach(btn => {
  btn.addEventListener('click', () => {
    video.playbackRate = parseFloat(btn.dataset.speed);
    speedBtn.textContent = `${btn.dataset.speed}×`;
    speedMenu.querySelectorAll('.vt-menu-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    speedMenu.classList.remove('open');
  });
});

// ── Settings ─────────────────────────────────────────────────
settingsBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  speedMenu.classList.remove('open');
  settingsMenu.classList.toggle('open');
});

loopToggle.addEventListener('click', () => {
  isLoop = !isLoop;
  video.loop = isLoop;
  loopState.textContent = isLoop ? 'On' : 'Off';
});

autoplayToggle.addEventListener('click', () => {
  isAutoplay = !isAutoplay;
  autoplayState.textContent = isAutoplay ? 'On' : 'Off';
});

document.addEventListener('click', closeAllMenus);

// ── Fullscreen ───────────────────────────────────────────────
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    wrap.requestFullscreen?.() || wrap.webkitRequestFullscreen?.();
  } else {
    document.exitFullscreen?.() || document.webkitExitFullscreen?.();
  }
}
fsBtn.addEventListener('click', toggleFullscreen);

document.addEventListener('fullscreenchange', () => {
  const fs = !!document.fullscreenElement;
  iconFs.style.display     = fs ? 'none' : '';
  iconFsExit.style.display = fs ? '' : 'none';
  wrap.classList.toggle('vt-fullscreen', fs);
});

// ── Download ─────────────────────────────────────────────────
downloadBtn.addEventListener('click', () => {
  if (downloadBtn.dataset.premium !== 'true') {
    showToast(!IS_AUTH
      ? '🔒 Faça login para baixar vídeos.'
      : '⭐ Apenas usuários Premium podem baixar vídeos.'
    );
    return;
  }
  const a = document.createElement('a');
  a.href     = downloadBtn.dataset.url;
  a.download = (downloadBtn.dataset.title || 'video') + '.mp4';
  a.target   = '_blank';
  a.click();
});

// ── Controls visibility ──────────────────────────────────────
wrap.addEventListener('mousemove', showControls);
wrap.addEventListener('mouseleave', () => {
  if (!video.paused) {
    clearTimeout(controlsTimer);
    controlsTimer = setTimeout(() => wrap.classList.remove('controls-visible'), 800);
  }
});
wrap.classList.add('controls-visible');

// ── Keyboard shortcuts ───────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
  switch (e.key) {
    case ' ': case 'k': e.preventDefault(); togglePlay(); break;
    case 'f': case 'F': toggleFullscreen(); break;
    case 'm': case 'M': muteBtn.click(); break;
    case 'ArrowRight':
      video.currentTime = Math.min(video.currentTime + 5, video.duration); break;
    case 'ArrowLeft':
      video.currentTime = Math.max(video.currentTime - 5, 0); break;
    case 'ArrowUp':
      e.preventDefault();
      video.volume = Math.min(1, video.volume + 0.1);
      volSlider.value = video.volume; updateVolIcon(); break;
    case 'ArrowDown':
      e.preventDefault();
      video.volume = Math.max(0, video.volume - 0.1);
      volSlider.value = video.volume; updateVolIcon(); break;
  }
});

// ─── VIDEO PROGRESS SAVE ────────────────────────────────────
let progressTimer;
video.addEventListener('play', () => {
  clearInterval(progressTimer);
  progressTimer = setInterval(() => {
    if (!IS_AUTH) return;
    fetch(`/api/videos/${VIDEO_ID}/progress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seconds: Math.floor(video.currentTime) }),
    }).catch(() => {});
  }, 10000);
});
video.addEventListener('pause', () => clearInterval(progressTimer));
video.addEventListener('ended', () => {
  clearInterval(progressTimer);
  if (IS_AUTH) {
    fetch(`/api/videos/${VIDEO_ID}/progress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seconds: Math.floor(video.duration || 0) }),
    }).catch(() => {});
  }
});

// ─── LIKE ────────────────────────────────────────────────────
const likeBtn   = document.getElementById('likeBtn');
const likeCount = document.getElementById('likeCount');

likeBtn?.addEventListener('click', async () => {
  if (!IS_AUTH) { openModal('modalLogin'); return; }
  try {
    const res  = await fetch(`/api/videos/${VIDEO_ID}/like`, { method: 'POST' });
    const json = await res.json();
    likeCount.textContent = json.likes;
    likeBtn.classList.toggle('liked', json.liked);
    const icon = likeBtn.querySelector('svg');
    if (icon) icon.setAttribute('fill', json.liked ? 'currentColor' : 'none');
  } catch (e) { console.error('Like error:', e); }
});

// ─── SUBSCRIBE ───────────────────────────────────────────────
const subscribeBtn = document.getElementById('subscribeBtn');
subscribeBtn?.addEventListener('click', async () => {
  if (!IS_AUTH) { openModal('modalLogin'); return; }
  const channelId = subscribeBtn.dataset.channel;
  try {
    const res  = await fetch(`/api/channels/${channelId}/subscribe`, { method: 'POST' });
    const json = await res.json();
    subscribeBtn.classList.toggle('subscribed', json.subscribed);
    subscribeBtn.textContent = json.subscribed ? 'Inscrito' : 'Inscrever-se';
    const countEl = document.querySelector('.channel-info small');
    if (countEl) countEl.textContent = `${json.count} inscritos`;
  } catch (e) { console.error('Subscribe error:', e); }
});

// ─── COMMENTS ────────────────────────────────────────────────
const commentInput   = document.getElementById('commentInput');
const commentActions = document.getElementById('commentActions');
const cancelComment  = document.getElementById('cancelComment');
const postComment    = document.getElementById('postComment');
const commentsList   = document.getElementById('commentsList');

commentInput?.addEventListener('focus', () => {
  commentActions?.classList.remove('hidden');
  commentInput.rows = 3;
});
cancelComment?.addEventListener('click', () => {
  commentInput.value = '';
  commentInput.rows  = 1;
  commentActions?.classList.add('hidden');
});
postComment?.addEventListener('click', async () => {
  const content = commentInput.value.trim();
  if (!content) return;
  postComment.disabled = true;
  try {
    const res  = await fetch(`/api/videos/${VIDEO_ID}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    const json = await res.json();
    if (json.ok) {
      commentInput.value = '';
      commentInput.rows  = 1;
      commentActions?.classList.add('hidden');
      const div = document.createElement('div');
      div.className = 'comment';
      const avatarHtml = json.profile_image
        ? `<img src="${json.profile_image}" alt="${json.username}">`
        : `<div class="avatar-placeholder">${json.username[0].toUpperCase()}</div>`;
      div.innerHTML = `
        <div class="comment-avatar">${avatarHtml}</div>
        <div class="comment-body">
          <span class="comment-author">${json.username}</span>
          <span class="comment-date">${json.created_at}</span>
          <p>${escapeHtml(json.content)}</p>
        </div>`;
      commentsList.insertBefore(div, commentsList.firstChild);
      const h3 = document.querySelector('.comments-section h3');
      if (h3) {
        const n = (parseInt(h3.textContent) || 0) + 1;
        h3.textContent = `${n} comentário${n !== 1 ? 's' : ''}`;
      }
    }
  } catch (e) { console.error('Comment error:', e); }
  postComment.disabled = false;
});

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

// ─── SHARE ───────────────────────────────────────────────────
document.getElementById('shareBtn')?.addEventListener('click', () => {
  if (navigator.share) {
    navigator.share({ title: document.title, url: window.location.href });
  } else {
    navigator.clipboard.writeText(window.location.href).then(() => showToast('🔗 Link copiado!'));
  }
});

// ─── DESCRIPTION EXPAND ──────────────────────────────────────
document.getElementById('expandDesc')?.addEventListener('click', function () {
  const full  = document.querySelector('.desc-full');
  const short = document.querySelector('#videoDesc > p');
  if (full && short) {
    short.style.display = 'none';
    full.classList.remove('hidden');
    this.style.display  = 'none';
  }
});

function openModal(id) {
  document.getElementById(id)?.classList.add('open');
  document.body.style.overflow = 'hidden';
}