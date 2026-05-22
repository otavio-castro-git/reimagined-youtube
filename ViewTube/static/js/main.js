"use strict";

// ─── UTILS ────────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

function formatViews(v) {
  if (typeof v === "string" && isNaN(v)) return v;
  const n = Number(v);
  if (n >= 1e9) return (n / 1e9).toFixed(1) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
}

function timeAgo(d) {
  if (!d) return "";
  const ms = Date.now() - new Date(d).getTime();
  const s = ms / 1000, m = s / 60, h = m / 60, dy = h / 24, y = dy / 365;
  if (y >= 1) return Math.floor(y) + "a atrás";
  if (dy >= 1) return Math.floor(dy) + "d atrás";
  if (h >= 1) return Math.floor(h) + "h atrás";
  if (m >= 1) return Math.floor(m) + "min atrás";
  return "agora";
}

// Generate a deterministic color from a string
function strColor(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
  return `hsl(${Math.abs(hash) % 360},55%,42%)`;
}

function initials(name) {
  return name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

// ─── TOAST ────────────────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 3000);
}

// ─── API HELPERS ──────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  try {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...opts
    });
    return await res.json();
  } catch (e) {
    console.error("API error:", e);
    return null;
  }
}

// ─── STATE ────────────────────────────────────────────────────────────────────
const State = {
  currentFilter: "all",
  sidebarCollapsed: false,
  searchDebounce: null,
  currentVideoId: null,
  currentPage: "home",
  currentChannel: null,
  channels: [],       // loaded from API
  heroVideo: null,
};

// ─── NAVIGATION ───────────────────────────────────────────────────────────────
function navigateTo(section, extra = null) {
  $$(".page-view").forEach(p => p.classList.remove("active"));
  $$(".nav-item").forEach(i => i.classList.remove("active"));

  State.currentPage = section;
  const target = $(`page-${section}`);
  if (target) target.classList.add("active");

  const sidebarBtn = document.querySelector(`.nav-item[data-section="${section}"]`);
  if (sidebarBtn) sidebarBtn.classList.add("active");

  if (section === "home") loadHome(State.currentFilter);
  else if (section === "seguindo") loadSeguindo();
  else if (section === "playlists") loadPlaylists();
  else if (section === "channel") loadChannel(extra);
  else if (section === "database") loadDatabase();
  else if (section === "trending") loadTrending();
  else if (section === "history") loadHistory();
  else if (section === "liked") loadLiked();
  else if (section === "logout") { showToast("👋 Até logo!"); return; }
  else if (section === "settings") { showToast("⚙️ Configurações em breve!"); return; }
  else if (!target) {
    $("page-home").classList.add("active");
    showToast(`📂 "${section}" em breve!`);
    return;
  }

  if (window.innerWidth <= 900) $("sidebar").classList.remove("mobile-open");
}

// ─── SIDEBAR TOGGLE ───────────────────────────────────────────────────────────
function toggleSidebar() {
  const sb = $("sidebar");
  if (window.innerWidth <= 900) {
    sb.classList.toggle("mobile-open");
  } else {
    State.sidebarCollapsed = !State.sidebarCollapsed;
    sb.classList.toggle("collapsed", State.sidebarCollapsed);
    $("mainContent").style.marginLeft = State.sidebarCollapsed
      ? "var(--sidebar-w-collapsed)"
      : "var(--sidebar-w)";
  }
}

