# Architecture

![Architecture](architecture.svg)

The system is four layers. Everything above the provider seam is independent of where the data comes from, so the round-1 build runs entirely on synthetic data and can later point at IDBI's sandbox APIs by flipping one environment variable.

## Layer 1 — Browser UI (`backend/web/`)

A single-page app served as static files by FastAPI — **no Node build step**, so it runs anywhere Python runs (the build machine had Node 16, too old for modern Next.js).

| File | Responsibility |
|------|----------------|
| `index.html` | Two-pane layout: 3D avatar (left), conversation (right), top bar with online status / customer selector / theme toggle |
| `styles.css` | Dark + light themes via CSS variables, glassmorphism, responsive |
| `avatar.js` | Three.js 3D AI avatar — idle/listening/thinking/speaking states, voice-reactive, WebGL fallback to a CSS orb |
| `app.js` | Chat, **intent routing**, Chart.js visualisations, Web Speech voice (talk + speak), theme persistence |

## Layer 2 — FastAPI (`backend/app/api/`, `backend/app/main.py`)

A thin JSON API plus the static-file mount. The **quant endpoints run fully offline** on synthetic data (no API key); only `/chat` needs an Anthropic credential. See [API.md](API.md).

## Layer 3 — The engine (`backend/app/quant/`, `backend/app/agent/`, `backend/app/rag/`)

- **Quant engine (the moat)** — `risk.py`, `goals.py`, `portfolio.py`, `insights.py`. Pure functions over typed inputs; every financial assumption is a named constant in `constants.py`. Unit-tested.
- **Product RAG** — `rag/retriever.py`, a dependency-free TF-IDF index over the product catalogue. Grounds every recommendation.
- **Agent + trust** — `agent/orchestrator.py` runs a manual Claude (`claude-opus-4-8`) tool-calling loop; `agent/tools.py` exposes the quant engine + RAG as typed tools; `agent/guardrails.py` validates the final answer (no guaranteed returns, no ungrounded products) and is unit-tested.

## Layer 4 — Data (`backend/app/providers/`, `backend/data/`)

- `providers/base.py` defines the `DataProvider` interface; `mock.py` reads the seeded synthetic dataset; a future `sandbox.py` implements the same methods against IDBI APIs.
- `data/generate.py` produces deterministic synthetic customers + transactions (with three hand-tuned demo personas); `data/catalogue.py` is the product catalogue that is the RAG ground truth.

## The swap seam

```
WEALTH_DATA_PROVIDER=mock      # round 1 — synthetic data (default)
WEALTH_DATA_PROVIDER=sandbox   # after shortlisting — IDBI sandbox APIs
```

`providers/factory.py` returns the configured provider. Nothing above this line knows or cares which is active — that's what makes the round-1 prototype "deployable-looking" to a bank.

## Repo map

```
IDBI Wealth Copilot/
├── start.sh                    one-command launcher (run | test | setup)
├── docs/                       this documentation
├── context/                    the original design brief / build prompt
└── backend/
    ├── app/
    │   ├── main.py             FastAPI app (+ serves web/)
    │   ├── config.py           settings + .env loader
    │   ├── api/routes.py       all HTTP endpoints
    │   ├── models/             Pydantic domain + API schemas
    │   ├── providers/          mock → sandbox swap seam
    │   ├── quant/              risk · goals · portfolio · insights  (the moat)
    │   ├── rag/                TF-IDF product retriever
    │   └── agent/              Claude loop · tools · prompts · guardrails
    ├── data/                   synthetic generator + product catalogue
    ├── web/                    the UI (avatar · voice · charts · chat)
    └── tests/                  20 tests (quant + guardrails + API)
```

## Tech stack

Python 3.9 · FastAPI · Pydantic v2 · Anthropic SDK (`claude-opus-4-8`) · Three.js · Chart.js · Web Speech API. Minimal dependencies and pure-Python quant/RAG so it runs reproducibly on a clean machine.
