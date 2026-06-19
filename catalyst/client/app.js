"use strict";

const state = {
  customerId: "CUST-DEMO-1",
  customerName: "",
  history: [],
  copilot: false,
  voiceOn: true,
};

const thread = document.getElementById("thread");
const composer = document.getElementById("composer");
const input = document.getElementById("message");
const select = document.getElementById("customer");
const badge = document.getElementById("copilotBadge");
const micBtn = document.getElementById("micBtn");
const voiceToggle = document.getElementById("voiceToggle");
const avatarState = document.getElementById("avatarState");
const themeToggle = document.getElementById("themeToggle");

if (window.Chart) Chart.defaults.font.family = "Inter, sans-serif";

// ---- theme (light / dark) -------------------------------------------------

function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  if (themeToggle) {
    themeToggle.textContent = t === "light" ? "☀️" : "🌙";
    themeToggle.title = t === "light" ? "Switch to dark mode" : "Switch to light mode";
  }
}
let theme = localStorage.getItem("theme") || "dark";
applyTheme(theme);
if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    theme = theme === "light" ? "dark" : "light";
    localStorage.setItem("theme", theme);
    applyTheme(theme);
  });
}

// ---- avatar + voice -------------------------------------------------------

const STATE_LABEL = { idle: "online", thinking: "thinking…", listening: "listening…", speaking: "speaking…" };
let currentAvatarState = "idle";
function setAvatar(name) {
  currentAvatarState = name;
  if (window.AanyaAvatar && window.AanyaAvatar.setState) window.AanyaAvatar.setState(name);
  if (avatarState) avatarState.textContent = STATE_LABEL[name] || "online";
}

let voice = null;
function pickVoice() {
  const voices = window.speechSynthesis ? speechSynthesis.getVoices() : [];
  voice =
    voices.find((v) => /en-IN/i.test(v.lang) && /female|aditi|veena|kalpana/i.test(v.name)) ||
    voices.find((v) => /female|samantha|google uk english female|zira/i.test(v.name)) ||
    voices.find((v) => /en-IN/i.test(v.lang)) ||
    voices.find((v) => /^en/i.test(v.lang)) ||
    voices[0] ||
    null;
}
if (window.speechSynthesis) {
  pickVoice();
  speechSynthesis.onvoiceschanged = pickVoice;
}
function speak(text) {
  if (!state.voiceOn || !window.speechSynthesis || !text) {
    setAvatar("idle");
    return;
  }
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/[*#_`>]/g, ""));
  if (voice) u.voice = voice;
  u.rate = 0.8;
  u.pitch = 1.05;
  u.onstart = () => setAvatar("speaking");
  u.onend = () => setAvatar("idle");
  u.onerror = () => setAvatar("idle");
  speechSynthesis.speak(u);
}

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recog = null;
let listening = false;
if (SR && micBtn) {
  recog = new SR();
  recog.lang = "en-IN";
  recog.interimResults = false;
  recog.maxAlternatives = 1;
  recog.onstart = () => {
    listening = true;
    micBtn.classList.add("listening");
    setAvatar("listening");
  };
  recog.onresult = (e) => {
    input.value = e.results[0][0].transcript;
    composer.requestSubmit();
  };
  recog.onerror = () => stopListening();
  recog.onend = () => stopListening();
  micBtn.addEventListener("click", () => {
    if (listening) recog.stop();
    else {
      try {
        if (window.speechSynthesis) speechSynthesis.cancel();
        recog.start();
      } catch (_) {}
    }
  });
} else if (micBtn) {
  micBtn.style.display = "none";
}
function stopListening() {
  listening = false;
  if (micBtn) micBtn.classList.remove("listening");
  if (currentAvatarState !== "speaking") setAvatar("idle");
}
voiceToggle.addEventListener("click", () => {
  state.voiceOn = !state.voiceOn;
  voiceToggle.setAttribute("aria-pressed", String(state.voiceOn));
  voiceToggle.textContent = state.voiceOn ? "🔊 Voice on" : "🔇 Voice off";
  if (!state.voiceOn && window.speechSynthesis) speechSynthesis.cancel();
});

// ---- generic helpers ------------------------------------------------------

async function api(path, opts) {
  if (window.__WC_API__) return window.__WC_API__(path, opts);
  const res = await fetch(path, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || res.statusText);
    err.status = res.status;
    throw err;
  }
  return res.json();
}
function fmtINR(n) {
  n = Math.round(Number(n) || 0);
  const s = n < 0 ? "-" : "";
  const a = Math.abs(n);
  if (a >= 1e7) return s + "₹" + (a / 1e7).toFixed(2).replace(/\.00$/, "") + " Cr";
  if (a >= 1e5) return s + "₹" + (a / 1e5).toFixed(2).replace(/\.00$/, "") + " L";
  return s + "₹" + a.toLocaleString("en-IN");
}
function fmtShort(n) {
  n = Math.round(Number(n) || 0);
  const a = Math.abs(n);
  if (a >= 1e7) return (n / 1e7).toFixed(1).replace(/\.0$/, "") + "Cr";
  if (a >= 1e5) return Math.round(n / 1e5) + "L";
  if (a >= 1e3) return Math.round(n / 1e3) + "k";
  return "" + n;
}
const pct = (x) => (Number(x) * 100).toFixed(1) + "%";
const scrollDown = () => (thread.scrollTop = thread.scrollHeight);

