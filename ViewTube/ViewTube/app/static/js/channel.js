/* ═══════════════════════════════════════════════════════════
   ViewTube — channel.js
   Subscribe toggle on channel page
   ═══════════════════════════════════════════════════════════ */

const subscribeBtn = document.getElementById('subscribeBtn');

subscribeBtn?.addEventListener('click', async () => {
  try {
    const res  = await fetch(`/api/channels/${CHANNEL_ID}/subscribe`, { method: 'POST' });
    const json = await res.json();
    subscribeBtn.classList.toggle('subscribed', json.subscribed);
    subscribeBtn.textContent = json.subscribed ? 'Inscrito' : 'Inscrever-se';
    const countEl = document.querySelector('.channel-details p');
    if (countEl) {
      const parts = countEl.textContent.split('·');
      if (parts.length >= 2) {
        countEl.textContent = `${json.count} inscritos · ${parts[1].trim()}`;
      }
    }
  } catch (e) {
    console.error('Subscribe error:', e);
  }
});

// Modal para criar canal (usado na página criar_canal.html inline)
const createChannelForm = document.getElementById('createChannelForm');
if (createChannelForm && document.getElementById('modalCreateChannel')) {
  document.getElementById('openCreateChannel')?.addEventListener('click', () => {
    document.getElementById('modalCreateChannel').classList.add('open');
    document.body.style.overflow = 'hidden';
  });
  document.querySelector('[data-close="modalCreateChannel"]')?.addEventListener('click', () => {
    document.getElementById('modalCreateChannel').classList.remove('open');
    document.body.style.overflow = '';
  });

  createChannelForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const err  = document.getElementById('channelError');
    err.textContent = '';
    const data = Object.fromEntries(new FormData(e.target));
    const res  = await fetch('/criar-canal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.ok) window.location.href = `/canal/${json.id}`;
    else err.textContent = json.msg;
  });
}
