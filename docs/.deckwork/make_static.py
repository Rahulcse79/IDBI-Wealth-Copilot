#!/usr/bin/env python
"""Generate a static (no-backend) build of the Wealth Copilot for Catalyst client hosting.

Bakes the quant data straight from the Python engine (no server) into static-data.js,
copies the web UI into catalyst/client/, wires the static API shim, and writes the
Catalyst project config — mirroring the KSP static-hosting pattern.
"""

import json
import os
import re
import shutil
import sys

ROOT = "/Users/rahulsingh/Desktop/IDBI Wealth Copilot"
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.providers import get_provider
from app.quant.insights import analyze
from data.catalogue import all_products

WEB = os.path.join(ROOT, "backend", "web")
CAT = os.path.join(ROOT, "catalyst")
CLIENT = os.path.join(CAT, "client")

provider = get_provider()
customers = provider.list_customers()


def current_sip(customer_id):
    txns = provider.get_transactions(customer_id, months=12)
    months = {t.date[:7] for t in txns} or {"_"}
    invested = sum(-t.amount for t in txns if t.category == "investment")
    return invested / len(months)


data = {
    "config": {"copilot_available": False, "model": "claude-opus-4-8", "data_provider": "static"},
    "customers": [
        {"customer_id": c.customer_id, "name": c.name, "age": c.age, "city": c.city, "occupation": c.occupation}
        for c in customers
    ],
    "byId": {},
    "insights": {},
    "customerSIP": {},
    "catalogue": [p.model_dump() for p in all_products()],
}
for c in customers:
    data["byId"][c.customer_id] = c.model_dump()
    txns = provider.get_transactions(c.customer_id, months=18)
    data["insights"][c.customer_id] = analyze(c, txns).model_dump()
    data["customerSIP"][c.customer_id] = round(current_sip(c.customer_id))

# ---- assemble catalyst/client ----
os.makedirs(CLIENT, exist_ok=True)
for f in ("index.html", "styles.css", "app.js", "avatar.js"):
    shutil.copy(os.path.join(WEB, f), os.path.join(CLIENT, f))

with open(os.path.join(CLIENT, "static-data.js"), "w") as fh:
    fh.write("window.__WC_DATA__ = " + json.dumps(data, separators=(",", ":")) + ";\n")

# patch index.html: add static-data.js + static-api.js before app.js
idx_path = os.path.join(CLIENT, "index.html")
idx = open(idx_path).read()
idx = idx.replace(
    '<script src="/avatar.js"></script>\n    <script src="/app.js"></script>',
    '<script src="/static-data.js"></script>\n'
    '    <script src="/static-api.js"></script>\n'
    '    <script src="/avatar.js"></script>\n    <script src="/app.js"></script>',
)
open(idx_path, "w").write(idx)

# patch app.js api(): route through the static shim when present
app_path = os.path.join(CLIENT, "app.js")
app = open(app_path).read()
app = app.replace(
    "async function api(path, opts) {\n  const res = await fetch(path, opts);",
    "async function api(path, opts) {\n  if (window.__WC_API__) return window.__WC_API__(path, opts);\n  const res = await fetch(path, opts);",
)
open(app_path, "w").write(app)

# client-package.json + catalyst.json (KSP pattern)
open(os.path.join(CLIENT, "client-package.json"), "w").write(
    json.dumps({"name": "idbi-wealth-copilot-client", "version": "1.0.0", "homepage": "index.html"}, indent=2)
)
open(os.path.join(CAT, "catalyst.json"), "w").write(
    json.dumps({"project_name": "IDBI-Wealth-Copilot", "client": {"source": "client"}}, indent=2)
)

print("customers:", len(data["customers"]))
print("client files:", sorted(os.listdir(CLIENT)))
print("api() patched:", "window.__WC_API__" in open(app_path).read())
print("index wired:", "static-api.js" in open(idx_path).read())