// ─── VIDEO CARD RENDERER ──────────────────────────────────────────────────────
function createVideoCard(video, delay = 0) {
  const card = document.createElement("div");
  card.className = "video-card";
  card.style.animationDelay = `${delay}ms`;
  card.dataset.id = video.id;

  const thumb = video.thumbnail_url || `https://picsum.photos/seed/${video.id}/480/270`;
  const color = strColor(video.channel || "");
  const ini = initials(video.channel || "VT");
  const dur = video.duration_fmt || video.duration || "0:00";
  const views = video.views_fmt || formatViews(video.views || 0);
  const date = video.created_at || video.watched_at || "";

  card.innerHTML = `
    <div class="card-thumb-wrap">
      <img class="card-thumbnail" src="${thumb}" alt="${video.title}" loading="lazy"
        onerror="this.src='https://picsum.photos/seed/${video.id}/480/270'">
      <div class="card-play-overlay">
        <div class="card-play-btn"><span class="material-symbols-rounded">play_arrow</span></div>
      </div>
      <span class="card-duration">${dur}</span>
    </div>
    <div class="card-body">
      <div class="card-channel-avatar" style="background:${color}">${ini}</div>
      <div class="card-info">
        <p class="card-title">${video.title}</p>
        <div class="card-meta">
          <span>${video.channel}</span>
          <span>${views} views • ${timeAgo(date)}</span>
        </div>
      </div>
      <button class="card-menu" title="Mais opções">
        <span class="material-symbols-rounded">more_vert</span>
      </button>
    </div>`;

  card.addEventListener("click", e => {
    if (!e.target.closest(".card-menu"))
      openVideo(video.video_url, video.title, video.channel, video.id);
  });
  card.querySelector(".card-menu").addEventListener("click", e => {
    e.stopPropagation();
    showToast("📋 Opções em breve!");
  });
  return card;
}

function renderGrid(containerId, videos) {
  const grid = $(containerId);
  if (!grid) return;
  grid.innerHTML = "";
  if (!videos || !videos.length) {
    grid.innerHTML = `<p style="color:var(--text-muted);font-size:.9rem;grid-column:1/-1;padding:20px 0">Nenhum vídeo encontrado.</p>`;
    return;
  }
  videos.forEach((v, i) => grid.appendChild(createVideoCard(v, i * 60)));
}

// ─── OPEN VIDEO MODAL ─────────────────────────────────────────────────────────
function openVideo(url, title, channel, videoId) {
  $("videoFrame").src = url + "?autoplay=1";
  $("modalTitle").textContent = title;
  $("modalChannel").textContent = channel;
  $("videoModal").classList.add("active");
  document.body.style.overflow = "hidden";
  State.currentVideoId = videoId;

  // register watch
  if (videoId) {
    api(`/api/videos/${videoId}/watch`, { method: "POST" });
  }

  // load likes count
  api(`/api/videos?tag=all`).then(videos => {
    if (!videos) return;
    const v = videos.find(x => x.id == videoId);
    if (v) $("likeCount").textContent = formatViews(v.likes_count || 0);
  });

  // reset liked state
  $("likeBtn").classList.remove("liked");
}

// ─── HOME PAGE ────────────────────────────────────────────────────────────────
async function loadHome(filter = "all") {
  State.currentFilter = filter;
  const [videos, trending] = await Promise.all([
    api(`/api/videos?tag=${filter}`),
    api("/api/videos/trending")
  ]);
  if (videos) renderGrid("videoGrid", videos);
  if (trending) {
    renderGrid("trendingGrid", filter === "all" ? trending : (videos || []).filter(v => v.views > 50000));
    updateHero(trending[0]);
  }
}

function updateHero(video) {
  if (!video) return;
  State.heroVideo = video;
  $("heroBg").style.backgroundImage = `url('${video.thumbnail_url || ""}')`;
  $("heroTitle").textContent = video.title;
  $("heroChannel").textContent = `${video.channel} • ${formatViews(video.views)} visualizações`;
  $("heroPlayBtn").onclick = () => openVideo(video.video_url, video.title, video.channel, video.id);
}

