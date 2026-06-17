# 01 · Product spec — IDBI Wealth Copilot

## One-liner
A personal AI wealth manager for every IDBI customer, at near-zero marginal cost — an avatar-led copilot inside the bank's mobile app that gives bank-grade, personalized, explainable investment advice grounded in the customer's own financial behavior.

## The problem (from IDBI's Track 01 statement)
Wealth management and advisory remain fragmented and inaccessible to most customers. The bank lacks a comprehensive view of customer investment behavior and spending habits, which limits its ability to give timely, personalized, data-driven guidance.

## Expected outcome (what IDBI asked for)
An AI-powered digital wealth-management (avatar-based) application that integrates into the bank's mobile app and delivers personalized, scalable wealth advisory through an intuitive interface.

## Who it's for
Mass-market and mass-affluent retail customers who would never get a human relationship manager — salaried young professionals, first-time investors, families planning big goals.

## The product in four layers
1. **Conversational avatar front-end** — voice + chat, multilingual (English + Hindi/regional). Feels like a video call with a personal banker. This is the wow factor.
2. **Agentic reasoning layer** — an LLM (Claude) that uses *tools* to fetch data and run calculations; it orchestrates, it does not free-style answers.
3. **Quant engine** — risk profiling, goal-based planning, and portfolio construction computed from the customer's transaction data. **This is the moat.**
4. **Trust & compliance layer** — explainable recommendations (always show "why"), grounded product references, and guardrails that refuse to invent returns.

## The three demo flows (the product is designed around these)
1. **"I'm new, where do I start?"** — Copilot reads the customer's transactions, spots idle savings and costly debt, and proposes a starter plan, showing the data it used.
2. **"Help me buy a house in 8 years."** — Live goal-based planning: required monthly SIP, asset allocation, gap analysis, and a "what if I add ₹5k/month" simulation.
3. **"Is this advice safe?"** — Customer asks for a guaranteed return; the copilot refuses to invent a number, cites only real catalogue products, and shows the disclaimer/guardrail.

## What "winning" looks like
- A polished 2–3 minute demo video showing all three flows.
- A product that *looks deployable inside IDBI's app* (mobile-style UI, AWS-hosted, sandbox-API-ready).
- A clear ROI story: advisory reach ×N, cross-sell uplift, cost-per-advised-customer → near zero.

## Scope guardrails
- **In scope (round 1, by Jul 9):** the three demo flows on synthetic data + mock APIs.
- **Out of scope (round 1):** real bank integration (only after shortlisting unlocks the sandbox on Jul 22), real money movement, account opening, trade execution. The copilot advises; it never transacts.
