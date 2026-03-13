## Carousel contract

This file defines the only carousel details the IG marketer skill should rely on.

Treat the script in `references/config.json` (`carousel.renderScript`) as a black box adapter.
Do not depend on its internal workflow, content schema, or extra output fields.
For invocation details see `references/carousel-workflow.md`.

### Required inputs

- topic
- target audience
- angle
- CTA
- optional visual style

### Required outputs

- `output/carousels/<slug>/content.json`
- `output/carousels/<slug>/*.png`
- `status`: `success` or `failure`
- `error`: short human-readable message when status is `failure`

### Rule

If the command returns extra detail, ignore it unless it is listed above.
