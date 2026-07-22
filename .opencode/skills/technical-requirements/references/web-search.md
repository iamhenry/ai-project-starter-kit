# Web Search Guidance

Verbatim adaptive retrieval guidance from technical-requirements Phase 2.

---

## WEB SEARCH GUIDANCE

Use adaptive retrieval. Not every answer requires verification.

1. **When to retrieve evidence:**
   - Claims about API docs/SDK behavior, auth/security rules, pricing/free tiers, quotas/rate limits, compliance, or version-specific implementation
   - Any claim with medium/low confidence
   - Any claim where being wrong causes user trust loss, rework, or security risk

2. **When retrieval is optional:**
   - Preference-only choices (naming, UX style, sequencing) that do not depend on external facts

3. **Source quality order:**
   - Official docs first
   - Then maintainer docs/repo/changelog
   - Then recent community sources for supporting context

4. **Retrieval levels:**
   - No verification: proceed directly
   - Quick check: 1 official source
   - Deep check: 2+ sources, include official docs, spawn focused subagents when useful
   - Prefer subagent retrieval for fast-changing facts (pricing, limits, SDK/API behavior)

5. **Output requirements (when retrieval used):**
   - Include source URL, accessed date, and version/date context
   - If evidence is stale/weak, say so explicitly
   - If sources conflict, show disagreement, choose conservative default, and note follow-up validation
