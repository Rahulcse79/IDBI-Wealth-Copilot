# Deploy to Zoho Catalyst (same pattern as KSP)

This `catalyst/` folder is a **static build** of the IDBI Wealth Copilot — the quant
engine is ported to client-side JS (`client/static-api.js`) with pre-baked data
(`client/static-data.js`), so it runs with **no backend**, exactly like the KSP site.

> The Catalyst CLI is interactive (it needs a real terminal), so run these **3 steps in
> your own Terminal** — they can't be automated from the agent.

## Steps

```bash
cd "/Users/rahulsingh/Desktop/IDBI Wealth Copilot/catalyst"

# 1. Create a NEW Catalyst project for this app (do NOT reuse KSP).
catalyst init
#    → when prompted:
#      • "Create a new project"  → name it: IDBI-Wealth-Copilot
#      • Select feature: Client (web client hosting) only
#      • It detects client/ as the client source (catalyst.json already set)

# 2. Deploy.
catalyst deploy

# 3. The CLI prints the hosting URL when it finishes — that's your DEPLOYMENT LINK.
```

## Your deployment link

After `catalyst deploy`, the link looks like KSP's, e.g.:

```
https://idbi-wealth-copilot-<env-id>.development.catalystserverless.in/
```

You can also find it in the **Catalyst console → your project → Web Client Hosting**.
Paste that link into:
- the Prototype Submission Deck, slide 14 (Final Product Link), and
- the hackathon submission form ("Final Product Link").

## Notes
- **What works live:** the 3D avatar, voice, and all quick-action/chart flows
  (snapshot, spending, goal plan, retirement, risk, products) — fully client-side.
- **Live free-text chat** stays disabled on the static site (it needs the Anthropic
  backend); typing a question shows the "use the quick actions" message. To enable it
  later, host the Python backend on Catalyst AppSail and point `app.js` at it.
- If `catalyst init` asks for a data center, pick the same one as your KSP project (`in`).
- Re-deploy after any change with `catalyst deploy`.
```
