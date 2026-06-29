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

// ---- motion infrastructure (all fail-soft; honors prefers-reduced-motion) ----
const REDUCED = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
const _odo = {};        // id -> Odometer instance
const _odoLast = {};    // id -> last numeric value

function flashTick(el) {
  if (REDUCED || !el) return;
  el.classList.remove("flash-tick");
  void el.offsetWidth; // restart the animation
  el.classList.add("flash-tick");
}

// route a headline number through the vendored odometer (rolling digits), with a
// glow flash on change. Falls back to plain text if Odometer didn't load. Never throws.
function setNum(id, value, dp) {
  const el = $(id);
  if (!el) return;
  dp = dp || 0;
  const finite = value !== null && value !== undefined && value !== "" && !Number.isNaN(Number(value));
  if (!finite) {
    el.textContent = "–";
    el.dataset.odoBroken = "1";
    _odoLast[id] = undefined;
    return;
  }
  const n = Number(value);
  const changed = _odoLast[id] !== undefined && _odoLast[id] !== n;
  try {
    if (window.Odometer) {
      const fmt = dp > 0 ? "(,ddd)." + "d".repeat(dp) : "(,ddd)";
      if (!_odo[id] || el.dataset.odoBroken) {
        el.textContent = "";
        _odo[id] = new window.Odometer({ el, value: n, format: fmt, theme: "minimal", duration: 900 });
        delete el.dataset.odoBroken;
      } else {
        _odo[id].update(n);
      }
    } else {
      el.textContent = n.toLocaleString([], { minimumFractionDigits: dp, maximumFractionDigits: dp });
    }
  } catch (_e) {
    el.textContent = n.toFixed(dp); // last-resort, UI never breaks
  }
  if (changed) flashTick(el);
  _odoLast[id] = n;
}

