# Demo guide

## Run it

```bash
cd "IDBI Wealth Copilot"
./start.sh                 # sets up the venv, generates data, runs on http://localhost:8000
```

Other modes:
```bash
./start.sh test            # run the 20-test suite
./start.sh setup           # only install deps + generate data
PORT=8078 ./start.sh       # run on a different port if 8000 is busy
```

To enable the **conversational copilot** (free-text chat), add an Anthropic credential before running:
```bash
export ANTHROPIC_API_KEY=sk-ant-...      # or: ant auth login
```
Everything else — the avatar, voice, and all chart flows — works **without** a key.

## Best browser

Use **Chrome** — it has the Web Speech APIs (talk + speak) and WebGL for the 3D avatar.

## 3-minute Demo-Day script

| Time | Do this | Say this (the point) |
|------|---------|----------------------|
| 0:00 | Land on the home screen; the 3D avatar is alive | "Aanya is an avatar-led wealth copilot that lives in the IDBI app — advisory for *every* customer, not just the wealthy." |
| 0:20 | Click **My snapshot** | "She reads the customer's own transactions — income, savings rate, **₹4.9 L sitting idle**, a high-interest EMI — and shows it as charts." |
| 0:50 | Click **Plan ₹50L house**; drag the slider | "Goal planning with a real engine: required SIP, allocation in **real IDBI products**, and a live projection. No guesswork." |
| 1:30 | Click **My risk profile** | "Every score is explained factor by factor — this is the explainability a bank and a regulator need." |
| 1:55 | Press 🎙 and say *"where does my money go"* | "Full voice — she listens, answers, and speaks back." |
| 2:20 | Type *"can you guarantee me 15% returns?"* | "And she **refuses to promise guaranteed returns** — that guardrail is enforced in code and unit-tested, not just a prompt." |
| 2:45 | Toggle light/dark; switch customer | "Production-ready polish, ready to slot into the IDBI mobile app." |

## What to emphasise to bank judges

1. **A real quant engine**, not a chatbot wrapper — every figure is computed and explainable.
2. **Compliance by design** — no guaranteed returns, no invented products; advice only, never executes transactions.
3. **Deployable** — one provider swap from synthetic data to IDBI's sandbox APIs; AWS/ACC-ready.
4. **ROI** — personal wealth advice for every customer at near-zero marginal cost.

## Talking points if asked

- *Why no live chat right now?* The agent path is built and verified; it needs Anthropic API credits on the account. The visual flows demonstrate the full engine without it.
- *Is the data real?* Synthetic, seeded, and reproducible for round 1; the architecture swaps to IDBI sandbox APIs after shortlisting.
