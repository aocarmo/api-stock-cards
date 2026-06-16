"use strict";

async function api(method, url, body) {
  const opt = { method, headers: {} };
  if (body !== undefined) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
  const r = await fetch(url, opt);
  let data = null;
  try { data = await r.json(); } catch (e) {}
  if (!r.ok) throw { status: r.status, data };
  return data;
}

function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const k in attrs) {
    if (k === "class") e.className = attrs[k];
    else if (k === "html") e.innerHTML = attrs[k];
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), attrs[k]);
    else e.setAttribute(k, attrs[k]);
  }
  kids.forEach((c) => e.append(c));
  return e;
}

// Paginador client-side reutilizável.
// renderItems(slice, startIndex) desenha a página; controlsEl recebe os controles.
function makePaginator(controlsEl, renderItems, perPage) {
  let page = 1, items = [], pp = perPage || 50;
  const pages = () => Math.max(1, Math.ceil(items.length / pp));
  function draw() {
    page = Math.min(Math.max(1, page), pages());
    const start = (page - 1) * pp;
    renderItems(items.slice(start, start + pp), start);
    controls();
  }
  function controls() {
    controlsEl.innerHTML = "";
    if (!items.length) return;
    const prev = el("button", { class: "secondary outline", onclick: () => { page--; draw(); } }, "‹ anterior");
    const next = el("button", { class: "secondary outline", onclick: () => { page++; draw(); } }, "próxima ›");
    prev.disabled = page <= 1; next.disabled = page >= pages();
    const info = el("span", { class: "muted" }, `Página ${page}/${pages()} · ${items.length} itens`);
    const sel = el("select", { onchange: (e) => { pp = parseInt(e.target.value); page = 1; draw(); } });
    [25, 50, 100, 200].forEach((n) => { const o = el("option", { value: String(n) }, n + "/pág"); if (n === pp) o.selected = true; sel.append(o); });
    controlsEl.append(prev, next, info, sel);
  }
  return {
    set(newItems) { items = newItems || []; page = 1; draw(); },   // nova busca → volta à pág 1
    update(newItems) { items = newItems || []; draw(); },          // mutação → mantém a página
    items: () => items,
  };
}

// ---- health (todas as telas) ----
async function checkHealth() {
  const h = document.getElementById("health");
  if (!h) return;
  try { await api("GET", "/api/health"); h.className = "health ok"; h.title = "API remota OK"; }
  catch { h.className = "health bad"; h.title = "API remota indisponível"; }
}

