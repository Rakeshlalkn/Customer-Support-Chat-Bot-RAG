// talks to the FastAPI backend at /api/* (proxied by nginx)
const API = "";

const $ = (s) => document.querySelector(s);
const messages = $("#messages");
const input = $("#input");
const composer = $("#composer");
const sendBtn = $("#send-btn");

async function refreshStats() {
  try {
    const r = await fetch(`${API}/api/stats`);
    if (!r.ok) throw new Error(r.status);
    const d = await r.json();
    $("#kb-count").textContent = `${d.total_chunks} chunks`;
    $("#kb-provider").textContent = `provider: ${d.provider}`;
    $("#kb-model").textContent = `model: ${d.embedding_model}`;
    setStatus(d.total_chunks > 0 ? "ready" : "kb empty - load samples or upload");
  } catch (e) {
    setStatus("backend offline", true);
  }
}

function setStatus(text, isErr = false) {
  const el = $("#status-pill");
  el.textContent = text;
  el.classList.remove("ok", "err");
  el.classList.add(isErr ? "err" : "ok");
}

function escapeHtml(s = "") {
  return s.replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;",
  }[c]));
}

function addMessage(role, html, sources = []) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  wrap.innerHTML = `
    <div class="avatar">${role === "user" ? "you" : "ai"}</div>
    <div class="bubble">
      <div class="content">${html}</div>
      ${sources.length ? renderSources(sources) : ""}
    </div>
  `;
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

function renderSources(sources) {
  const chips = sources
    .map((s, i) => `<span class="source-chip" data-i="${i}">${escapeHtml(s.source)}</span>`)
    .join("");
  const details = sources
    .map((s, i) => `<div class="source-detail" data-i="${i}">${escapeHtml(s.content)}</div>`)
    .join("");
  return `<div class="sources">${chips}</div>${details}`;
}

// click a chip to expand the source chunk
messages.addEventListener("click", (e) => {
  const chip = e.target.closest(".source-chip");
  if (!chip) return;
  const i = chip.dataset.i;
  const detail = chip.parentElement.parentElement.querySelector(`.source-detail[data-i="${i}"]`);
  if (detail) detail.classList.toggle("open");
});

function addTyping() {
  return addMessage("bot", `<div class="typing"><span></span><span></span><span></span></div>`, []);
}

async function sendQuestion(q) {
  addMessage("user", escapeHtml(q));
  const typing = addTyping();
  sendBtn.disabled = true;
  try {
    const r = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });
    typing.remove();
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      addMessage("bot", `error: ${escapeHtml(err.detail || "request failed")}`);
      return;
    }
    const d = await r.json();
    addMessage("bot", escapeHtml(d.answer), d.sources || []);
  } catch (e) {
    typing.remove();
    addMessage("bot", `network error: ${escapeHtml(String(e))}`);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  input.style.height = "auto";
  sendQuestion(q);
});

// auto-grow the textarea as you type
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 180) + "px";
});
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    composer.requestSubmit();
  }
});

$("#btn-clear").addEventListener("click", () => {
  messages.innerHTML = "";
  addMessage("bot", "Chat cleared. What can I help with?");
});

$("#file-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  setStatus(`uploading ${file.name}…`);
  const fd = new FormData();
  fd.append("file", file);
  try {
    const r = await fetch(`${API}/api/ingest/file`, { method: "POST", body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "upload failed");
    setStatus(`added ${d.added_chunks} chunks from ${d.source}`);
    refreshStats();
  } catch (err) {
    setStatus(`upload failed: ${err.message}`, true);
  } finally {
    e.target.value = "";
  }
});

$("#btn-seed").addEventListener("click", async () => {
  setStatus("seeding sample kb…");
  try {
    const r = await fetch(`${API}/api/admin/seed`, { method: "POST" });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "seed failed");
    setStatus(`seeded ${d.added_chunks} chunks`);
    refreshStats();
  } catch (err) {
    setStatus(`seed failed: ${err.message}`, true);
  }
});

$("#btn-reset").addEventListener("click", async () => {
  if (!confirm("Wipe the knowledge base? can't undo this.")) return;
  setStatus("resetting…");
  try {
    await fetch(`${API}/api/admin/reset`, { method: "POST" });
    setStatus("kb cleared");
    refreshStats();
  } catch (err) {
    setStatus(`reset failed: ${err.message}`, true);
  }
});

// boot
(async () => {
  setStatus("connecting…");
  await refreshStats();
  // keep stats fresh in case other clients add stuff
  setInterval(refreshStats, 15000);
})();
