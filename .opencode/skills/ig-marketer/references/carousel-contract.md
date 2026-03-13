## Carousel contract

This file defines the only carousel details the IG marketer skill should rely on.

Treat the command in `references/config.json` (`carousel.command`) as a black box adapter.
Do not depend on its internal workflow, prompt format, or extra output fields.

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
