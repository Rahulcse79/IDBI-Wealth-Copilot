# 05 · Build requirements & acceptance criteria — IDBI Wealth Copilot

## Round-1 goal (by Jul 9, 2026)
A deployed, demoable MVP running on synthetic data + mock APIs that performs the three demo flows convincingly, plus a 2–3 min demo video, pitch deck, and repo.

## Functional requirements

### FR-1 — Conversational copilot
- Accepts text (and later voice) input, responds as the avatar/banker persona.
- Maintains conversation context within a session.
- Answers only by composing the agent tools; never fabricates data.

### FR-2 — Behavioral insight (Demo flow 1)
- From a customer's transactions, compute: monthly savings rate, idle-cash estimate, costly-debt/EMI flags, estimated income, top spend categories.
- Surface a ranked "next best actions" list with the underlying data points.
- **Acceptance:** for demo persona A, the copilot identifies idle savings and a high-interest debt and proposes a concrete starter plan, showing the numbers it used.

### FR-3 — Goal-based planning (Demo flow 2)
- Given a goal (target amount, horizon), compute required monthly investment, recommended asset allocation (tied to risk bucket), and gap vs. current trajectory.
- Support a live "what-if" (change monthly amount or horizon → updated projection).
- **Acceptance:** for "₹50L in 8 years," the copilot returns a required SIP, an allocation across catalogue products, a gap analysis, and updates instantly when the user changes the monthly contribution.

### FR-4 — Grounded recommendations + guardrails (Demo flow 3)
- All recommended products come from the catalogue via RAG, with indicative (never guaranteed) returns and disclaimers.
- On a request for a guaranteed return, the copilot refuses, explains risk, and offers grounded alternatives.
- **Acceptance:** the guardrail validator blocks any output containing an off-catalogue product or a "guaranteed return"; this is covered by a unit test.

### FR-5 — Explainability
- Every recommendation can show "why": the data points and tool outputs behind it.
- **Acceptance:** the UI has a visible "why this?" affordance on each recommendation.

## Non-functional requirements
- **Latency:** a copilot turn returns in a few seconds; show a thinking/streaming state.
- **Reproducibility:** seeded synthetic data; documented setup runs end-to-end on a clean machine.
- **Deployability:** containerized; deployable to AWS; mock→sandbox provider swap via env var.
- **Multilingual (stretch):** English + at least one Indian language in the UI/voice.

## Round-1 deliverables checklist
- [ ] Deployed prototype (URL) + public/Git repo.
- [ ] 2–3 min demo video covering all three flows.
- [ ] Pitch deck (problem → solution → architecture → AI/data approach → quantified business impact → deployability → roadmap).
- [ ] One-pager mapping the solution to IDBI's stated expected outcome.

## Acceptance metrics for the demo (what we'll point judges to)
- 3/3 demo flows run live, no faked answers.
- Guardrail visibly prevents an ungrounded/guaranteed-return claim.
- A quantified ROI slide (advisory reach, cost-per-advised-customer → ~0, cross-sell uplift).

## Explicitly out of scope for round 1
Real bank-system integration (sandbox unlocks Jul 22 only after shortlisting), real money movement, KYC/account opening, trade execution. The copilot advises; it never transacts.