function bubble(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  thread.appendChild(div);
  scrollDown();
  return div;
}
function card(html) {
  const div = document.createElement("div");
  div.className = "card";
  div.innerHTML = html;
  thread.appendChild(div);
  scrollDown();
  return div;
}
const typing = () => bubble("bot typing", "Aanya is thinking…");

// ---- charts ---------------------------------------------------------------

let _uid = 0;
const uid = () => "chart" + ++_uid;
function themeColors() {
  const cs = getComputedStyle(document.documentElement);
  const g = (n) => cs.getPropertyValue(n).trim();
  return {
    text: g("--text"),
    muted: g("--muted"),
    teal: g("--teal"),
    violet: g("--violet"),
    magenta: g("--magenta"),
    amber: g("--amber"),
    ok: g("--ok"),
    danger: g("--danger"),
    line: g("--line-2"),
  };
}
function palette() {
  const c = themeColors();
  return [c.teal, c.violet, c.amber, c.magenta, "#4d9fff", c.ok];
}
function chartbox(node, id, height) {
  const el = node.querySelector("#" + id);
  if (el) el.parentElement.style.height = (height || 200) + "px";
  return el;
}
function doughnut(canvas, labels, data, fmt) {
  if (!window.Chart || !canvas) return;
  const c = themeColors();
  fmt = fmt || fmtINR;
  new Chart(canvas, {
    type: "doughnut",
    data: { labels, datasets: [{ data, backgroundColor: palette(), borderWidth: 0 }] },
    options: {
      maintainAspectRatio: false,
      cutout: "60%",
      plugins: {
        legend: { position: "right", labels: { color: c.muted, boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: (x) => " " + x.label + ": " + fmt(x.raw) } },
      },
    },
  });
}
function barChart(canvas, labels, data, fmt, colors) {
  if (!window.Chart || !canvas) return;
  const c = themeColors();
  fmt = fmt || fmtINR;
  new Chart(canvas, {
    type: "bar",
    data: { labels, datasets: [{ data, backgroundColor: colors || palette(), borderRadius: 6 }] },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (x) => " " + fmt(x.raw) } } },
      scales: {
        x: { ticks: { color: c.muted, font: { size: 11 } }, grid: { display: false } },
        y: { ticks: { color: c.muted, font: { size: 10 }, callback: (v) => fmtShort(v) }, grid: { color: c.line } },
      },
    },
  });
}
function lineChart(canvas, labels, datasets) {
  if (!window.Chart || !canvas) return null;
  const c = themeColors();
  return new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: c.muted, boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: (x) => " " + x.dataset.label + ": " + fmtINR(x.raw) } },
      },
      scales: {
        x: { ticks: { color: c.muted, font: { size: 11 } }, grid: { display: false } },
        y: { ticks: { color: c.muted, font: { size: 10 }, callback: (v) => fmtShort(v) }, grid: { color: c.line } },
      },
    },
  });
}
function riskRing(canvas, score, color) {
  if (!window.Chart || !canvas) return;
  const c = themeColors();
  new Chart(canvas, {
    type: "doughnut",
    data: { datasets: [{ data: [score, 100 - score], backgroundColor: [color, c.line], borderWidth: 0 }] },
    options: { maintainAspectRatio: false, cutout: "72%", plugins: { legend: { display: false }, tooltip: { enabled: false } } },
  });
}
function projectSeries(current, monthly, annual, years) {
  const r = Math.pow(1 + annual, 1 / 12) - 1;
  const pts = [];
  for (let y = 0; y <= years; y++) {
    const n = 12 * y;
    const corpus = current * Math.pow(1 + r, n) + (r ? monthly * ((Math.pow(1 + r, n) - 1) / r) : monthly * n);
    pts.push(Math.round(corpus));
  }
  return pts;
}