// ===================== MANAGE (cadastrar/alterar/excluir) =====================
function initManage() {
  const cfgEl = document.getElementById("page-cfg");
  if (!cfgEl) return false;
  const CFG = JSON.parse(cfgEl.textContent);
  const list = [];
  const body = document.getElementById("list-body");
  const count = document.getElementById("count");
  const form = document.getElementById("card-form");
  const pager = makePaginator(document.getElementById("list-pager"), renderSlice, 50);

  function renderSlice(slice, start) {
    body.innerHTML = "";
    count.textContent = list.length;
    slice.forEach((c, i) => {
      const gi = start + i;
      const cells = [c.numero, c.colecao, c.tipo, c.idioma];
      if (CFG.needsPrice) cells.push(c.preco, c.quantidade);
      const tr = el("tr", {}, ...cells.map((v) => el("td", {}, document.createTextNode(v ?? ""))));
      tr.append(el("td", {}, el("a", { href: "#", onclick: (e) => { e.preventDefault(); list.splice(gi, 1); pager.update(list); } }, "remover")));
      body.append(tr);
    });
  }
  const refresh = () => pager.update(list);

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const f = new FormData(form);
    const c = { numero: f.get("numero").trim(), colecao: f.get("colecao").trim(), tipo: f.get("tipo"), idioma: f.get("idioma") };
    if (CFG.needsPrice) { c.preco = (f.get("preco") || "").trim(); c.quantidade = (f.get("quantidade") || "").trim(); }
    list.push(c); refresh();
    form.reset();
    form.querySelector("[name=numero]").focus();
  });

  const qs = new URLSearchParams(location.search);
  if (qs.get("numero")) {
    for (const k of ["numero", "colecao", "tipo", "idioma", "preco", "quantidade"]) {
      const inp = form.querySelector(`[name=${k}]`);
      if (inp && qs.get(k)) inp.value = qs.get(k);
    }
  }

  document.getElementById("bulk-validate").addEventListener("click", async () => {
    const text = document.getElementById("bulk-text").value;
    const box = document.getElementById("bulk-errors");
    box.innerHTML = "";
    if (!text.trim()) return;
    try {
      const res = await api("POST", "/api/parse", { text, operation: CFG.operation });
      res.valid.forEach((c) => list.push(c));
      refresh();
      document.getElementById("bulk-text").value = "";
      if (res.invalid.length) {
        box.append(el("p", { class: "muted" }, `${res.invalid.length} linha(s) inválida(s):`));
        res.invalid.forEach((iv) => box.append(el("small", { class: "b-err badge" }, `L${iv.linha}: ${iv.erro}`), document.createTextNode(" ")));
      }
    } catch (err) { box.textContent = "Erro ao validar: " + JSON.stringify(err.data || err); }
  });

  document.getElementById("clear-btn").addEventListener("click", () => { list.length = 0; refresh(); });

  document.getElementById("send-btn").addEventListener("click", async () => {
    const msg = document.getElementById("send-msg");
    if (!list.length) { msg.textContent = "Lista vazia."; return; }
    msg.textContent = "Enviando…";
    try {
      // Tudo via job (pipeline em massa, confiável). O caminho síncrono de 1 carta
      // depende do endpoint /atualizar do backend, que tem bug de serialização.
      const res = await api("POST", `/api/jobs/${CFG.action}`, { cartas: list });
      msg.textContent = `Job ${res.job_id} criado (${res.total} carta(s)). Redirecionando…`;
      setTimeout(() => (location.href = "/progresso"), 800);
    } catch (err) {
      const d = err.data && err.data.detail;
      if (d && d.invalid) msg.textContent = `Linhas inválidas: ` + d.invalid.map((x) => `L${x.linha}(${x.erro})`).join("; ");
      else msg.textContent = "Erro: " + JSON.stringify(d || err);
    }
  });

  refresh();
  return true;
}

// ===================== INVENTÁRIO =====================
function initInventario() {
  const wrap = document.getElementById("inv-wrap");
  if (!wrap) return false;
  const pager = makePaginator(document.getElementById("inv-pager"), renderTable, 50);

  function renderTable(slice) {
    const tbody = el("tbody");
    slice.forEach((c) => {
      const tr = el("tr", { class: "row-link", onclick: () => {
        const q = new URLSearchParams({ numero: c.numero, colecao: c.colecao, tipo: c.tipo, idioma: c.idioma, preco: c.preco ?? "", quantidade: c.quantidade ?? "" });
        location.href = "/alterar?" + q.toString();
      } },
        el("td", {}, document.createTextNode(c.numero)),
        el("td", {}, document.createTextNode(c.colecao)),
        el("td", {}, document.createTextNode(c.tipo)),
        el("td", {}, document.createTextNode(c.idioma)),
        el("td", {}, document.createTextNode(c.preco ?? "")),
        el("td", {}, document.createTextNode(c.quantidade ?? "")));
      tbody.append(tr);
    });
    wrap.innerHTML = "";
    wrap.append(el("table", {}, el("thead", { html: "<tr><th>Número</th><th>Coleção</th><th>Tipo</th><th>Idioma</th><th>Preço</th><th>Qtd</th></tr>" }), tbody));
  }

  api("GET", "/api/inventory/summary").then((s) => {
    document.getElementById("summary").innerHTML = `<strong>${s.total_cards ?? "?"}</strong> cartas no total · atualizado ${s.updated_at || "?"}`;
  }).catch(() => { document.getElementById("summary").innerHTML = "<small class='muted'>Sem inventário sincronizado ainda.</small>"; });

  function filterParams() {
    const f = new FormData(document.getElementById("filtros"));
    const p = new URLSearchParams();
    for (const [k, v] of f.entries()) if (v.trim()) p.set(k, v.trim());
    return p;
  }

  document.getElementById("buscar").addEventListener("click", async () => {
    const msg = document.getElementById("inv-msg");
    msg.textContent = "Buscando…";
    document.getElementById("export").href = "/api/inventory/export?" + filterParams().toString();
    try {
      const res = await api("GET", "/api/inventory?" + filterParams().toString());
      const cards = res.cards || res.items || [];
      msg.textContent = `${cards.length} carta(s).`;
      pager.set(cards);
    } catch (err) {
      wrap.innerHTML = ""; document.getElementById("inv-pager").innerHTML = "";
      const d = (err.data && err.data.detail) || err;
      msg.textContent = "Erro: " + (typeof d === "string" ? d : JSON.stringify(d));
    }
  });

  document.getElementById("sync-btn").addEventListener("click", async () => {
    const prog = document.getElementById("sync-prog"), sm = document.getElementById("sync-msg");
    sm.textContent = "Iniciando scrape…"; prog.style.display = "inline-block"; prog.removeAttribute("value");
    try {
      const r = await api("POST", "/api/inventory/sync");
      const jobId = r.job_id;
      const timer = setInterval(async () => {
        try {
          const st = await api("GET", "/api/inventory/sync/" + jobId);
          prog.value = st.progress_percent || 0;
          sm.textContent = `${st.status} · ${st.progress_percent || 0}% (${st.total_cards ?? "?"} cartas)`;
          if (st.status === "COMPLETED" || st.status === "FAILED") clearInterval(timer);
        } catch (e) { clearInterval(timer); sm.textContent = "Erro ao consultar sync."; }
      }, 3000);
    } catch (err) { sm.textContent = "Erro: " + JSON.stringify(err.data || err); }
  });
  return true;
}

