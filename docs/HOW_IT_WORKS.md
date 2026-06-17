# How it works

> Screenshots referenced below live in [`screenshots/`](screenshots/). See [screenshots/README.md](screenshots/README.md) for the capture list — drop the PNGs in and these images render automatically.

## The home screen

![Home — dark](screenshots/01-hero-dark.png)

Two panes on one screen:
- **Left** — the IDBI logo, "Meet Aanya", and the **3D AI avatar** with a live status dot.
- **Right** — the **conversation**: quick-action chips, the message thread, and the mic + text composer.
- **Top bar** — online status, the **customer selector**, and a **light/dark toggle** (persisted across refreshes).

![Home — light](screenshots/02-hero-light.png)

## Two ways to get an answer

When you send a message, `app.js` runs an **intent router** before anything else:

```
type / speak a message
        │
        ▼
  routeIntent(text)
   ├── matches a DATA intent ──► run the quant endpoint ──► render a CHART card   (no API key)
   └── no match ─────────────► POST /api/chat ──► Claude agent + guardrails ──► text reply
```

This means **data questions are answered instantly and visually**, and only open-ended conversation uses the LLM. The router also **parses numbers** — "₹50 lakh", "2 crore", "8 years", "house/car/retirement" all feed the goal planner.

## Visual flow 1 — Snapshot / "where my money goes"

*Triggers: "My snapshot", "where my money goes", "spending", "where do I start".*

![Snapshot with charts](screenshots/03-snapshot-charts.png)

1. `GET /api/customers/{id}/insights` → `app/quant/insights.py` analyses the transaction ledger.
2. It estimates **monthly income** (mean of salary credits), **expenses**, **savings rate**, **idle cash** (savings above a 6-month emergency buffer), and flags **high-interest EMIs**.
3. The UI renders a **spending doughnut** (by category, with an "other" slice), an **income vs spending vs surplus bar**, and a ranked list of **next-best-actions** — each with the numbers behind it.
4. Aanya speaks a one-line summary.

## Visual flow 2 — Goal planning

*Triggers: "Plan ₹50L house", "Retirement plan", "plan 1 crore in 20 years", "save for…".*

![Goal plan](screenshots/04-goal-plan.png)

1. `POST /api/goal-plan` → `app/quant/goals.py`.
2. The risk bucket comes from `assess_risk` (or is passed in); the portfolio (`portfolio.py`) gives a blended expected return.
3. **Required monthly SIP** is solved from the future-value-of-annuity formula:

   ```
   r = (1 + annual_return)^(1/12) − 1
   required = (target − current·(1+r)^n) · r / ((1+r)^n − 1)        n = months
   ```

4. The UI shows an **allocation doughnut** (grounded in real products), a **projected-growth line chart** with a dashed **target line**, and a **slider** that **redraws the growth curve live** while `/api/simulate` reports whether each amount is on track.

## Visual flow 3 — Risk profile

*Triggers: "My risk profile", "how much risk", "aggressive/conservative".*

![Risk profile gauge](screenshots/05-risk-profile.png)

`POST /api/risk` → `app/quant/risk.py` computes a 0–100 risk-capacity score from an **additive, fully explainable** rubric (age, horizon, loss tolerance, income stability, dependents, emergency fund). The UI renders a **score ring gauge** plus a **factor-by-factor breakdown** so every point is justified — exactly the explainability a bank reviewer wants.

## Visual flow 4 — Products

*Triggers: "best products", "where to invest", "tax-saving", "low-risk fund".*

![Products](screenshots/06-products.png)

`GET /api/products?q=…` → the **TF-IDF retriever** ranks the catalogue. The UI lists matches (name, category, risk, min investment, **indicative** return) and a **bar chart comparing indicative returns** — always labelled indicative, never guaranteed.

## The conversational copilot (the LLM path)

For anything not matched by the router, `POST /api/chat` runs the agent loop in `app/agent/orchestrator.py`:

```
user message
   ▼
Claude (claude-opus-4-8, adaptive thinking) ── wants a tool? ──► execute tool ──┐
   ▲                                                                            │
   └──────────────────── tool results fed back ◄───────────────────────────────┘
   ▼ (no more tools)
final answer ──► guardrail validate ──► (if violation) one corrective turn ──► reply
```

The model can **only** answer by composing tools (`get_customer_profile`, `get_next_best_actions`, `assess_risk`, `plan_goal`, `simulate_goal`, `search_products`). Each reply carries a **"Why this?"** trail of the data lookups it made.

![Voice + guardrail](screenshots/07-voice-guardrail.png)

## Guardrails (trust layer)

`app/agent/guardrails.py` validates the final text and is unit-tested independently of the LLM:

- **No guaranteed returns** — affirmative promises of guaranteed/assured/risk-free returns are blocked (while compliant phrasing like "returns are *not* guaranteed" passes).
- **Product grounding** — any catalogue product named in the answer must have been looked up via `search_products`/`plan_goal` this turn.

If a check fails, the agent gets exactly one corrective turn; if it still fails, a safe fallback message is returned. This is the maturity signal that separates this from a chatbot wrapper.

## The 3D avatar (`web/avatar.js`)

A stylised Three.js robot — metallic head, glowing visor eyes, antenna, orbiting halo rings, particle field. It is **voice-reactive**:

| State | Behaviour |
|-------|-----------|
| idle | gentle bob, follows the cursor, occasional blink |
| listening | eyes/halo shift magenta, halo spins faster |
| thinking | eyes shimmer, subtle mouth idle |
| speaking | mouth equaliser animates with the speech |

If WebGL is unavailable it falls back to a glowing CSS orb — the app never breaks.

## Voice (`web/app.js`)

- **Speak to Aanya** — the mic button uses the Web Speech `SpeechRecognition` API; the transcript is auto-submitted.
- **Aanya speaks back** — replies use `SpeechSynthesis` (a calm ~0.8 rate, Indian/female voice when available), driving the avatar's speaking animation. A top-bar toggle turns voice on/off.

## Theming

A light/dark toggle flips a `data-theme` attribute on `<html>`; the whole UI recolours through CSS variables and the choice is saved in `localStorage`. Charts adopt the current theme's colors when drawn.