// ---- visual render functions (no user bubble) -----------------------------

async function renderInsights() {
  setAvatar("thinking");
  const t = typing();
  try {
    const ins = await api(`/api/customers/${state.customerId}/insights`);
    t.remove();
    bubble("bot", "Here's a visual snapshot of your money:");
    const dId = uid();
    const bId = uid();
    const actions = ins.actions
      .map(
        (a) =>
          `<div class="action"><div class="t">${a.title}</div><div class="d">${a.detail}</div>` +
          `<span class="impact ${a.impact}">${a.impact} impact</span></div>`
      )
      .join("");
    const node = card(`
      <h3>Your financial snapshot</h3>
      <p class="sub">Estimated from ${ins.months_observed} months of transactions</p>
      <div class="stat-row">
        <div class="stat"><div class="k">Monthly income</div><div class="v">${fmtINR(ins.estimated_monthly_income)}</div></div>
        <div class="stat"><div class="k">Savings rate</div><div class="v ok">${pct(ins.savings_rate)}</div></div>
        <div class="stat"><div class="k">Idle cash</div><div class="v amber">${fmtINR(ins.idle_cash)}</div></div>
        <div class="stat"><div class="k">Costly EMI / mo</div><div class="v danger">${fmtINR(ins.monthly_costly_debt)}</div></div>
      </div>
      <div class="chart-title">Where your money goes (monthly)</div>
      <div class="chartbox"><canvas id="${dId}"></canvas></div>
      <div class="chart-title">Income vs spending</div>
      <div class="chartbox"><canvas id="${bId}"></canvas></div>
      ${actions}
      <p class="disclaimer">Charts built from your own transaction behaviour.</p>`);

    const cats = ins.top_spend_categories || [];
    const labels = cats.map((c) => c.category);
    const data = cats.map((c) => c.monthly_amount);
    const known = data.reduce((s, v) => s + v, 0);
    const other = Math.max(0, ins.estimated_monthly_expenses - known);
    if (other > 0) {
      labels.push("other");
      data.push(other);
    }
    doughnut(chartbox(node, dId, 190), labels, data);
    const surplus = Math.max(0, ins.estimated_monthly_income - ins.estimated_monthly_expenses);
    const c = themeColors();
    barChart(
      chartbox(node, bId, 170),
      ["Income", "Spending", "Surplus"],
      [ins.estimated_monthly_income, ins.estimated_monthly_expenses, surplus],
      fmtINR,
      [c.teal, c.danger, c.ok]
    );

    const line =
      ins.idle_cash > 0
        ? `You have about ${fmtINR(ins.idle_cash)} sitting idle and a high-interest EMI. I'd clear the debt first, then put the idle cash to work.`
        : "Here's where your money goes, with the actions I'd prioritise.";
    speak(line);
  } catch (e) {
    t.remove();
    setAvatar("idle");
    bubble("bot", "Could not load insights: " + e.message);
  }
}