// P&L can be negative and odometer 0.4.8 drops the minus sign (a loss would read as a gain),
// so signed values get a custom count-up tween that keeps the +/- via fmtSigned. Fail-soft.
function tweenSigned(id, to) {
  const el = $(id);
  if (!el) return;
  const finite = to !== null && to !== undefined && to !== "" && !Number.isNaN(Number(to));
  if (!finite) { el.textContent = "–"; _odoLast[id] = undefined; return; }
  const target = Number(to);
  const prev = _odoLast[id];
  const changed = prev !== undefined && prev !== target;
  if (REDUCED || prev === undefined || !changed) {
    el.textContent = fmtSigned(target);
  } else {
    const from = prev, dur = 700, t0 = performance.now();
    (function step(now) {
      const k = Math.min(1, (now - t0) / dur);
      el.textContent = fmtSigned(from + (target - from) * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }
  if (changed) flashTick(el);
  _odoLast[id] = target;
}

// only rebuild a heavy section's DOM when its payload actually changed — saves work and,
// crucially, stops the 7s poll from collapsing any debate <details> the user opened.
const _lastJSON = {};
function renderIfChanged(key, data, fn) {
  const s = JSON.stringify(data);
  if (_lastJSON[key] === s) return false;
  _lastJSON[key] = s;
  fn(data);
  return true;
}

// ---- renderers ----
function renderStatus(s) {
  const map = { RUNNING: "running", PAUSED: "paused", HALTED: "halted" };
  const cls = map[s.running_state] || "unknown";
  const pill = $("state-pill");
  pill.className = `pill pill--${cls}`;
  $("state-label").textContent = s.running_state || "—";

  $("phase-tag").textContent = s.phase || "—";
  setNum("trades-today", s.trades_today, 0);
  $("trades-cap").textContent = s.max_trades_per_day ?? "–";
  $("fails").textContent = s.consecutive_failures ?? "–";
  $("fails-max").textContent = s.max_consecutive_failures ?? "–";
  $("session-date").textContent = s.session_date || "–";

  const pnl = $("pnl-today");
  tweenSigned("pnl-today", s.realized_pnl_today);
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

// local calendar date (YYYY-MM-DD) of an ISO ts, in the browser's tz (Berlin for the operator)
function localDay(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  return Number.isNaN(d.getTime()) ? null : d.toLocaleDateString("en-CA");
}

// "from an earlier cycle" marker when the artifact pre-dates today's session
function markStale(elId, ts, sessionDate) {
  const el = $(elId);
  const day = localDay(ts);
  if (ts && sessionDate && day && day !== sessionDate) {
    el.textContent = `from an earlier cycle · ${fmtTs(ts)}`;
    el.hidden = false;
  } else if (ts) {
    el.textContent = fmtTs(ts);
    el.hidden = false;
  } else {
    el.hidden = true;
  }
}

function dirBadge(dir) {
  const d = String(dir || "").toUpperCase();
  const cls = d === "BUY" ? "dir-buy" : d === "SELL" ? "dir-sell" : "";
  return `<span class="${cls}">${d || "–"}</span>`;
}

function renderCycle(c) {
  $("cycle-reason").textContent = c.last_no_trade_reason || "—";
  $("cycle-research").textContent = fmtTs(c.last_research_ts);
  $("cycle-reconcile").textContent = fmtTs(c.last_reconcile_ts);

  // --- research pick ---
  const p = c.research_pick;
  const pickEl = $("cycle-pick");
  if (p && (p.reasoning || p.direction)) {
    pickEl.innerHTML = `
      <div class="reason-meta">
        ${dirBadge(p.direction)}
        <span class="reason-epic" title="${escapeHtml(p.epic || "")}">${shortEpic(p.epic)}</span>
        <span class="reason-num">conf ${fmtNum(p.llm_confidence, 0)}</span>
        <span class="reason-num">floor ${fmtNum(p.threshold_applied, 0)}</span>
        <span class="reason-num">score ${fmtNum(p.score_at_pick, 0)}</span>
      </div>
      <p class="reason-block">${escapeHtml(p.reasoning || "")}</p>`;
    markStale("pick-stale", p.generated_at, c.session_date);
  } else if (c.last_no_trade_detail) {
    // No pick this cycle — show the LLM's prose reason for abstaining (display-only).
    pickEl.innerHTML = `
      <div class="reason-meta"><span class="reason-num">ABSTAIN REASONING</span></div>
      <p class="reason-block">${escapeHtml(c.last_no_trade_detail)}</p>`;
    $("pick-stale").hidden = true;
  } else {
    pickEl.innerHTML = `<p class="empty">no research pick on record yet</p>`;
    $("pick-stale").hidden = true;
  }

  // --- debate ---
  const d = c.debate;
  const debEl = $("cycle-debate");
  if (d && (d.rationale || (d.transcript && d.transcript.length))) {
    const decisionCls = d.final_decision === "TRADE" ? "is-ok" : "is-insufficient";
    const flip = d.final_direction && d.seed_direction && d.final_direction !== d.seed_direction
      ? `<span class="flip">flip ${escapeHtml(d.seed_direction)}→${escapeHtml(d.final_direction)}</span>` : "";
    const turns = (d.transcript || [])
      .map((t) => {
        const agent = String(t.agent || "").toUpperCase();
        const cls = agent === "BULL" ? "agent-bull" : agent === "BEAR" ? "agent-bear" : "agent-judge";
        return `<details class="turn">
          <summary><span class="${cls}">${agent || "—"}</span><span class="turn-model">${escapeHtml(t.model || "")}</span><span class="turn-round">r${t.round ?? "?"}</span></summary>
          <p class="reason-block">${escapeHtml(t.text || "")}</p>
        </details>`;
      })
      .join("");
    debEl.innerHTML = `
      <div class="reason-meta">
        <span class="tag ${decisionCls}">${escapeHtml(d.final_decision || "—")}</span>
        ${d.final_direction ? dirBadge(d.final_direction) : ""}
        ${flip}
        <span class="reason-num">conf ${fmtNum(d.confidence, 0)}</span>
        <span class="reason-num">${d.rounds_used ?? "?"} round(s)</span>
      </div>
      ${d.rationale ? `<p class="reason-block reason-block--judge">${escapeHtml(d.rationale)}</p>` : ""}
      <div class="turns">${turns}</div>`;
    markStale("debate-stale", d.ts, c.session_date);
  } else {
    debEl.innerHTML = `<p class="empty">no debate on record yet</p>`;
    $("debate-stale").hidden = true;
  }
}

function renderTokenMeter(t) {
  const pct = t.percent;
  $("tok-pct").textContent = pct == null ? "—" : `${fmtNum(pct, 1)}%`;
  setNum("tok-consumed", t.consumed_tokens, 0);
  $("tok-budget").textContent = t.budget == null ? "off" : fmtNum(t.budget, 0);
  setNum("tok-cost", t.cost_eur_today, 4);
  $("tok-calls").textContent = fmtNum(t.calls_today, 0);

  const bar = $("tok-bar");
  const w = pct == null ? 0 : Math.min(100, Math.max(0, pct));
  bar.style.width = w + "%";
  bar.classList.toggle("warn", pct != null && pct > 80 && pct < 100);
  bar.classList.toggle("over", pct != null && pct >= 100);
}

function renderConfidence(c) {
  const tag = $("conf-state");
  const state = c.state || "—";
  tag.textContent = state;
  tag.className = "tag " + ({ OK: "is-ok", INSUFFICIENT: "is-insufficient" }[state] || "is-unavailable");
  $("conf-n").textContent = `${c.n ?? "–"} / ${c.n_min ?? "–"}`;

  // dial: n / n_min progress arc + center count (circumference of r=15.5 ≈ 97.4)
  const n = Number(c.n), nmin = Number(c.n_min);
  const frac = nmin > 0 && Number.isFinite(n) ? Math.max(0, Math.min(1, n / nmin)) : 0;
  const arc = $("dial-arc");
  if (arc) arc.style.strokeDashoffset = String((97.4 * (1 - frac)).toFixed(2));
  $("dial-n").textContent = Number.isFinite(n) ? n : "–";
  $("conf-dial").setAttribute("class",
    "conf-dial " + ({ OK: "is-ok", INSUFFICIENT: "" }[state] || "is-unavailable"));
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
  setNum("score-now", pts.length ? pts[pts.length - 1] : null, 1);

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
        <stop offset="0%" stop-color="#e6a24c" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#e6a24c" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path class="spark-area" d="${area}"/>
    <path class="spark-line" d="${line}"/>
    <circle class="spark-dot" cx="${lastX}" cy="${lastY}" r="3.5"/>`;

  // draw-on the needle (renderScore is change-gated, so this only fires on real new data)
  if (!REDUCED) { svg.classList.remove("is-fresh"); void svg.offsetWidth; svg.classList.add("is-fresh"); }
}

let _prevTradeKeys = null; // null until first render, so the first paint doesn't animate every row
function tradeKey(t) {
  return `${t.deal_id || ""}|${t.open_ts || ""}|${t.direction || ""}|${t.open_level ?? ""}`;
}

function renderTrades(rows) {
  $("trades-count").textContent = rows.length;
  const body = $("trades-body");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="8" class="empty">no trades yet</td></tr>`;
    _prevTradeKeys = new Set();
    return;
  }
  body.innerHTML = rows
    .map((t) => {
      const dir = (t.direction || "").toUpperCase();
      const dirCls = dir === "BUY" ? "dir-buy" : dir === "SELL" ? "dir-sell" : "";
      const pl = t.profit_loss;
      const plCls = pl > 0 ? "pos" : pl < 0 ? "neg" : "";
      const stCls = "st--" + String(t.status || "").toLowerCase();
      return `<tr data-key="${escapeHtml(tradeKey(t))}">
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

  // highlight rows that are new since the last render (skip the very first paint)
  const keys = new Set(rows.map(tradeKey));
  if (_prevTradeKeys && !REDUCED) {
    body.querySelectorAll("tr[data-key]").forEach((tr) => {
      if (!_prevTradeKeys.has(tr.getAttribute("data-key"))) tr.classList.add("row-new");
    });
  }
  _prevTradeKeys = keys;
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
    const [status, cycle, conf, score, trades, lessons, tokens] = await Promise.all([
      getJSON("/api/status"),
      getJSON("/api/last_cycle"),
      getJSON("/api/confidence"),
      getJSON("/api/score"),
      getJSON("/api/trades"),
      getJSON("/api/lessons"),
      getJSON("/api/token_usage"),
    ]);
    renderStatus(status);
    renderConfidence(conf);
    renderTokenMeter(tokens);
    // heavy DOM rebuilds only when their payload changed (also preserves open <details>)
    renderIfChanged("cycle", cycle, renderCycle);
    renderIfChanged("score", score, renderScore);
    renderIfChanged("trades", trades, renderTrades);
    renderIfChanged("lessons", lessons, renderLessons);
    const u = $("updated-at");
    u.textContent = new Date().toLocaleTimeString();
    if (!REDUCED) { u.classList.remove("pip"); void u.offsetWidth; u.classList.add("pip"); }
    setConn(true);
  } catch (err) {
    setConn(false);
  }
}

// ---- controls ----
function flash(msg, isErr) {
  const el = $("control-msg");
  el.textContent = msg;
  el.style.color = isErr ? "var(--red)" : "var(--amber)";
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
