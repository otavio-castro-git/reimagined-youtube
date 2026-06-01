/* ═══════════════════════════════════════════════════════════
   ViewTube — upload.js  (upload direto pro Azure Blob via SAS)
   Fluxo:
     1. Usuário seleciona arquivo
     2. JS pede SAS URLs ao Flask (/upload/sas)
     3. JS faz PUT direto pro Blob com progresso real
     4. JS avisa o Flask pra salvar no banco (/upload/confirm)
   ═══════════════════════════════════════════════════════════ */

const uploadDrop     = document.getElementById('uploadDrop');
const videoFile      = document.getElementById('videoFile');
const videoPreview   = document.getElementById('videoPreview');
const previewWrap    = document.getElementById('videoPreviewWrap');
const videoFileName  = document.getElementById('videoFileName');
const thumbFile      = document.getElementById('thumbFile');
const thumbPreview   = document.getElementById('thumbPreview');
const uploadForm     = document.getElementById('uploadForm');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill   = document.getElementById('progressFill');
const progressLabel  = document.getElementById('progressLabel');
const uploadError    = document.getElementById('uploadError');

// ─── DRAG & DROP ─────────────────────────────────────────────
uploadDrop?.addEventListener('click', () => videoFile?.click());
uploadDrop?.addEventListener('dragover', (e) => { e.preventDefault(); uploadDrop.classList.add('drag-over'); });
uploadDrop?.addEventListener('dragleave', () => uploadDrop.classList.remove('drag-over'));
uploadDrop?.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadDrop.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('video/')) setVideoFile(file);
});
videoFile?.addEventListener('change', () => { if (videoFile.files[0]) setVideoFile(videoFile.files[0]); });

function setVideoFile(file) {
  const dt = new DataTransfer();
  dt.items.add(file);
  videoFile.files = dt.files;

  const url = URL.createObjectURL(file);
  videoPreview.src = url;
  videoFileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
  previewWrap?.classList.remove('hidden');
  uploadDrop?.classList.add('hidden');

  const titleInput = uploadForm?.querySelector('[name="title"]');
  if (titleInput && !titleInput.value)
    titleInput.value = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');

  videoPreview.addEventListener('loadedmetadata', () => {
    const dur = Math.round(videoPreview.duration || 0);
    if (dur > 0) uploadForm.dataset.duration = dur;
  }, { once: true });
}

// ─── THUMBNAIL PREVIEW ───────────────────────────────────────
thumbFile?.addEventListener('change', () => {
  const file = thumbFile.files[0];
  if (file) { thumbPreview.src = URL.createObjectURL(file); thumbPreview.classList.remove('hidden'); }
});

// ─── UPLOAD DIRETO VIA SAS ───────────────────────────────────
async function putBlob(sasUrl, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) onProgress(e.loaded, e.total);
    });
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error(`Blob error ${xhr.status}: ${xhr.responseText}`));
    });
    xhr.addEventListener('error', () => reject(new Error('Erro de conexão com o Blob')));
    xhr.open('PUT', sasUrl);
    xhr.setRequestHeader('x-ms-blob-type', 'BlockBlob');
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    xhr.send(file);
  });
}

// ─── FORM SUBMIT ─────────────────────────────────────────────
uploadForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  uploadError.textContent = '';

  const vFile = videoFile.files[0];
  if (!vFile) { uploadError.textContent = 'Selecione um vídeo.'; return; }

  const title = uploadForm.querySelector('[name="title"]')?.value.trim();
  if (!title) { uploadError.textContent = 'Título obrigatório.'; return; }

  const tFile    = thumbFile?.files[0] || null;
  const videoExt = '.' + vFile.name.split('.').pop().toLowerCase();
  const thumbExt = tFile ? '.' + tFile.name.split('.').pop().toLowerCase() : '';

  uploadProgress.classList.remove('hidden');
  uploadForm.querySelector('[type="submit"]').disabled = true;
  setProgress(0, 'Preparando upload…');

  try {
    // 1. Pede SAS URLs ao Flask
    const sasRes = await fetch('/upload/sas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_ext: videoExt, thumb_ext: thumbExt }),
    });
    const sas = await sasRes.json();
    if (!sas.ok) throw new Error(sas.msg);

    // 2. Upload do vídeo direto pro Blob
    setProgress(0, 'Enviando vídeo… 0%');
    await putBlob(sas.video_sas, vFile, (loaded, total) => {
      const pct = Math.round((loaded / total) * 100);
      setProgress(tFile ? pct * 0.85 : pct, `Enviando vídeo… ${pct}%`);
    });

    // 3. Upload da thumbnail (se existir)
    let thumbUrl = null;
    if (tFile && sas.thumb_sas) {
      setProgress(85, 'Enviando thumbnail…');
      await putBlob(sas.thumb_sas, tFile, (loaded, total) => {
        const pct = Math.round((loaded / total) * 100);
        setProgress(85 + pct * 0.1, `Enviando thumbnail… ${pct}%`);
      });
      thumbUrl = sas.thumb_url;
    }

    // 4. Avisa o Flask pra salvar no banco
    setProgress(97, 'Finalizando…');
    const tagIds = [...uploadForm.querySelectorAll('[name="tags"]:checked')].map(el => el.value);
    const confirmRes = await fetch('/upload/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        description: uploadForm.querySelector('[name="description"]')?.value.trim() || '',
        video_url:   sas.video_url,
        thumb_url:   thumbUrl,
        tags:        tagIds,
        duration:    uploadForm.dataset.duration || null,
      }),
    });
    const confirm = await confirmRes.json();
    if (!confirm.ok) throw new Error(confirm.msg);

    setProgress(100, 'Publicado! Redirecionando…');
    setTimeout(() => { window.location.href = confirm.redirect; }, 800);

  } catch (err) {
    uploadError.textContent = err.message || 'Erro no upload.';
    uploadProgress.classList.add('hidden');
    uploadForm.querySelector('[type="submit"]').disabled = false;
  }
});

function setProgress(pct, label) {
  progressFill.style.width = `${Math.round(pct)}%`;
  progressLabel.textContent = label;
}

// ─── CRIAR CANAL MODAL ───────────────────────────────────────
const openCreateChannel  = document.getElementById('openCreateChannel');
const modalCreateChannel = document.getElementById('modalCreateChannel');
const createChannelForm  = document.getElementById('createChannelForm');
const channelError       = document.getElementById('channelError');

openCreateChannel?.addEventListener('click', () => {
  modalCreateChannel.classList.remove('hidden');
  modalCreateChannel.classList.add('open');
  document.body.style.overflow = 'hidden';
});
document.querySelector('[data-close="modalCreateChannel"]')?.addEventListener('click', () => {
  modalCreateChannel.classList.remove('open');
  document.body.style.overflow = '';
});
createChannelForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (channelError) channelError.textContent = '';
  const data = Object.fromEntries(new FormData(e.target));
  const res  = await fetch('/criar-canal', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (json.ok) window.location.reload();
  else if (channelError) channelError.textContent = json.msg;
});