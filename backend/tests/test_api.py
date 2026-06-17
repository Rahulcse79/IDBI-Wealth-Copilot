from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_customers_include_demo_personas():
    ids = {c["customer_id"] for c in client.get("/api/customers").json()}
    assert {"CUST-DEMO-1", "CUST-DEMO-2", "CUST-DEMO-3"} <= ids


def test_insights_endpoint():
    resp = client.get("/api/customers/CUST-DEMO-1/insights")
    assert resp.status_code == 200
    body = resp.json()
    assert body["idle_cash"] > 0
    assert body["monthly_costly_debt"] == 8500


def test_goal_plan_endpoint():
    resp = client.post(
        "/api/goal-plan",
        json={
            "customer_id": "CUST-DEMO-2",
            "label": "house",
            "target_amount": 5_000_000,
            "horizon_years": 8,
            "current_savings": 600_000,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["required_monthly"] > 0
    assert body["allocation"]["holdings"]  # grounded products attached


def test_products_search():
    resp = client.get("/api/products", params={"q": "retirement pension"})
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()["products"]}
    assert any("NPS" in n or "PPF" in n or "Pension" in n for n in names)


def test_unknown_customer_404():
    assert client.get("/api/customers/NOPE").status_code == 404


def test_chat_requires_credential(monkeypatch):
    # Hermetic: ensure no key so we exercise the graceful 503, never the live API.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    resp = client.post(
        "/api/chat",
        json={"customer_id": "CUST-DEMO-1", "message": "Where should I start?", "history": []},
    )
    assert resp.status_code == 503
