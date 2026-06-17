# 04 · Code quality guide — IDBI Wealth Copilot

Follow this style for everything. The goal is **clean, reproducible, demo-ready, judge-readable** code — not cleverness.

## General principles
- Readability over cleverness. A bank judge may skim the repo.
- Small, single-purpose functions. Pure functions in the quant engine (input → output, no hidden state).
- Reproducible: every random process takes a `seed`. Same seed → same result, every run.
- Fail loudly with clear messages; never silently swallow errors.

## Python (backend, quant, agent)
- Python 3.11, type hints on every function signature.
- Format with `black`, lint with `ruff`. Imports sorted.
- Data models are Pydantic v2 classes in `app/models/` — no loose dicts crossing module boundaries.
- Docstrings (Google style) on every public function: what, args, returns, and *why* for any non-obvious finance logic.
- No magic numbers — name constants (e.g. `EQUITY_EXPECTED_RETURN = 0.11`) and cite the assumption in a comment.
- Tests with `pytest`. The quant engine and guardrails must have unit tests. Aim for the critical paths, not 100% coverage theatre.

## Agent / LLM code
- All prompts live in `app/agent/prompts/` as named template files — never inline scattered strings.
- Tool definitions are typed and documented; the model only ever sees tools, never raw DB access.
- **Guardrails are code, not vibes:** a post-processing validator checks that any product/return/fee in the model's output traces to a tool result, and blocks/rewrites it otherwise. This validator is unit-tested.
- Never hardcode API keys. Read from `.env` via `pydantic-settings`. Commit a `.env.example`.
- Log every tool call and its inputs/outputs (redact PII) so the demo can show "the AI's reasoning trail."

## Frontend (Next.js / TypeScript)
- TypeScript strict mode. Components small and typed. Tailwind for styling.
- Mobile-first: design at 390px width (a phone) — this is a banking app, not a desktop dashboard.
- Keep API calls in a typed client module; no fetch scattered in components.
- The UI must work in text-only mode if the avatar service is down (graceful degradation for the demo).

## Project hygiene
- `README.md` at repo root: one-command setup, how to seed data, how to run backend + frontend, how to run the demo.
- `requirements.txt` / `pyproject.toml` and `package.json` pinned.
- `.gitignore` covers `.env`, data outputs, `__pycache__`, `node_modules`.
- Conventional, descriptive commit messages. Small commits over giant ones.
- Every module that does finance math has a comment block stating its assumptions (expected returns, inflation, etc.) — judges will ask.

## What NOT to do
- No notebooks as the deliverable — notebooks are for exploration only; ship modules.
- No hardcoded demo answers faked to look like AI. The demo must be the real system running.
- No off-catalogue financial products, no invented guaranteed returns — anywhere, ever.