async function renderGoal(opts) {
  const target = opts.target || 5000000;
  const horizon = opts.horizon || 8;
  const label = opts.label || "house";
  setAvatar("thinking");
  const t = typing();
  try {
    const plan = await api("/api/goal-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: state.customerId, label, target_amount: target, horizon_years: horizon, current_savings: 0 }),
    });
    t.remove();
    bubble("bot", `Here's a plan to reach ${fmtINR(target)} for your ${label} in ${horizon} years:`);
    const aId = uid();
    const gId = uid();
    const holdings = plan.allocation.holdings
      .map((h) => `<span class="holding">${Math.round(h.weight * 100)}% · ${h.product_name}</span>`)
      .join("");
    const node = card(`
      <h3>${label.charAt(0).toUpperCase() + label.slice(1)} goal · ${horizon} years</h3>
      <p class="sub">${plan.bucket} risk profile · blended return ~${pct(plan.expected_return_pa)} p.a.</p>
      <div class="stat-row">
        <div class="stat"><div class="k">Required monthly SIP</div><div class="v teal">${fmtINR(plan.required_monthly)}</div></div>
        <div class="stat"><div class="k">Target in today's money</div><div class="v">${fmtINR(plan.inflation_adjusted_target)}</div></div>
      </div>
      <div class="chart-title">Recommended allocation</div>
      <div class="chartbox"><canvas id="${aId}"></canvas></div>
      <div class="holdings">${holdings}</div>
      <div class="chart-title">Projected growth</div>
      <div class="chartbox"><canvas id="${gId}"></canvas></div>
      <div class="sim">
        <label>Invest <b><span id="simVal">${fmtINR(plan.required_monthly)}</span></b> / month</label>
        <input id="simRange" type="range" min="2000" max="60000" step="1000" value="${Math.min(60000, plan.required_monthly)}" />
        <div class="out">Projected in ${horizon} yrs: <b id="simOut">—</b> <span id="simFlag"></span></div>
      </div>
      <p class="disclaimer">Indicative returns, not guaranteed; subject to market risk.</p>`);

    doughnut(
      chartbox(node, aId, 180),
      plan.allocation.holdings.map((h) => h.product_name),
      plan.allocation.holdings.map((h) => Math.round(h.weight * 100)),
      (v) => v + "%"
    );

    const c = themeColors();
    const years = Array.from({ length: horizon + 1 }, (_, i) => "Yr " + i);
    const startMonthly = Math.min(60000, plan.required_monthly);
    const growth = lineChart(chartbox(node, gId, 200), years, [
      {
        label: "Projected corpus",
        data: projectSeries(0, startMonthly, plan.expected_return_pa, horizon),
        borderColor: c.teal,
        backgroundColor: "rgba(34,227,200,0.12)",
        fill: true,
        tension: 0.3,
        pointRadius: 0,
      },
      {
        label: "Target",
        data: Array(horizon + 1).fill(target),
        borderColor: c.amber,
        borderDash: [6, 4],
        pointRadius: 0,
        fill: false,
      },
    ]);

    const range = node.querySelector("#simRange");
    const runSim = async () => {
      node.querySelector("#simVal").textContent = fmtINR(range.value);
      if (growth) {
        growth.data.datasets[0].data = projectSeries(0, Number(range.value), plan.expected_return_pa, horizon);
        growth.update();
      }
      try {
        const sim = await api("/api/simulate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ customer_id: state.customerId, label, target_amount: target, horizon_years: horizon, monthly_contribution: Number(range.value) }),
        });
        node.querySelector("#simOut").textContent = fmtINR(sim.projected_corpus);
        const flag = node.querySelector("#simFlag");
        flag.textContent = sim.meets_target ? "✓ on track" : "↓ short";
        flag.style.color = sim.meets_target ? "var(--ok)" : "var(--danger)";
      } catch (_) {}
    };
    range.addEventListener("input", runSim);
    runSim();
    speak(
      `To reach ${fmtShort(target)} in ${horizon} years on a ${plan.bucket} portfolio, you'd invest about ${fmtINR(plan.required_monthly)} a month. Drag the slider to explore other amounts.`
    );
  } catch (e) {
    t.remove();
    setAvatar("idle");
    bubble("bot", "Could not build the plan: " + e.message);
  }
}

async function renderRisk() {
  setAvatar("thinking");
  const t = typing();
  try {
    const r = await api("/api/risk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: state.customerId }),
    });
    t.remove();
    bubble("bot", "Here's your risk profile:");
    const gId = uid();
    const colors = { conservative: "var(--teal)", balanced: "var(--violet)", aggressive: "var(--amber)" };
    const bucketColor = { conservative: themeColors().teal, balanced: themeColors().violet, aggressive: themeColors().amber }[r.bucket];
    const factors = r.factors
      .filter((f) => f.factor !== "baseline")
      .map((f) => `<div class="action"><div class="t">${f.factor} · ${f.contribution > 0 ? "+" : ""}${f.contribution}</div><div class="d">${f.note}</div></div>`)
      .join("");
    const node = card(`
      <h3>Risk profile · ${r.bucket}</h3>
      <p class="sub">Risk-capacity score, explained factor by factor</p>
      <div class="chartbox"><canvas id="${gId}"></canvas>
        <div class="gauge-overlay"><span class="g-score" style="color:${colors[r.bucket]}">${r.score}</span><span class="g-sub">/ 100 · ${r.bucket}</span></div>
      </div>
      ${factors}
      <p class="disclaimer">Score drives your recommended allocation.</p>`);
    riskRing(chartbox(node, gId, 200), r.score, bucketColor);
    speak(`Your risk-capacity score is ${r.score} out of 100, which puts you in the ${r.bucket} bracket.`);
  } catch (e) {
    t.remove();
    setAvatar("idle");
    bubble("bot", "Could not assess risk: " + e.message);
  }
}

