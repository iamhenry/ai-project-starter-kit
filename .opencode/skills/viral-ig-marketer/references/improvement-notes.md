# Improvement Notes

Append-only log of issues, observations, and improvement suggestions from each cycle.

---

## 2026-03-17 — Cycle 2

- **Cold start problem**: With 2 followers, no content experiment yields useful data. The skill assumes some minimum distribution exists. Suggestion: add a "Cycle 0.5" step for new accounts — manual engagement strategy (commenting in niche, following relevant accounts from the phone) before content experiments begin. Without this, we're burning cycles producing content nobody sees.
- **Telegram media sending**: The `openclaw message send --media` command takes ~5-8 seconds per image due to CLI initialization overhead. For 7 slides, this means ~45-60 seconds of sending. Consider batching or a dedicated media-upload command. Worked around by splitting into two batches.

## 2026-03-17 — Health Check (22:00 UTC)

- **Instagram Graph API**: ✅ Working. @zeroproofapp, 2 followers.
- **RevenueCat API**: ⚠️ Service-side issue (HTTP/2 PROTOCOL_ERROR on /metrics/overview). Not auth-related. Endpoint unreachable. Likely temporary API issue on RevenueCat side.
- **agent-browser Instagram session**: ❌ Logged out. Browser shows Instagram login wall. Cookies expired or invalid. Requires manual re-auth (Henry login via browser).
- **Remotion test run**: ✅ Pipeline working end-to-end. seedream v5 lite (portrait_4_3) → Remotion render → output. New paths verified.
