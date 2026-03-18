# App Intelligence Feedback

Append-only. Written during each cycle's analytics review — only when the diagnostic quadrant shows high views + flat MRR. Skip entirely if that signal is absent.

**Trigger conditions (write when ANY of these apply):**
- Views are high but MRR is flat → possible misalignment between Instagram content and app value prop / onboarding
- Winning Instagram content angles are not reflected in App Store screenshots or description
- RevenueCat shows trial-to-paid drop-off → onboarding clarity issue
- Content referencing a feature that the app doesn't clearly surface in its UX
- Any UX signal that could explain a conversion gap

**Do NOT write padding entries.** If nothing concrete to report this batch, skip.

**Sources the agent should consult before writing:**
- GitHub repo: read via gitingest CLI (cached in `references/app-brief.md` — refresh monthly or when codebase changes)
- App Store listing: browse via agent-browser (`app.appStoreUrl` in `references/config.json`)
- RevenueCat funnel: already pulled in Step 1 analytics
- Support notes: `references/config.json` → `app.supportNotes` (optional — fill if user provides)

**Feedback categories:**
- `copy-misalignment` — Instagram message vs app description diverge
- `onboarding-signal` — trial-to-paid drop suggests unclear onboarding
- `app-store-gap` — screenshots / description miss the winning content angle
- `ux-signal` — UX behavior hinting at friction or missing feature
- `retention-hypothesis` — churn pattern + possible cause

**Format:**
```
## [YYYY-MM-DD] Batch N
Category: [category]
Signal: [what data showed this]
Observation: [concrete finding]
Suggestion: [actionable change for the human to consider]
```

---

<!-- Agent entries begin below this line -->
