# Production Spec Contract

The production spec is the interface between viral-ig-marketer (orchestrator) and viral-producer (renderer). viral-ig-marketer builds this spec; viral-producer validates and executes it.

## Output Requirements

- Final output must be Instagram Reel format: `9:16` vertical at `1080x1920` in `.mp4`.
- Canonical render package path: `../viral-producer/output/reels/<slug>/`.
- Generated images for this flow must use `portrait_9_16` sizing.

## Required Fields

| Field | Type | Description |
|---|---|---|
| `format_tier` | string | One of: T1, T2, T3, T4, P1, P2, P3 |
| `format_tier_label` | string | Human-readable label (e.g. "P3 Cultural Edutainment") |
| `topic` | string | The content angle from the research brief |
| `hook_text` | string | The winning hook from virality gate |
| `cta_text` | string | The call-to-action text |
| `caption` | string | Full caption: hook line + body + CTA + hashtags |
| `imagery_direction` | string | Visual approach — footage style, color palette, mood |
| `audio_track` | string | Filename from the `audio/` directory |

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `specific_assets` | string | Paths to pre-generated assets, if any |

## Example

```json
{
  "format_tier": "P3",
  "format_tier_label": "P3 Cultural Edutainment",
  "topic": "hangxiety — the anxiety after a night of drinking",
  "hook_text": "There's a word for why you feel dread the morning after drinking",
  "cta_text": "Comment ZEROPROOF for the app that tracks your streak",
  "caption": "There's a word for why you feel dread the morning after drinking.\n\nIt's called hangxiety — and it's not just in your head. Alcohol disrupts GABA and glutamate, leaving your nervous system in overdrive.\n\nThe good news? Every alcohol-free day lets your brain recalibrate.\n\nComment ZEROPROOF for the app that tracks your streak.\n\n#soberlife #hangxiety #alcoholfree #sobercurious #zeroproof",
  "imagery_direction": "Cinematic drone footage of misty coastal cliffs at golden hour. Frosted glass card centered, dictionary-style typography.",
  "audio_track": "calm-reflective.mp3",
  "specific_assets": null
}
```
