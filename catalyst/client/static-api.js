"use strict";
/*
 * Static API shim — replaces the FastAPI backend for Catalyst client hosting.
 * Ports the quant engine (risk, portfolio, goals, products) to the browser and serves
 * pre-baked data from window.__WC_DATA__. window.__WC_API__(path, opts) mirrors the
 * server's JSON responses so app.js works unchanged. The live LLM chat returns 503.
 */
(function () {
  if (!window.__WC_DATA__) return;
  var D = window.__WC_DATA__;

  var OCC_STAB = { salaried: 4, business: 3, self_employed: 2 };
  var ALLOC = {
    conservative: { equity: 0.2, debt: 0.7, gold: 0.1 },
    balanced: { equity: 0.5, debt: 0.4, gold: 0.1 },
    aggressive: { equity: 0.75, debt: 0.15, gold: 0.1 },
  };
  var ASSET_RETURN = { equity: 0.11, debt: 0.067, gold: 0.075, hybrid: 0.09 };
  var ASSET_PRODUCT = { equity: "MF-EQ-301", debt: "IDBI-FD-001", gold: "GOLD-SGB-401" };
  var INFLATION = 0.06;
  var BY_PID = {};
  D.catalogue.forEach(function (p) { BY_PID[p.product_id] = p; });

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function r4(x) { return Math.round(x * 10000) / 10000; }
  function err(status, msg) { var e = new Error(msg || "error"); e.status = status; throw e; }

  function assessRisk(body) {
    var c = D.byId[body.customer_id];
    if (!c) err(404, "customer not found");
    var horizon = body.horizon_years != null ? body.horizon_years : 7;
    var lt = body.loss_tolerance != null ? body.loss_tolerance : 3;
    var hasEF = body.has_emergency_fund != null ? body.has_emergency_fund : true;
    var f = [];
    f.push({ factor: "baseline", contribution: 50, note: "Neutral starting point" });
    f.push({ factor: "age", contribution: Math.trunc(clamp((40 - c.age) * 0.6, -18, 18)),
             note: "Age " + c.age + ": a longer earning runway raises risk capacity" });
    f.push({ factor: "horizon", contribution: Math.trunc(clamp((horizon - 5) * 2, -16, 20)),
             note: horizon + "-year horizon: more time absorbs market swings" });
    f.push({ factor: "loss_tolerance", contribution: (lt - 3) * 8,
             note: "Loss tolerance " + lt + "/5 (willingness to stay invested)" });
    var stab = OCC_STAB[c.occupation] != null ? OCC_STAB[c.occupation] : 3;
    f.push({ factor: "income_stability", contribution: (stab - 3) * 4,
             note: "Income stability " + stab + "/5 (" + c.occupation + ")" });
    f.push({ factor: "dependents", contribution: -(c.dependents || 0) * 2,
             note: (c.dependents || 0) + " dependent(s): higher obligations reduce capacity" });
    f.push({ factor: "emergency_fund", contribution: hasEF ? 5 : -8,
             note: hasEF ? "Emergency fund in place" : "No emergency buffer" });
    var total = f.reduce(function (s, x) { return s + x.contribution; }, 0);
    var score = Math.trunc(clamp(total, 0, 100));
    var bucket = score < 35 ? "conservative" : score <= 65 ? "balanced" : "aggressive";
    return { score: score, bucket: bucket, factors: f };
  }

  function deriveBucket(cid, horizon) {
    return assessRisk({ customer_id: cid, horizon_years: horizon }).bucket;
  }

  function buildPortfolio(bucket) {
    var alloc = ALLOC[bucket];
    var holdings = [];
    var blended = 0;
    ["equity", "debt", "gold"].forEach(function (ac) {
      var w = alloc[ac];
      var prod = BY_PID[ASSET_PRODUCT[ac]];
      holdings.push({ asset_class: ac, weight: r4(w), product_id: prod.product_id,
                      product_name: prod.name, indicative_return_pa: prod.indicative_return_pa });
      blended += w * ASSET_RETURN[ac];
    });
    return { bucket: bucket, holdings: holdings, blended_return_pa: r4(blended),
             product_ids: holdings.map(function (h) { return h.product_id; }) };
  }

  function mrate(a) { return Math.pow(1 + a, 1 / 12) - 1; }
  function fvAnnuity(m, r, n) { return r === 0 ? m * n : m * ((Math.pow(1 + r, n) - 1) / r); }
  function projectCorpus(cur, m, annual, years) {
    var r = mrate(annual), n = Math.round(years * 12);
    return cur * Math.pow(1 + r, n) + fvAnnuity(m, r, n);
  }
  function requiredMonthly(target, cur, annual, years) {
    var r = mrate(annual), n = Math.round(years * 12);
    var fv = cur * Math.pow(1 + r, n);
    var rem = target - fv;
    if (rem <= 0) return 0;
    return r === 0 ? rem / n : (rem * r) / (Math.pow(1 + r, n) - 1);
  }

  function goalPlan(b) {
    if (!D.byId[b.customer_id]) err(404, "customer not found");
    var horizon = Number(b.horizon_years);
    var bucket = b.bucket || deriveBucket(b.customer_id, horizon);
    var target = Math.round(Number(b.target_amount));
    var cur = Math.round(Number(b.current_savings || 0));
    var port = buildPortfolio(bucket);
    var rate = port.blended_return_pa;
    var sip = D.customerSIP[b.customer_id] || 0;
    var required = requiredMonthly(target, cur, rate, horizon);
    var projected = projectCorpus(cur, sip, rate, horizon);
    var gap = target - projected;
    return {
      label: b.label, target_amount: target, horizon_years: horizon, current_savings: cur, bucket: bucket,
      expected_return_pa: r4(rate), required_monthly: Math.round(required),
      current_monthly_investment: Math.round(sip), projected_with_current: Math.round(projected),
      gap: Math.round(gap), on_track: gap <= 0,
      additional_monthly_needed: Math.round(Math.max(0, required - sip)),
      inflation_adjusted_target: Math.round(target / Math.pow(1 + INFLATION, horizon)),
      allocation: port, product_ids: port.product_ids.slice(),
    };
  }

  function simulateGoal(b) {
    var horizon = Number(b.horizon_years);
    var bucket = b.bucket || deriveBucket(b.customer_id, horizon);
    var target = Math.round(Number(b.target_amount));
    var cur = Math.round(Number(b.current_savings || 0));
    var port = buildPortfolio(bucket);
    var rate = port.blended_return_pa;
    var m = Number(b.monthly_contribution);
    var projected = projectCorpus(cur, m, rate, horizon);
    return {
      label: b.label, monthly_contribution: Math.round(m), horizon_years: horizon,
      expected_return_pa: r4(rate), projected_corpus: Math.round(projected),
      target_amount: target, meets_target: projected >= target, surplus_or_gap: Math.round(projected - target),
    };
  }

  function tokenize(s) { return (s.toLowerCase().match(/[a-z0-9]+/g) || []); }
  function searchProducts(query) {
    var qt = tokenize(query || "");
    var scored = D.catalogue.map(function (p) {
      var doc = new Set(tokenize([p.name, p.category, p.asset_class, p.risk_level, p.description, p.lock_in].join(" ")));
      var overlap = 0;
      qt.forEach(function (t) { if (doc.has(t)) overlap++; });
      return { p: p, score: qt.length ? overlap / qt.length : 0 };
    });
    scored.sort(function (a, b) { return b.score - a.score || a.p.min_investment - b.p.min_investment; });
    return scored.slice(0, 8).map(function (s) {
      var o = {}; for (var k in s.p) o[k] = s.p[k]; o.relevance = r4(s.score); return o;
    });
  }

  window.__WC_API__ = async function (path, opts) {
    opts = opts || {};
    var method = (opts.method || "GET").toUpperCase();
    var body = opts.body ? JSON.parse(opts.body) : {};
    var u = new URL(path, location.origin);
    var p = u.pathname, q = u.searchParams, m;

    if (p === "/api/config") return D.config;
    if (p === "/api/customers") return D.customers;
    if ((m = p.match(/^\/api\/customers\/([^/]+)\/insights$/))) {
      var ins = D.insights[m[1]]; if (!ins) err(404, "customer not found"); return ins;
    }
    if ((m = p.match(/^\/api\/customers\/([^/]+)$/))) {
      var c = D.byId[m[1]]; if (!c) err(404, "customer not found"); return c;
    }
    if (p === "/api/risk") return assessRisk(body);
    if (p === "/api/goal-plan") return goalPlan(body);
    if (p === "/api/simulate") return simulateGoal(body);
    if (p === "/api/products") return { products: searchProducts(q.get("q") || "") };
    if (p === "/api/chat") err(503, "The live copilot needs Anthropic API credits.");
    err(404, "not found (" + method + " " + p + ")");
  };
})();
