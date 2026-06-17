# Master prompt — IDBI Wealth Copilot

> Paste this prompt into Claude Code (or Claude) **with the five `context/` files attached / open in the project**.
> It follows the "plan first, then build clean reproducible code" workflow. Do not let the model skip the planning step.

---

## The prompt

You are my senior engineering partner building **IDBI Wealth Copilot**, our entry for the IDBI Innovate 2026 hackathon (Track 01 — Wealth Advisory). We are aiming for 1st place (₹2L). Judges are bank business heads, so they reward clear ROI, a working demo, explainability/compliance, and deployability — not raw model accuracy.

**Step 1 — Read everything first.**
Before writing any code, read these context files completely and tell me, in 3–4 bullets, what you understood the product, the data, and the constraints to be:
- `context/01_PRODUCT_SPEC.md` — what we're building and why
- `context/02_ARCHITECTURE.md` — the 4-layer architecture and tech stack
- `context/03_DATASET_SPECIFICATIONS.md` — the data schemas we build on
- `context/04_CODE_QUALITY_GUIDE.md` — the coding style you MUST follow
- `context/05_BUILD_REQUIREMENTS.md` — functional requirements + acceptance criteria

**Step 2 — Propose a plan. Do NOT write code yet.**
Produce a detailed, multi-stage build plan covering, in this order:
1. Synthetic data layer (schemas, generator, loaders)
2. Quant engine (risk profiling, goal-based planning, portfolio model) — *this is our moat, build it first*
3. Product RAG (grounding recommendations in a real product catalogue)
4. Agent layer (Claude tool-calling orchestrator + guardrails)
5. API layer (FastAPI, mock endpoints designed to be swapped for the bank's sandbox later)
6. UI shell (Next.js mobile-style app) and, last, the avatar integration

For each stage list: the files you'll create, the key functions, and how we'll verify it works.

**Step 3 — Ask before you build.**
Present the plan and ask me clarifying questions on anything genuinely ambiguous — especially: the exact data schema fields, which models/algorithms to use for risk and portfolio, acceptance metrics for each demo flow, and the LLM guardrail rules. Recommend a default for each so I can just say "yes."

**Step 4 — Build, after I approve.**
Once I approve the plan, implement it as a **clean, reproducible MVP** that strictly follows `context/04_CODE_QUALITY_GUIDE.md`. Start with the quant engine and the agent tool layer. Include:
- full docstrings and a runnable `README` with setup steps
- deterministic synthetic-data seeding so results reproduce
- tests for the quant engine and the guardrails (the AI must never state an ungrounded return figure)
- the three demo flows in `05_BUILD_REQUIREMENTS.md` working end to end

Work in small, reviewable increments. After each stage, stop, show me what you built and how to run it, and wait for my go-ahead. We'll refine the methodology together.

---

### House rules for this build
- Never invent financial returns, fees, or product names — everything a customer sees must trace back to data in the product catalogue. Show the "why" behind every recommendation.
- Design every external call (customer data, products, market data) as a swappable interface: a `mock` implementation now, the bank's sandbox API later. Keep that seam clean.
- Optimize for a convincing 3-minute demo and a deployable-looking product over leaderboard accuracy.
