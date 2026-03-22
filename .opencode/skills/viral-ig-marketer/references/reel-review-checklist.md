# Reel Review Checklist (QA Gate)

Deterministic checklist for reviewing reel drafts before they reach Henry.
Every item is pass/fail. **All items must pass** before moving an issue to `in_review`.

## How to Use

Run this checklist against the reel's Paperclip issue (description + attachments).
Mark each item ✅ or ❌. If any item fails, add a comment with the specific failures
and move the issue back to `in_progress` with the assignee who produced it.

Do not apply judgment calls — if the answer to the question isn't clearly "yes," it fails.

---

## 1. Production Completeness

| # | Check | What to verify |
|---|---|---|
| 1.1 | **Video exists** | A rendered `.mp4` file is attached or its path is referenced and the file exists on disk. `render-instructions.md` alone is an automatic fail. |
| 1.2 | **Video format correct** | 9:16 vertical, 1080×1920, `.mp4` container |
| 1.3 | **Video duration ≤ 90s** | Under Instagram's recommended Reel length for algorithmic push |
| 1.4 | **No watermarks** | No TikTok, CapCut, or other platform watermarks (Instagram tanks reach for these) |
| 1.5 | **Caption exists** | Full caption text is present in the issue description or a `caption.txt` file |
| 1.6 | **Posting date specified** | Issue description includes a clear posting date |

## 2. Caption Structure (per caption-guide.md)

| # | Check | What to verify |
|---|---|---|
| 2.1 | **Hook line ≤ 125 chars** | First line of caption is ≤ 125 characters (Instagram truncation point) |
| 2.2 | **Hook line has no emojis** | No emojis in the first line (per caption guide: reduces perceived seriousness in wellness niche) |
| 2.3 | **Body present (2-4 sentences)** | Caption has a body section between the hook and CTA |
| 2.4 | **Emotional register matches format** | Body tone matches the reel format (T1=light, T4=direct/factual, P3=educational) |
| 2.5 | **Single CTA** | Exactly one call-to-action, not multiple competing CTAs |
| 2.6 | **CTA type is appropriate** | CTA matches a type from the guide: DM share, comment keyword, save, engagement, or link |
| 2.7 | **Hashtags: 3-5 total** | Between 3 and 5 hashtags, inclusive |
| 2.8 | **No overly broad hashtags** | No generic tags like #motivation, #wellness, #inspiration (dilutes reach) |
| 2.9 | **Hashtags after CTA** | Hashtags are placed after the CTA, separated by a line break |
| 2.10 | **No hashtag starts the caption** | Caption does not begin with a hashtag |

## 3. Virality Gate (per virality-model.md)

| # | Check | What to verify |
|---|---|---|
| 3.1 | **Virality score ≥ 4** | The concept scored 4+ on the 5-question gate (documented in results.jsonl or issue) |
| 3.2 | **Hook tension** | First 3 seconds create tension, surprise, or ask a question the viewer is already wondering |
| 3.3 | **Specificity** | Topic is specific enough that someone in the sobriety niche thinks "this is exactly about me" |
| 3.4 | **Emotional resonance** | Content makes someone feel understood/validated/motivated — not just informed |
| 3.5 | **Sendable** | Would someone DM this to a friend? ("You need to see this" factor) |
| 3.6 | **Watchable** | Pacing is tight, no dead time, viewer will watch to the end |

## 4. Brand & Content Rules

| # | Check | What to verify |
|---|---|---|
| 4.1 | **No competitor trademarks** | No mention of competing app names or trademarked terms |
| 4.2 | **Claims are verifiable** | Any statistics or facts cited can be traced to a real source (WHO, CDC, published study) |
| 4.3 | **No medical advice** | Content doesn't promise health outcomes or prescribe treatment |
| 4.4 | **Brand voice consistent** | Tone matches the Zero Proof brand voice (direct, no-BS, empathetic, not preachy) |
| 4.5 | **No recycled content** | This concept hasn't been posted before (check results.jsonl for duplicate topics/hooks) |

## 5. Experiment Integrity

| # | Check | What to verify |
|---|---|---|
| 5.1 | **Single output per cycle** | Only one reel was produced for this cycle (not multiple variations rendered) |
| 5.2 | **results.jsonl entry exists** | A single entry for this cycle exists in results.jsonl with all required fields |
| 5.3 | **Discarded variations logged** | `reasoning.discarded_variations` contains the non-winning concepts with scores and reasons |
| 5.4 | **Experiment variable tracked** | If part of an experiment, `experiment_id` and `experiment_variable` are populated |

## 6. Platform Compliance

| # | Check | What to verify |
|---|---|---|
| 6.1 | **Original content** | Not repurposed from another platform with visible attribution to that platform |
| 6.2 | **Audio licensed/original** | Audio track is from our library, royalty-free, or original — no copyrighted music |
| 6.3 | **Community guidelines safe** | Content doesn't violate Instagram community guidelines (no graphic content, misinformation, etc.) |

---

## Audit Template

Copy this for each review:

```
### QA Review: EXT-XXX

**Reel:** [title]
**Format:** [tier]
**Reviewer:** Zigzag
**Date:** YYYY-MM-DD

#### Results
- [ ] 1.1 Video exists
- [ ] 1.2 Video format correct
- [ ] 1.3 Duration ≤ 90s
- [ ] 1.4 No watermarks
- [ ] 1.5 Caption exists
- [ ] 1.6 Posting date specified
- [ ] 2.1 Hook ≤ 125 chars
- [ ] 2.2 Hook no emojis
- [ ] 2.3 Body present
- [ ] 2.4 Tone matches format
- [ ] 2.5 Single CTA
- [ ] 2.6 CTA type appropriate
- [ ] 2.7 Hashtags 3-5
- [ ] 2.8 No broad hashtags
- [ ] 2.9 Hashtags after CTA
- [ ] 2.10 No hashtag-start
- [ ] 3.1 Virality ≥ 4
- [ ] 3.2 Hook tension
- [ ] 3.3 Specificity
- [ ] 3.4 Emotional resonance
- [ ] 3.5 Sendable
- [ ] 3.6 Watchable
- [ ] 4.1 No competitor TMs
- [ ] 4.2 Claims verifiable
- [ ] 4.3 No medical advice
- [ ] 4.4 Brand voice
- [ ] 4.5 No recycled content
- [ ] 5.1 Single output/cycle
- [ ] 5.2 results.jsonl entry
- [ ] 5.3 Discards logged
- [ ] 5.4 Experiment tracked
- [ ] 6.1 Original content
- [ ] 6.2 Audio licensed
- [ ] 6.3 Community safe

**Verdict:** PASS / FAIL
**Failures:** [list specific items]
**Action:** [move to in_review / send back with feedback]
```
