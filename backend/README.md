# IDBI Wealth Copilot — backend

An avatar-led, agentic, explainable AI wealth advisor for IDBI Innovate 2026 (Track 01).
FastAPI backend + Claude tool-calling agent + a pure-Python quant engine, serving a 3D,
voice-enabled, chart-rich web UI. Runs entirely on synthetic data; the conversational
copilot adds an Anthropic key.

> Full documentation is in [`../docs/`](../docs/) — start with [docs/HOW_IT_WORKS.md](../docs/HOW_IT_WORKS.md).

## Quick start

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# (optional) generate a fresh dataset — the app also auto-generates on first run
python -m data.generate --seed 20260617 --n-customers 40 --months 18

pytest                          # 20 tests, no API key needed
uvicorn app.main:app --reload   # open http://127.0.0.1:8000
```

To enable the conversational copilot:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or: ant auth login
```

The avatar, voice, and all chart flows (snapshot, goal plan, risk, products) work
**without** a key — they call the quant engine directly. Free-text chat uses the agent.

## Architecture

| Layer | Where | What |
|------|-------|------|
| Data | `data/` | Seeded synthetic customers/transactions + the product catalogue (RAG ground truth) |
| Providers | `app/providers/` | `mock` now → `sandbox` (IDBI API) later, behind one interface (`WEALTH_DATA_PROVIDER`) |
| Quant engine | `app/quant/` | Risk, portfolio, goal planning, behavioural insights — pure functions, the moat |
| RAG | `app/rag/` | Offline TF-IDF retriever over the catalogue |
| Agent | `app/agent/` | Claude (`claude-opus-4-8`) tool-calling loop, prompt, compliance guardrails |
| API + UI | `app/api/`, `app/main.py`, `web/` | FastAPI JSON API + 3D/voice/chart UI |

## Web UI (`web/`)

- `avatar.js` — Three.js 3D AI avatar, voice-reactive, WebGL fallback.
- `app.js` — chat + **intent routing** (data questions → Chart.js charts; else LLM), Web Speech voice (talk + speak), light/dark theme.
- `styles.css` / `index.html` — single-screen two-pane layout, glassmorphism, responsive.

No Node build step — the UI is static files served by FastAPI (so it runs on any Python box).

## Key endpoints

- `GET  /api/customers` · `GET /api/customers/{id}` · `GET /api/customers/{id}/insights`
- `POST /api/risk` · `POST /api/goal-plan` · `POST /api/simulate`
- `GET  /api/products?q=` · `POST /api/chat` · `GET /api/config`

See [docs/API.md](../docs/API.md) for request/response examples.

## The two things that make this win

1. **A real quant engine**, not a chatbot wrapper — every figure is computed and explainable.
2. **Guardrails in code** (`app/agent/guardrails.py`, unit-tested) — the copilot can never
   promise guaranteed returns or cite a product it didn't look up.

## Configuration (env, prefix `WEALTH_`)

`WEALTH_MODEL` (default `claude-opus-4-8`), `WEALTH_EFFORT` (`medium`),
`WEALTH_DATA_PROVIDER` (`mock`), `WEALTH_SEED` (`20260617`). The Anthropic key is read
from the environment or `backend/.env`.