// ===================== PROGRESSO =====================
function jobBadge(status) {
  const map = { COMPLETED: "b-ok", COMPLETED_WITH_ERRORS: "b-err", FAILED: "b-err",
    RUNNING: "b-run", RETRYING: "b-run", WAITING: "b-wait", PENDING: "b-wait", CANCELLED: "b-done" };
  return el("span", { class: "badge " + (map[status] || "b-done") }, status);
}

function initProgresso() {
  const root = document.getElementById("jobs");
  if (!root) return false;
  const open = new Set();

  async function tick() {
    let data;
    try { data = await api("GET", "/api/jobs"); } catch { return; }
    root.innerHTML = "";
    if (!data.jobs.length) { root.append(el("p", { class: "muted" }, "Nenhum job ainda.")); return; }
    for (const j of data.jobs) {
      const pct = j.total_batches ? Math.round((j.current_batch / j.total_batches) * 100) : 0;
      const card = el("div", { class: "job" });
      card.append(el("div", {}, el("strong", {}, j.id + " "), jobBadge(j.status), el("span", { class: "muted" }, ` · ${j.operation} · ${j.mensagem || ""}`)));
      card.append(el("progress", { value: String(pct), max: "100" }));
      card.append(el("div", { class: "muted" },
        `lote ${j.current_batch}/${j.total_batches} · rodada ${j.round} · `,
        el("span", { class: "badge b-ok" }, `${j.total_sucesso} ok`), document.createTextNode(" "),
        el("span", { class: "badge b-err" }, `${j.total_erro} erro`), document.createTextNode(` · ${j.total_linhas} total`)));
      const actions = el("div", {});
      const active = ["RUNNING", "WAITING", "RETRYING", "PENDING"].includes(j.status);
      if (active) actions.append(el("a", { href: "#", onclick: async (e) => { e.preventDefault(); await api("POST", `/api/jobs/${j.id}/cancel`); } }, "cancelar"), document.createTextNode("  "));
      if (j.total_erro > 0 && !active) actions.append(el("a", { href: "#", onclick: async (e) => { e.preventDefault(); await api("POST", `/api/jobs/${j.id}/retry`); } }, "retry falhas"), document.createTextNode("  "));
      if (j.total_erro > 0) actions.append(el("a", { href: "#", onclick: async (e) => { e.preventDefault(); open.has(j.id) ? open.delete(j.id) : open.add(j.id); await showErrors(j.id, card); } }, open.has(j.id) ? "ocultar falhas" : "ver falhas"));
      card.append(actions);
      if (open.has(j.id)) await showErrors(j.id, card);
      root.append(card);
    }
  }

  async function showErrors(jobId, card) {
    if (card.querySelector(".err-list")) card.querySelector(".err-list").remove();
    if (!open.has(jobId)) return;
    try {
      const d = await api("GET", "/api/jobs/" + jobId);
      const box = el("div", { class: "err-list" });
      (d.erros || []).forEach((e) => box.append(el("div", {}, `${e.numero} ${e.tipo} ${e.idioma} — ${e.status}`)));
      card.append(box);
    } catch {}
  }

  tick();
  setInterval(tick, 3000);
  return true;
}

document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  initManage() || initInventario() || initProgresso();
});