// ─── FILTER CHIPS ─────────────────────────────────────────────────────────────
async function initFilterChips() {
  const tags = await api("/api/tags");
  const bar = $("filterBar");
  if (!tags) return;

  // Keep "Tudo" chip, add others
  const labelMap = {
    music: "Música", gaming: "Games", film: "Cinema",
    tech: "Tecnologia", sports: "Esportes", news: "Notícias", comedy: "Comédia"
  };
  tags.forEach(tag => {
    if (bar.querySelector(`[data-filter="${tag}"]`)) return;
    const btn = document.createElement("button");
    btn.className = "chip";
    btn.dataset.filter = tag;
    btn.textContent = labelMap[tag] || tag.charAt(0).toUpperCase() + tag.slice(1);
    bar.appendChild(btn);
  });

  bar.addEventListener("click", e => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    $$(".chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    loadHome(chip.dataset.filter);
  });
}

// ─── TRENDING PAGE ────────────────────────────────────────────────────────────
async function loadTrending() {
  $("page-home").classList.add("active");
  const videos = await api("/api/videos/trending");
  if (videos) renderGrid("videoGrid", videos);
  showToast("🔥 Em Alta");
}

// ─── HISTORY PAGE ─────────────────────────────────────────────────────────────
async function loadHistory() {
  $("page-home").classList.add("active");
  const videos = await api("/api/history");
  if (videos) renderGrid("videoGrid", videos);
  showToast(`📜 Histórico: ${videos ? videos.length : 0} vídeos`);
}

// ─── LIKED PAGE ───────────────────────────────────────────────────────────────
async function loadLiked() {
  $("page-home").classList.add("active");
  const videos = await api("/api/liked");
  if (videos) renderGrid("videoGrid", videos);
  showToast(`❤️ Vídeos curtidos: ${videos ? videos.length : 0}`);
}

// ─── SEGUINDO PAGE ────────────────────────────────────────────────────────────
async function loadSeguindo() {
  const channels = await api("/api/channels");
  if (!channels) return;
  State.channels = channels;

  const strip = $("channelsStrip");
  strip.innerHTML = "";
  channels.forEach(ch => {
    const color = strColor(ch.name);
    const pill = document.createElement("div");
    pill.className = "channel-pill";
    pill.innerHTML = `
      <div class="channel-pill-avatar" style="background:${color}">${initials(ch.name)}</div>
      <span class="channel-pill-name">${ch.name}</span>`;
    pill.addEventListener("click", () => navigateTo("channel", ch.id));
    strip.appendChild(pill);
  });

  // featured row
  const allVideos = await api("/api/videos?tag=all");
  if (!allVideos) return;

  const featRow = $("featuredRow");
  featRow.innerHTML = "";
  allVideos.slice(0, 4).forEach((v, i) => {
    const color = strColor(v.channel || "");
    const card = document.createElement("div");
    card.className = "featured-card" + (i === 0 ? " big" : "");
    const thumb = v.thumbnail_url || `https://picsum.photos/seed/${v.id}/480/270`;
    card.innerHTML = `
      <img class="featured-thumb" src="${thumb}" alt="${v.title}"
        onerror="this.src='https://picsum.photos/seed/${v.id}/480/270'">
      <div class="featured-overlay"></div>
      <div class="featured-info">
        <div class="featured-channel-row">
          <div class="featured-channel-avatar" style="background:${color}">${initials(v.channel)}</div>
          <span class="featured-channel-name">${v.channel}</span>
        </div>
        <p class="featured-title">${v.title}</p>
        <p class="featured-meta">${v.views_fmt || formatViews(v.views)} views</p>
      </div>
      <button class="watch-btn"><span class="material-symbols-rounded">play_arrow</span>Assistir</button>`;
    card.addEventListener("click", () => openVideo(v.video_url, v.title, v.channel, v.id));
    featRow.appendChild(card);
  });

  renderGrid("seguindoGrid", allVideos.slice(0, 8));
}