async function renderProducts(query) {
  setAvatar("thinking");
  const t = typing();
  try {
    const res = await api("/api/products?q=" + encodeURIComponent(query || "invest"));
    t.remove();
    const products = (res.products || []).filter((p) => p.relevance > 0).slice(0, 5);
    if (!products.length) {
      setAvatar("idle");
      bubble("bot", "I couldn't find a matching product. Try 'tax saving', 'retirement' or 'low risk'.");
      return;
    }
    bubble("bot", "Here are matching IDBI products, with indicative (not guaranteed) returns:");
    const bId = uid();
    const rows = products
      .map(
        (p) =>
          `<div class="prod"><div><div class="pn">${p.name}</div><div class="pm">${p.category} · ${p.risk_level} risk · min ${fmtINR(p.min_investment)}</div></div><div class="pr">${p.indicative_return}</div></div>`
      )
      .join("");
    const node = card(`
      <h3>Product matches</h3>
      <p class="sub">Grounded in the IDBI catalogue · query: "${query}"</p>
      <div class="prod-list">${rows}</div>
      <div class="chart-title">Indicative return p.a.</div>
      <div class="chartbox"><canvas id="${bId}"></canvas></div>
      <p class="disclaimer">Indicative only and subject to market risk; not guaranteed.</p>`);
    barChart(
      chartbox(node, bId, 180),
      products.map((p) => p.name.replace(/^IDBI /, "").slice(0, 16)),
      products.map((p) => +(p.indicative_return_pa * 100).toFixed(1)),
      (v) => v + "%"
    );
    speak("Here are some grounded options with their indicative returns and risk levels.");
  } catch (e) {
    t.remove();
    setAvatar("idle");
    bubble("bot", "Could not search products: " + e.message);
  }
}

// ---- intent routing -------------------------------------------------------

function parseGoal(t) {
  let target = 5000000;
  let horizon = 8;
  let label = "goal";
  const cr = t.match(/(\d+(?:\.\d+)?)\s*(crore|cr)\b/i);
  const lk = t.match(/(\d+(?:\.\d+)?)\s*(lakh|lac|l)\b/i);
  if (cr) target = Math.round(parseFloat(cr[1]) * 1e7);
  else if (lk) target = Math.round(parseFloat(lk[1]) * 1e5);
  const yr = t.match(/(\d+)\s*(year|yr)/i);
  if (yr) horizon = parseInt(yr[1], 10);
  if (/house|home|flat|apartment/i.test(t)) label = "house";
  else if (/car|vehicle/i.test(t)) label = "car";
  else if (/retire|pension/i.test(t)) label = "retirement";
  else if (/child|education|college|school/i.test(t)) label = "education";
  else if (/wedding|marriage/i.test(t)) label = "wedding";
  return { target, horizon, label };
}

function routeIntent(t) {
  const s = t.toLowerCase();
  if (/(spend|spending|expense|where.*money|budget|categor|breakdown|snapshot|health|start|begin|improve|overview)/.test(s))
    return { kind: "insights" };
  if (/(risk profile|my risk|how much risk|aggressive|conservative|risk score)/.test(s)) return { kind: "risk" };
  if (/(goal|house|home|car|retire|education|wedding|plan .*\b(year|yr|lakh|crore)|sip|save for|target|corpus|lakh|crore)/.test(s))
    return { kind: "goal", opts: parseGoal(t) };
  if (/(product|fund|invest in|where.*invest|options|fixed deposit|\bfd\b|tax sav|recommend|scheme)/.test(s))
    return { kind: "products", query: t };
  return null;
}

// ---- chat -----------------------------------------------------------------

async function handleMessage(text) {
  bubble("user", text);
  const intent = routeIntent(text);
  if (intent) {
    if (intent.kind === "insights") return renderInsights();
    if (intent.kind === "risk") return renderRisk();
    if (intent.kind === "goal") return renderGoal(intent.opts);
    if (intent.kind === "products") return renderProducts(intent.query);
  }
  return sendChatLLM(text);
}

