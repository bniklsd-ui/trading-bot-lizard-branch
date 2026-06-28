/* Scheduler dashboard — vanilla polling client (no framework, no build step).
   Reads the read-only API every 7s and renders; control buttons POST the kill/command files.
   Fail-soft: a fetch error flips the footer to "down" and keeps the last good values. */

"use strict";

const POLL_MS = 7000;
const $ = (id) => document.getElementById(id);

async function getJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

async function postJSON(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `${path} -> ${res.status}`);
  return data;
}

// ---- formatting helpers ----
const fmtNum = (v, dp = 1) =>
  v === null || v === undefined || v === "" || Number.isNaN(Number(v))
    ? "–"
    : Number(v).toFixed(dp);

function fmtSigned(v) {
  if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "–";
  const n = Number(v);
  return (n >= 0 ? "+" : "") + n.toFixed(2);
}

function fmtTs(ts) {
  if (!ts) return "–";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return String(ts);
  return d.toLocaleString([], {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

function shortEpic(e) {
  if (!e) return "–";
  const parts = String(e).split(".");
  return parts.length > 2 ? parts.slice(1, 3).join(".") : e;
}

// ---- renderers ----
function renderStatus(s) {
  const map = { RUNNING: "running", PAUSED: "paused", HALTED: "halted" };
  const cls = map[s.running_state] || "unknown";
  const pill = $("state-pill");
  pill.className = `pill pill--${cls}`;
  $("state-label").textContent = s.running_state || "—";

  $("phase-tag").textContent = s.phase || "—";
  $("trades-today").textContent = s.trades_today ?? "–";
  $("trades-cap").textContent = s.max_trades_per_day ?? "–";
  $("fails").textContent = s.consecutive_failures ?? "–";
  $("fails-max").textContent = s.max_consecutive_failures ?? "–";
  $("session-date").textContent = s.session_date || "–";

  const pnl = $("pnl-today");
  pnl.textContent = fmtSigned(s.realized_pnl_today);
  pnl.classList.toggle("pos", Number(s.realized_pnl_today) > 0);
  pnl.classList.toggle("neg", Number(s.realized_pnl_today) < 0);

  const banner = $("kill-banner");
  if (s.running_state === "HALTED") {
    banner.hidden = false;
    $("kill-reason").textContent = s.kill_reason || "(no reason)";
  } else {
    banner.hidden = true;
  }
}

function renderCycle(c) {
  $("cycle-reason").textContent = c.last_no_trade_reason || "—";
  $("cycle-research").textContent = fmtTs(c.last_research_ts);
  $("cycle-reconcile").textContent = fmtTs(c.last_reconcile_ts);
}

function renderConfidence(c) {
  const tag = $("conf-state");
  const state = c.state || "—";
  tag.textContent = state;
  tag.className = "tag " + ({ OK: "is-ok", INSUFFICIENT: "is-insufficient" }[state] || "is-unavailable");
  $("conf-n").textContent = `${c.n ?? "–"} / ${c.n_min ?? "–"}`;
  $("conf-val").textContent = c.confidence_value === null || c.confidence_value === undefined ? "–" : fmtNum(c.confidence_value, 1);
  $("conf-wilson").textContent = fmtNum(c.win_rate_wilson_lb, 3);
  $("conf-exp").textContent = fmtNum(c.expectancy_r, 2);
  $("conf-wr").textContent = c.win_rate_raw === null || c.win_rate_raw === undefined ? "–" : (Number(c.win_rate_raw) * 100).toFixed(0) + "%";
  $("conf-sqn").textContent = fmtNum(c.sqn, 2);
}

function renderScore(rows) {
  const svg = $("spark");
  const empty = $("spark-empty");
  const pts = rows.map((r) => Number(r.score_after)).filter((v) => !Number.isNaN(v));
  $("score-now").textContent = pts.length ? fmtNum(pts[pts.length - 1], 1) : "—";

  if (pts.length < 2) {
    svg.innerHTML = "";
    empty.style.display = "";
    return;
  }
  empty.style.display = "none";

  const W = 600, H = 140, pad = 8;
  const min = Math.min(...pts), max = Math.max(...pts);
  const span = max - min || 1;
  const x = (i) => pad + (i / (pts.length - 1)) * (W - 2 * pad);
  const y = (v) => H - pad - ((v - min) / span) * (H - 2 * pad);

  const line = pts.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L${x(pts.length - 1).toFixed(1)},${H} L${x(0).toFixed(1)},${H} Z`;
  const lastX = x(pts.length - 1).toFixed(1), lastY = y(pts[pts.length - 1]).toFixed(1);

  svg.innerHTML = `
    <defs>
      <linearGradient id="spark-grad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#3fb950" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#3fb950" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path class="spark-area" d="${area}"/>
    <path class="spark-line" d="${line}"/>
    <circle class="spark-dot" cx="${lastX}" cy="${lastY}" r="3.5"/>`;
}

function renderTrades(rows) {
  $("trades-count").textContent = rows.length;
  const body = $("trades-body");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="8" class="empty">no trades yet</td></tr>`;
    return;
  }
  body.innerHTML = rows
    .map((t) => {
      const dir = (t.direction || "").toUpperCase();
      const dirCls = dir === "BUY" ? "dir-buy" : dir === "SELL" ? "dir-sell" : "";
      const pl = t.profit_loss;
      const plCls = pl > 0 ? "pos" : pl < 0 ? "neg" : "";
      const stCls = "st--" + String(t.status || "").toLowerCase();
      return `<tr>
        <td>${fmtTs(t.open_ts)}</td>
        <td class="${dirCls}">${dir || "–"}</td>
        <td title="${t.epic || ""}">${shortEpic(t.epic)}</td>
        <td class="num">${fmtNum(t.size, 2)}</td>
        <td class="num">${fmtNum(t.open_level, 1)}</td>
        <td class="num">${t.close_level == null ? "–" : fmtNum(t.close_level, 1)}</td>
        <td class="num ${plCls}">${pl == null ? "–" : fmtSigned(pl)}</td>
        <td><span class="st ${stCls}">${t.status || "–"}</span></td>
      </tr>`;
    })
    .join("");
}

function renderLessons(rows) {
  $("lessons-count").textContent = rows.length;
  const list = $("lessons-list");
  if (!rows.length) {
    list.innerHTML = `<li class="empty">no lessons yet</li>`;
    return;
  }
  list.innerHTML = rows
    .map(
      (l) => `<li>
        <span class="lesson-ts">${fmtTs(l.extracted_at)}</span>
        <span class="lesson-text">${escapeHtml(l.lesson_text || "")}</span>
      </li>`
    )
    .join("");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function setConn(ok) {
  const c = $("conn-state");
  c.className = "conn " + (ok ? "conn--ok" : "conn--down");
  c.textContent = ok ? "api" : "api down";
}

// ---- poll loop ----
async function refresh() {
  try {
    const [status, cycle, conf, score, trades, lessons] = await Promise.all([
      getJSON("/api/status"),
      getJSON("/api/last_cycle"),
      getJSON("/api/confidence"),
      getJSON("/api/score"),
      getJSON("/api/trades"),
      getJSON("/api/lessons"),
    ]);
    renderStatus(status);
    renderCycle(cycle);
    renderConfidence(conf);
    renderScore(score);
    renderTrades(trades);
    renderLessons(lessons);
    $("updated-at").textContent = new Date().toLocaleTimeString();
    setConn(true);
  } catch (err) {
    setConn(false);
  }
}

// ---- controls ----
function flash(msg, isErr) {
  const el = $("control-msg");
  el.textContent = msg;
  el.style.color = isErr ? "var(--red)" : "var(--cyan)";
}

async function control(action) {
  try {
    if (action === "start") { await postJSON("/api/command", { cmd: "start" }); flash("resume requested — start"); }
    else if (action === "stop") { await postJSON("/api/command", { cmd: "stop" }); flash("pause requested — stop"); }
    else if (action === "kill") {
      if (!confirm("Engage the KILL switch? The daemon stops at the next cycle.")) return;
      await postJSON("/api/kill", { reason: "dashboard" }); flash("KILL engaged");
    } else if (action === "clear") { await postJSON("/api/clear_kill", {}); flash("KILL cleared"); }
    refresh();
  } catch (err) {
    flash(String(err.message || err), true);
  }
}

$("btn-start").addEventListener("click", () => control("start"));
$("btn-stop").addEventListener("click", () => control("stop"));
$("btn-kill").addEventListener("click", () => control("kill"));
$("btn-clear").addEventListener("click", () => control("clear"));

refresh();
setInterval(refresh, POLL_MS);
