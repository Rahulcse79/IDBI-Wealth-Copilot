# 03 · Dataset specifications — IDBI Wealth Copilot

The contest provides synthetic datasets (transactions, MSME financials, UPI patterns) at the Jun 17 orientation. Until then, generate our own synthetic data matching these schemas so the whole pipeline runs day one. Keep generation **deterministic** (fixed seed) for reproducibility.

## 1. Customer profile (`customers`)
| field | type | notes |
|-------|------|-------|
| customer_id | str | primary key, e.g. `CUST00001` |
| name | str | synthetic |
| age | int | 21–65 |
| city | str | Indian cities |
| occupation | enum | salaried / self_employed / business |
| monthly_income | int (₹) | estimated, not always known |
| dependents | int | 0–4 |
| accounts | list | savings/current balances |
| existing_investments | list | {type, value} |
| risk_appetite | enum\|null | filled after questionnaire |

## 2. Transactions (`transactions`)
| field | type | notes |
|-------|------|-------|
| txn_id | str | primary key |
| customer_id | str | FK |
| date | date | last 12–24 months |
| amount | float (₹) | signed: debit negative, credit positive |
| type | enum | upi / card / neft / ach / cash / interest |
| merchant | str | synthetic |
| category | enum | salary / rent / groceries / dining / utilities / emi / investment / entertainment / transfer / fees |
| balance_after | float | running balance |

Categories drive the behavioral insights (idle cash, costly EMIs, savings rate, income estimation).

## 3. Product catalogue (`products`) — the RAG ground truth
| field | type | notes |
|-------|------|-------|
| product_id | str | primary key |
| name | str | real IDBI-style products: FD, RD, mutual funds, ULIP, pension, insurance |
| category | enum | fixed_deposit / mutual_fund / insurance / pension / govt_scheme |
| risk_level | enum | low / medium / high |
| indicative_return | str | e.g. "6.5% p.a." — ALWAYS quoted as indicative, never guaranteed |
| min_investment | int (₹) | |
| lock_in | str | tenure / lock-in |
| description | str | used for vector embedding |
| disclaimer | str | mandatory text |

**Rule:** every recommendation the copilot makes must reference a `product_id` from this table. No off-catalogue products.

## 4. Financial goals (`goals`)
| field | type | notes |
|-------|------|-------|
| goal_id | str | |
| customer_id | str | FK |
| label | str | "house", "child education", "retirement" |
| target_amount | int (₹) | |
| horizon_years | int | |
| current_savings | int (₹) | already set aside |

## 5. Risk questionnaire (`risk_questionnaire`)
A short set of weighted questions (income stability, investment horizon, loss tolerance, experience) → numeric risk score → bucket. Document the scoring rubric in `quant/risk.py`.

## Synthetic data generator requirements
- One module, `data/generate.py`, seeded (`--seed`), `--n-customers`, `--months`.
- Produce internally consistent data: balances reconcile with transactions; income inferable from salary credits; some customers deliberately have idle cash / costly EMIs / under-insurance so the demo flows have something to find.
- Output to `data/synthetic/*.parquet` (or csv) + a small `demo_customers.json` of 3 hand-tuned personas for the demo flows.
