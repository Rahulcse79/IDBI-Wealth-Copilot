# IDBI Wealth Copilot — Aanya

Our entry for **IDBI Innovate 2026 · Track 01 (Wealth Advisory)**. **Aanya** is an avatar-led, agentic, explainable AI wealth advisor that lives inside the IDBI mobile app and gives every customer bank-grade, personalised guidance — grounded in their own transaction behaviour, shown as charts, spoken by a 3D avatar, and protected by compliance guardrails enforced in code.

> Goal: 1st place (₹2L). First-round submission deadline: **9 July 2026**.

![Architecture](docs/architecture.svg)

## Highlights

- 🤖 **3D AI avatar (Three.js)** — voice-reactive; idle / listening / thinking / speaking states.
- 🎙 **Voice chat** — talk to Aanya and hear her reply (Web Speech API).
- 📊 **Answers as charts** — spending doughnut, goal-growth line, risk ring gauge, product-return bars (Chart.js).
- 🧠 **A real quant engine, not a chatbot** — risk profiling, goal-based SIP planning, portfolio construction, behavioural insights. Pure functions, unit-tested.
- 🛡 **Compliant by design** — code-level guardrails block guaranteed-return claims and ungrounded products; advice only, never executes transactions.
- 🌗 **Light / dark mode**, responsive, single-screen layout.
- 🔌 **Deployable** — one env var swaps synthetic data for IDBI sandbox APIs.

## Run it

```bash
./start.sh           # sets up + runs on http://localhost:8000
./start.sh test      # run the 20-test suite
PORT=8078 ./start.sh # use another port if 8000 is busy
```

Use **Chrome** (for voice + WebGL). The avatar, voice, and all chart flows work **without** an API key — only free-text chat needs one:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or: ant auth login
```

## Documentation

Full docs are in **[`docs/`](docs/)**:

| Doc | What it covers |
|-----|----------------|
| [docs/README.md](docs/README.md) | Overview + the 60-second version |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | The four layers, tech stack, repo map, swap seam |
| [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) | Intent routing, every visual flow + the math, agent loop, guardrails, voice, avatar |
| [docs/API.md](docs/API.md) | Every endpoint with example requests/responses |
| [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) | How to run + a 3-minute Demo-Day script |
| [docs/screenshots/](docs/screenshots/) | Screenshots of every screen |

Backend specifics: **[backend/README.md](backend/README.md)**.

## How this was built

The original design brief and build prompt live in [`context/`](context/) and [`PROMPT.md`](PROMPT.md) — the "review the spec → plan → build clean code" workflow that produced this. The as-built system is documented in [`docs/`](docs/).

## Project layout

```
.
├── start.sh          one-command launcher
├── docs/             documentation (this is the place to start)
├── context/          original design brief / build prompt
└── backend/          the app: FastAPI + quant engine + agent + web UI + tests
```