// ─── PLAYLISTS PAGE ───────────────────────────────────────────────────────────
async function loadPlaylists() {
  const playlists = await api("/api/playlists");
  const grid = $("playlistsGrid");
  grid.innerHTML = "";
  if (!playlists) return;

  playlists.forEach((pl, i) => {
    const card = document.createElement("div");
    card.className = "playlist-card";
    card.style.animationDelay = `${i * 60}ms`;
    const thumb = pl.thumbnail_url || `https://picsum.photos/seed/pl${pl.id}/480/270`;
    card.innerHTML = `
      <div class="playlist-thumb-stack">
        <img src="${thumb}" alt="${pl.name}"
          onerror="this.src='https://picsum.photos/seed/pl${pl.id}/480/270'">
        ${!pl.is_public ? `<div class="playlist-lock"><span class="material-symbols-rounded" style="font-size:12px">lock</span>Privada</div>` : ""}
        <div class="playlist-count">${pl.video_count} vídeos</div>
        <div class="play-overlay-pl">
          <div class="card-play-btn"><span class="material-symbols-rounded">play_arrow</span></div>
        </div>
        <div class="playlist-stack-layers">
          <div class="stack-bar"></div><div class="stack-bar"></div><div class="stack-bar"></div>
        </div>
      </div>
      <div class="playlist-info">
        <p class="playlist-name">${pl.name}</p>
        <p class="playlist-meta">${pl.video_count} vídeos • ${pl.is_public ? "Pública" : "Privada"}</p>
      </div>`;
    card.addEventListener("click", () => showToast(`▶ Playlist: ${pl.name}`));
    grid.appendChild(card);
  });

  // New playlist card
  const nc = document.createElement("div");
  nc.className = "playlist-card new-card";
  nc.innerHTML = `<span class="material-symbols-rounded">add_circle</span><span>Nova Playlist</span>`;
  nc.addEventListener("click", () => {
    $("newPlaylistModal").classList.add("active");
    document.body.style.overflow = "hidden";
  });
  grid.appendChild(nc);
}

// ─── CHANNEL PAGE ─────────────────────────────────────────────────────────────
async function loadChannel(channelId) {
  const channels = await api("/api/channels");
  if (!channels) return;

  // accept channel id (number) or name (string)
  let ch = typeof channelId === "number" || !isNaN(channelId)
    ? channels.find(c => c.id == channelId)
    : channels.find(c => c.name === channelId);
  if (!ch) ch = channels[0];
  if (!ch) return;

  State.currentChannel = ch;
  const color = strColor(ch.name);

  $("channelAvatarLg").style.background = color;
  $("channelAvatarLg").textContent = initials(ch.name);
  $("channelName").textContent = ch.name;
  $("channelSubs").textContent = `${formatViews(ch.subscribers)} inscritos`;

  const videos = await api(`/api/channels/${ch.id}/videos`);
  if (videos) renderGrid("channelGrid", videos);

  $$(".channel-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      $$(".channel-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const t = tab.dataset.tab;
      if (t === "videos" && videos) renderGrid("channelGrid", videos);
      else if (t === "playlists") showToast("📂 Playlists do canal em breve!");
      else if (t === "sobre")
        $("channelGrid").innerHTML = `<div style="grid-column:1/-1;padding:20px;color:var(--text-secondary);line-height:1.7">${ch.description || "Sem descrição."}</div>`;
    });
  });
}

// ─── SUBSCRIBE TOGGLE ─────────────────────────────────────────────────────────
async function toggleSubscribe() {
  const ch = State.currentChannel;
  if (!ch) return;
  const data = await api(`/api/channels/${ch.id}/subscribe`, { method: "POST" });
  if (!data) return;
  const subBtn = $("subscribeBtn");
  if (data.subscribed) {
    subBtn.className = "btn-subscribe";
    subBtn.innerHTML = `<span class="material-symbols-rounded">notifications</span>Inscrever-se`;
    showToast(`🔔 Inscrito em ${ch.name}!`);
  } else {
    subBtn.className = "btn-subscribe subscribed";
    subBtn.innerHTML = `<span class="material-symbols-rounded">notifications_off</span>Inscrito`;
    showToast(`🔕 Inscrição cancelada em ${ch.name}`);
  }
  $("channelSubs").textContent = `${formatViews(data.subscribers)} inscritos`;
}

