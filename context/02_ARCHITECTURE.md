# 02 · Architecture — IDBI Wealth Copilot

## System overview
```
┌─────────────────────────────────────────────────────────────┐
│  UI shell (Next.js, mobile-style)  +  Avatar (D-ID / Simli)  │  ← Layer 1: front-end
└───────────────────────────────┬─────────────────────────────┘
                                │  REST / WebSocket
┌───────────────────────────────▼─────────────────────────────┐
│  FastAPI backend                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Agent orchestrator (Claude, tool-calling)          │    │  ← Layer 2: reasoning
│  │  + guardrails (grounding, refusal, disclaimers)     │    │  ← Layer 4: trust
│  └───────────┬─────────────────────────┬───────────────┘    │
│              │ tools                    │ retrieval          │
│  ┌───────────▼───────────┐   ┌──────────▼──────────────┐    │
│  │  Quant engine          │   │  Product RAG            │    │  ← Layer 3: moat
│  │  risk / goals /        │   │  (vector search over    │    │
│  │  portfolio             │   │   product catalogue)    │    │
│  └───────────┬───────────┘   └──────────┬──────────────┘    │
└──────────────┼──────────────────────────┼──────────────────┘
               │  data provider interface (mock now → sandbox API later)
┌──────────────▼──────────────────────────▼──────────────────┐
│  Data layer: synthetic customers, transactions, products    │
└─────────────────────────────────────────────────────────────┘
```

## Tech stack (default — change only with reason)
- **Backend:** Python 3.11, FastAPI, Pydantic, Uvicorn.
- **Agent:** Claude via the Anthropic SDK (`anthropic`), tool-calling. Use the latest capable model (Opus / Fable) for the orchestrator.
- **Quant:** NumPy, pandas, scikit-learn, SciPy (optimization).
- **RAG:** sentence-transformers or Anthropic embeddings + FAISS (local) for the product catalogue.
- **Frontend:** Next.js + React + TypeScript, Tailwind. Mobile-first layout that mimics a banking app.
- **Avatar:** D-ID or Simli streaming SDK + TTS (added last; the product must work in text-only mode without it).
- **Infra:** Docker; deploy on AWS (the contest provides AWS + ACC credits — use and cite them). `.env` for secrets.

## The swap seam (critical design rule)
Every external dependency goes through an interface with two implementations:
- `MockProvider` — reads the synthetic datasets (used for round 1).
- `SandboxProvider` — calls IDBI's sandbox APIs (wired in after Jul 22 shortlisting).
Selected via env var (`DATA_PROVIDER=mock|sandbox`). Code above this seam never knows which is active.

## Agent tools (functions the LLM can call)
- `get_customer_profile(customer_id)` → demographics, accounts, balances.
- `get_transactions(customer_id, months)` → categorized transaction history.
- `assess_risk(customer_id, questionnaire)` → risk score + bucket (conservative / balanced / aggressive).
- `plan_goal(customer_id, goal)` → required monthly investment, allocation, gap analysis.
- `simulate(customer_id, plan, change)` → "what-if" projection.
- `search_products(query, filters)` → grounded product matches from the catalogue (RAG).
- `get_next_best_actions(customer_id)` → behavior-mined nudges (idle cash, costly debt, under-insured).

The agent must answer customer questions **only** by composing these tools. Any number it states must come from a tool result.

## Guardrails (Layer 4, enforced in code, not just prompts)
- No product, return, or fee may appear unless it came from `search_products` / catalogue data.
- On requests for guaranteed returns: refuse, explain risk, offer grounded alternatives.
- Every recommendation response includes a machine-attached "why" (the tool outputs / data points used).
- Append the standard advisory disclaimer; never claim to execute transactions.

## Suggested repo structure
```
backend/
  app/
    agent/        orchestrator, tool definitions, guardrails
    quant/        risk.py, goals.py, portfolio.py, nudges.py
    rag/          index build + search over product catalogue
    providers/    base.py, mock.py, sandbox.py  (the swap seam)
    api/          FastAPI routers
    models/       Pydantic schemas
  data/           synthetic generators + sample datasets
  tests/
frontend/
  app/            Next.js mobile-style UI + avatar
infra/            Dockerfile, deploy notes
```
