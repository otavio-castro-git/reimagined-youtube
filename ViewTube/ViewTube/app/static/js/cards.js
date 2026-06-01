/* ═══════════════════════════════════════════════════════════
   ViewTube — cards.js
   Hover preview + duration badge auto-fill
   ═══════════════════════════════════════════════════════════ */

function fmtSec(s) {
  if (!s || isNaN(s)) return '';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h) return `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
  return `${m}:${String(sec).padStart(2,'0')}`;
}

document.querySelectorAll('.video-card').forEach(card => {
  const thumbWrap  = card.querySelector('.card-thumb');
  const thumbInner = card.querySelector('.card-thumb-inner');
  const imgEl      = card.querySelector('.card-thumb-img');
  const previewVid = card.querySelector('.card-preview-video');
  const badge      = card.querySelector('.duration-badge');
  const fillBar    = card.querySelector('.card-preview-fill');
  const videoUrl   = card.dataset.videoUrl;

  if (!previewVid || !videoUrl) return;

  let hoverTimer  = null;
  let progTimer   = null;

  // ── On mouseenter — wait 800ms then start preview ──────────
  thumbWrap.addEventListener('mouseenter', () => {
    hoverTimer = setTimeout(() => {
      previewVid.src = videoUrl;
      previewVid.currentTime = 3; // skip first 3s like YouTube
      previewVid.play().catch(() => {});
      previewVid.classList.add('visible');
      if (imgEl) imgEl.style.opacity = '0';

      // Update progress bar
      progTimer = setInterval(() => {
        if (previewVid.duration) {
          const pct = (previewVid.currentTime / previewVid.duration) * 100;
          if (fillBar) fillBar.style.width = `${pct}%`;
        }
      }, 200);

      // Fill duration badge if still empty
      previewVid.addEventListener('loadedmetadata', () => {
        if (badge && !badge.textContent.trim()) {
          badge.textContent = fmtSec(previewVid.duration);
        }
      }, { once: true });

      // Loop preview within itself
      previewVid.addEventListener('ended', () => {
        previewVid.currentTime = 3;
        previewVid.play().catch(() => {});
      });

    }, 800);
  });

  // ── On mouseleave — stop preview ───────────────────────────
  thumbWrap.addEventListener('mouseleave', () => {
    clearTimeout(hoverTimer);
    clearInterval(progTimer);
    previewVid.pause();
    previewVid.src = '';
    previewVid.classList.remove('visible');
    if (imgEl) imgEl.style.opacity = '';
    if (fillBar) fillBar.style.width = '0%';
  });
});
