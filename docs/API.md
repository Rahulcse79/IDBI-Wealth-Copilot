# API reference

Base URL: `http://localhost:8000`. All responses are JSON. The quant endpoints need **no API key**; `/api/chat` needs an Anthropic credential.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness check |
| GET | `/api/config` | Whether the copilot is available + model/provider |
| GET | `/api/customers` | List customers (summary) |
| GET | `/api/customers/{id}` | One customer profile |
| GET | `/api/customers/{id}/insights` | Behavioural insights + ranked actions |
| POST | `/api/risk` | Risk-capacity score + explainable factors |
| POST | `/api/goal-plan` | Required SIP, allocation, gap analysis |
| POST | `/api/simulate` | Project a chosen monthly contribution |
| GET | `/api/products?q=` | Catalogue search (TF-IDF) |
| POST | `/api/chat` | Conversational copilot (Claude agent) |

---

### `GET /api/config`
```json
{ "copilot_available": true, "model": "claude-opus-4-8", "data_provider": "mock" }
```

### `GET /api/customers/{id}/insights`
```json
{
  "customer_id": "CUST-DEMO-1",
  "estimated_monthly_income": 95000,
  "savings_rate": 0.359,
  "idle_cash": 487862,
  "monthly_costly_debt": 8500,
  "top_spend_categories": [{ "category": "rent", "monthly_amount": 22000 }],
  "actions": [{ "id": "clear_costly_debt", "title": "Clear high-interest debt first",
               "impact": "high", "evidence": { "monthly_costly_debt": 8500 } }]
}
```

### `POST /api/goal-plan`
Request:
```json
{ "customer_id": "CUST-DEMO-2", "label": "house",
  "target_amount": 5000000, "horizon_years": 8, "current_savings": 600000 }
```
Response (abridged):
```json
{ "bucket": "aggressive", "expected_return_pa": 0.1001,
  "required_monthly": 25879, "inflation_adjusted_target": 3137000,
  "allocation": { "holdings": [
    { "asset_class": "equity", "weight": 0.75, "product_name": "IDBI Nifty 50 Index Fund" },
    { "asset_class": "debt",   "weight": 0.15, "product_name": "IDBI Fixed Deposit" },
    { "asset_class": "gold",   "weight": 0.10, "product_name": "Sovereign Gold Bond (via IDBI)" } ] } }
```

### `POST /api/simulate`
```json
{ "customer_id": "CUST-DEMO-2", "label": "house", "target_amount": 5000000,
  "horizon_years": 8, "monthly_contribution": 25879 }
```
→ `{ "projected_corpus": 5000xxx, "meets_target": true, "surplus_or_gap": ... }`

### `POST /api/risk`
```json
{ "customer_id": "CUST-DEMO-1", "horizon_years": 7, "loss_tolerance": 3, "has_emergency_fund": true }
```
→ `{ "score": 62, "bucket": "balanced", "factors": [{ "factor": "age", "contribution": 7, "note": "…" }] }`

### `POST /api/chat`
Request:
```json
{ "customer_id": "CUST-DEMO-1", "message": "Where should I start?", "history": [] }
```
Response:
```json
{ "answer": "…", "tool_trace": [{ "tool": "get_next_best_actions", "is_error": false }],
  "grounded_products": ["IDBI Fixed Deposit"], "guardrail_triggered": false, "guardrail_violations": [] }
```
If no Anthropic credit is configured, returns **503** with a friendly message; the visual quant flows still work.