async function sendChatLLM(text) {
  setAvatar("thinking");
  const t = typing();
  const prior = state.history.slice();
  try {
    const reply = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: state.customerId, message: text, history: prior }),
    });
    t.remove();
    bubble("bot", reply.answer);
    if (reply.tool_trace && reply.tool_trace.length) {
      const items = reply.tool_trace.map((s) => `<li>${s.tool}${s.is_error ? " ⚠️" : ""}</li>`).join("");
      const why = document.createElement("details");
      why.className = "why";
      why.innerHTML = `<summary>Why this? (${reply.tool_trace.length} data lookups)</summary><ul>${items}</ul>`;
      thread.appendChild(why);
    }
    if (reply.guardrail_triggered) {
      const g = document.createElement("div");
      g.className = "guard";
      g.textContent = "⚠️ Compliance guardrail adjusted this response to stay within bank policy.";
      thread.appendChild(g);
    }
    scrollDown();
    state.history.push({ role: "user", content: text });
    state.history.push({ role: "assistant", content: reply.answer });
    speak(reply.answer);
  } catch (e) {
    t.remove();
    setAvatar("idle");
    if (e.status === 503) {
      bubble(
        "bot",
        "The live copilot needs Anthropic API credits — but you can still ask me for data visually: try “show my spending”, “plan ₹50 lakh in 8 years”, “my risk profile”, or “tax-saving products”."
      );
    } else {
      bubble("bot", "Sorry, something went wrong: " + e.message);
    }
  }
}

// ---- bootstrap ------------------------------------------------------------

async function boot() {
  try {
    const cfg = await api("/api/config");
    state.copilot = cfg.copilot_available;
    badge.textContent = cfg.copilot_available ? "● online" : "● demo mode";
    badge.className = "badge " + (cfg.copilot_available ? "ok" : "");
  } catch (e) {
    badge.textContent = "offline";
  }
  try {
    const customers = await api("/api/customers");
    select.innerHTML = "";
    customers.forEach((c) => {
      const o = document.createElement("option");
      o.value = c.customer_id;
      o.textContent = `${c.name} · ${c.customer_id}`;
      select.appendChild(o);
    });
    select.value = state.customerId;
    const cur = customers.find((c) => c.customer_id === state.customerId);
    state.customerName = cur ? cur.name : "";
    greet();
  } catch (e) {
    bubble("bot", "Could not load customers. Is the server running?");
  }
}
function greet() {
  thread.innerHTML = "";
  state.history = [];
  const first = (state.customerName || "there").split(" ")[0];
  bubble(
    "bot",
    `Hi, I'm Aanya — your AI wealth copilot. Ask me for data and I'll show it as charts: try “show my spending”, “plan ₹50 lakh house in 8 years”, or “my risk profile”. Tap a quick action, type, or press 🎙 to talk.`
  );
  setAvatar("idle");
}

// ---- events ---------------------------------------------------------------

document.getElementById("quick").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-flow]");
  if (!btn) return;
  const flow = btn.getAttribute("data-flow");
  if (flow === "start") {
    bubble("user", "Give me my financial snapshot.");
    renderInsights();
  } else if (flow === "spending") {
    bubble("user", "Where does my money go?");
    renderInsights();
  } else if (flow === "goal") {
    bubble("user", "Help me plan ₹50 lakh for a house in 8 years.");
    renderGoal({ target: 5000000, horizon: 8, label: "house" });
  } else if (flow === "retire") {
    bubble("user", "Plan ₹2 crore for retirement in 20 years.");
    renderGoal({ target: 20000000, horizon: 20, label: "retirement" });
  } else if (flow === "risk") {
    bubble("user", "What's my risk profile?");
    renderRisk();
  } else if (flow === "products") {
    bubble("user", "Show me the best products for me.");
    renderProducts("balanced growth long term investment");
  } else if (flow === "safety") {
    if (state.copilot) handleMessage("Can you guarantee me 15% returns?");
    else flowSafetyStatic();
  }
});

function flowSafetyStatic() {
  bubble("user", "Can you guarantee me 15% returns?");
  card(`
    <h3>Why I won't promise that</h3>
    <p class="sub">Compliance guardrail — enforced in code, unit-tested</p>
    <div class="guard">Aanya never promises guaranteed, assured, or risk-free returns. A code-level validator
      blocks any such claim before it reaches you, and every product I mention must trace back to a real
      catalogue lookup — no invented returns.</div>
    <p class="disclaimer">Add Anthropic credits to chat with the live copilot.</p>`);
  speak("I can't promise guaranteed returns — every market-linked investment carries risk. But I can show you suitable IDBI options with their indicative returns and risks.");
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  handleMessage(text);
});

select.addEventListener("change", () => {
  state.customerId = select.value;
  state.customerName = select.options[select.selectedIndex].textContent.split(" · ")[0];
  greet();
});

boot();