// ─── SIDEBAR CHANNELS ─────────────────────────────────────────────────────────
async function loadSidebarChannels() {
  const channels = await api("/api/channels");
  if (!channels) return;
  State.channels = channels;
  const container = $("sidebarChannels");
  container.innerHTML = "";
  channels.forEach(ch => {
    const color = strColor(ch.name);
    const btn = document.createElement("button");
    btn.className = "nav-item channel-item";
    btn.dataset.section = "channel";
    btn.dataset.channel = ch.id;
    btn.innerHTML = `
      <div class="channel-avatar" style="background:${color};width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;color:white;flex-shrink:0">${initials(ch.name)}</div>
      <span>${ch.name}</span>`;
    btn.addEventListener("click", () => navigateTo("channel", ch.id));
    container.appendChild(btn);
  });
}

// ─── SEARCH ───────────────────────────────────────────────────────────────────
async function handleSearch(q) {
  const box = $("searchResults");
  if (!q.trim()) { box.classList.add("hidden"); return; }
  const results = await api(`/api/videos/search?q=${encodeURIComponent(q)}`);
  if (!results) return;
  box.classList.remove("hidden");
  box.innerHTML = "";
  if (!results.length) {
    box.innerHTML = `<div class="search-result-item"><span class="material-symbols-rounded">search_off</span><span>Nenhum resultado encontrado.</span></div>`;
    return;
  }
  results.slice(0, 8).forEach(v => {
    const item = document.createElement("div");
    item.className = "search-result-item";
    item.innerHTML = `<span class="material-symbols-rounded">play_circle</span><span>${v.title} — ${v.channel}</span>`;
    item.addEventListener("click", () => {
      box.classList.add("hidden");
      $("searchInput").value = "";
      openVideo(v.video_url, v.title, v.channel, v.id);
    });
    box.appendChild(item);
  });
}

// ─── DATABASE PAGE ────────────────────────────────────────────────────────────
async function loadDatabase() {
  const tables = await api("/api/db/tables");
  if (!tables) return;
  const list = $("dbTableList");
  list.innerHTML = "";
  tables.forEach(t => {
    const btn = document.createElement("button");
    btn.className = "db-table-btn";
    btn.dataset.table = t.name;
    btn.innerHTML = `
      <span class="material-symbols-rounded">table_rows</span>
      ${t.name}
      <span class="table-count">${t.count}</span>`;
    btn.addEventListener("click", () => {
      $$(".db-table-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      $("dbQueryInput").value = `SELECT * FROM ${t.name} LIMIT 20;`;
    });
    list.appendChild(btn);
  });

  // schema
  const schemaView = $("dbSchemaView");
  schemaView.innerHTML = "";
  for (const t of tables) {
    const schema = await api(`/api/db/schema/${t.name}`);
    if (!schema) continue;
    const block = document.createElement("div");
    block.className = "schema-table-block";
    block.innerHTML = `
      <div class="schema-table-name">
        <span class="material-symbols-rounded">table_rows</span>${t.name}
      </div>
      ${schema.map(col => `
        <div class="schema-col-row">
          <span class="schema-col-name">${col.Field}</span>
          <span class="schema-col-type">${col.Type}</span>
          <span class="schema-col-extra">${col.Extra || ""} ${col.Null === "NO" ? "NOT NULL" : ""}</span>
          ${col.Key === "PRI" ? `<span class="schema-pk">PK</span>` : ""}
          ${col.Key === "MUL" ? `<span class="schema-fk">FK</span>` : ""}
        </div>`).join("")}`;
    schemaView.appendChild(block);
  }
}

async function runDbQuery() {
  const sql = $("dbQueryInput").value.trim();
  if (!sql) return;
  const data = await api("/api/db/query", {
    method: "POST",
    body: JSON.stringify({ sql })
  });
  if (!data) return;
  if (data.error) {
    $("dbResultsWrap").innerHTML = `<div class="db-empty" style="color:#e13535"><span class="material-symbols-rounded">error</span>${data.error}</div>`;
    $("dbRowCount").textContent = "Erro";
    return;
  }
  const rows = data.rows;
  $("dbRowCount").textContent = `${rows.length} linha${rows.length !== 1 ? "s" : ""}`;
  if (!rows.length) {
    $("dbResultsWrap").innerHTML = `<div class="db-empty"><span class="material-symbols-rounded">table_view</span>Nenhum resultado.</div>`;
    return;
  }
  const cols = Object.keys(rows[0]);
  const table = document.createElement("table");
  table.className = "db-table";
  table.innerHTML = `
    <thead><tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => `<tr>${cols.map(c => {
      const val = r[c];
      if (val === null || val === "None") return `<td><span class="db-null">NULL</span></td>`;
      if (typeof val === "number" || /^\d+$/.test(val)) return `<td class="db-type-int">${val}</td>`;
      if (val === "1" || val === "true") return `<td class="db-type-bool-true">TRUE</td>`;
      if (val === "0" || val === "false") return `<td class="db-type-bool-false">FALSE</td>`;
      if (String(val).startsWith("http")) return `<td class="db-type-url">${val}</td>`;
      return `<td class="db-type-str">${val}</td>`;
    }).join("")}</tr>`).join("")}</tbody>`;
  $("dbResultsWrap").innerHTML = "";
  $("dbResultsWrap").appendChild(table);
}

// ─── UPLOAD ───────────────────────────────────────────────────────────────────
async function handleUpload() {
  const title = $("uploadTitle").value.trim();
  const url = $("uploadUrl").value.trim();
  const thumb = $("uploadThumb").value.trim();
  const channel = $("uploadChannel").value.trim();
  const category = $("uploadCategory").value;
  if (!title || !url || !channel) { showToast("⚠️ Preencha título, URL e canal."); return; }

  const data = await api("/api/videos/upload", {
    method: "POST",
    body: JSON.stringify({ title, url, thumbnail: thumb, channel, category })
  });

  if (data && data.id) {
    $("uploadModal").classList.remove("active");
    document.body.style.overflow = "";
    [$("uploadTitle"), $("uploadUrl"), $("uploadThumb"), $("uploadChannel")].forEach(el => el.value = "");
    showToast(`✅ Vídeo "${data.title}" publicado!`);
    loadHome(State.currentFilter);
  } else {
    showToast("❌ Erro ao publicar: " + (data?.error || "tente novamente"));
  }
}

// ─── INIT ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Load initial data
  await loadHome("all");
  await initFilterChips();
  await loadSidebarChannels();

  // Sidebar nav
  $$(".nav-item[data-section]").forEach(item => {
    item.addEventListener("click", e => {
      e.preventDefault();
      const section = item.dataset.section;
      const channel = item.dataset.channel || null;
      navigateTo(section, channel);
    });
  });

  $("menuToggle").addEventListener("click", toggleSidebar);

  // Search
  $("searchInput").addEventListener("input", e => {
    clearTimeout(State.searchDebounce);
    State.searchDebounce = setTimeout(() => handleSearch(e.target.value), 280);
  });
  $("searchInput").addEventListener("keydown", e => {
    if (e.key === "Enter") handleSearch(e.target.value);
  });
  document.addEventListener("click", e => {
    if (!e.target.closest(".header-center")) $("searchResults").classList.add("hidden");
  });
  $("searchBtn").addEventListener("click", () => handleSearch($("searchInput").value));

  // Video modal
  $("modalClose").addEventListener("click", () => {
    $("videoModal").classList.remove("active");
    $("videoFrame").src = "";
    document.body.style.overflow = "";
  });
  $("videoModal").addEventListener("click", e => {
    if (e.target === $("videoModal")) {
      $("videoModal").classList.remove("active");
      $("videoFrame").src = "";
      document.body.style.overflow = "";
    }
  });

  // Like
  $("likeBtn").addEventListener("click", async () => {
    if (!State.currentVideoId) return;
    const data = await api(`/api/videos/${State.currentVideoId}/like`, { method: "POST" });
    if (!data) return;
    $("likeCount").textContent = formatViews(data.likes);
    $("likeBtn").classList.toggle("liked", data.liked);
    showToast(data.liked ? "❤️ Você curtiu este vídeo!" : "💔 Curtida removida");
  });

  // Upload modal
  $("uploadBtn").addEventListener("click", () => {
    $("uploadModal").classList.add("active");
    document.body.style.overflow = "hidden";
  });
  $("uploadClose").addEventListener("click", () => {
    $("uploadModal").classList.remove("active");
    document.body.style.overflow = "";
  });
  $("uploadSubmit").addEventListener("click", handleUpload);
  $("uploadModal").addEventListener("click", e => {
    if (e.target === $("uploadModal")) {
      $("uploadModal").classList.remove("active");
      document.body.style.overflow = "";
    }
  });

  // New Playlist modal
  $("newPlaylistBtn").addEventListener("click", () => {
    $("newPlaylistModal").classList.add("active");
    document.body.style.overflow = "hidden";
  });
  $("newPlaylistClose").addEventListener("click", () => {
    $("newPlaylistModal").classList.remove("active");
    document.body.style.overflow = "";
  });
  $("newPlaylistModal").addEventListener("click", e => {
    if (e.target === $("newPlaylistModal")) {
      $("newPlaylistModal").classList.remove("active");
      document.body.style.overflow = "";
    }
  });
  $("playlistSubmit").addEventListener("click", async () => {
    const name = $("playlistName").value.trim();
    if (!name) { showToast("⚠️ Dê um nome à playlist."); return; }
    const data = await api("/api/playlists", {
      method: "POST",
      body: JSON.stringify({
        name,
        description: $("playlistDesc").value.trim(),
        isPublic: $("playlistVisibility").value === "public"
      })
    });
    if (data && data.id) {
      $("newPlaylistModal").classList.remove("active");
      document.body.style.overflow = "";
      $("playlistName").value = "";
      $("playlistDesc").value = "";
      showToast(`✅ Playlist "${data.name}" criada!`);
      loadPlaylists();
    }
  });

  // DB buttons
  $("dbRunBtn").addEventListener("click", () => runDbQuery());
  $("dbClearBtn").addEventListener("click", () => {
    $("dbQueryInput").value = "";
    $("dbResultsWrap").innerHTML = `<div class="db-empty"><span class="material-symbols-rounded">table_view</span>Execute uma query para ver os resultados</div>`;
    $("dbRowCount").textContent = "—";
  });
  $("dbQueryInput").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); runDbQuery(); }
  });

  // Avatar
  $("avatarBtn").addEventListener("click", async () => {
    const s = await api("/api/stats");
    if (s) showToast(`👤 ViewTube User • ${s.totalVideos} vídeos`);
  });

  // Keyboard shortcuts
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      [$("videoModal"), $("uploadModal"), $("newPlaylistModal")].forEach(m => m.classList.remove("active"));
      $("videoFrame").src = "";
      document.body.style.overflow = "";
      $("searchResults").classList.add("hidden");
    }
    if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
      e.preventDefault();
      $("searchInput").focus();
    }
  });

  // Scroll effect on header
  window.addEventListener("scroll", () => {
    $("header").style.borderBottomColor = window.scrollY > 10
      ? "rgba(225,53,53,0.3)"
      : "var(--border)";
  }, { passive: true });

  setTimeout(() => showToast("👋 Bem-vindo ao ViewTube!"), 800);

  // expose globally for inline onclick usage
  window.openVideo = openVideo;
  window.toggleSubscribe = toggleSubscribe;
});
