# Sora dataset plan

Sora is an original adult female sky courier with a short teal bob, amber eyes, cream utility jacket, red scarf, brown crossbody satchel, navy trousers, and brown boots. The design reference is `assets/sora-reference.png`. Preserve the face, hair length/color, and eye color across all images. Keep images suitable for a general audience.

Use 20 training images and 4 held-out references to start. Include varied framing and backgrounds so the trigger does not simply memorize one composition. For synthetic images, generate separate illustrations using the design reference, then manually reject identity drift and bad anatomy. Synthetic training images teach the provided visual identity; they do not guarantee better anatomy or broader artistic ability than the base model.

| ID | Split | Composition |
|---|---|---|
| 001 | Train | Front portrait, neutral, white background |
| 002 | Train | Three-quarter portrait, smile, pale blue background |
| 003 | Train | Side portrait, thoughtful, gray background |
| 004 | Train | Upper body, hands on satchel strap, stone street |
| 005 | Train | Full body, standing, cream background |
| 006 | Train | Full body, walking, town square |
| 007 | Train | Upper body, surprised, sky backdrop |
| 008 | Train | Upper body, laughing, garden |
| 009 | Train | Seated, three-quarter view, wooden bench |
| 010 | Train | Full body, looking over shoulder, balcony |
| 011 | Train | Upper body, holding envelope, indoors |
| 012 | Train | Full body, reaching toward a shelf, room |
| 013 | Train | Portrait, serious, evening lighting |
| 014 | Train | Full body, hands on hips, hilltop |
| 015 | Train | Upper body, waving, platform |
| 016 | Train | Kneeling to tie boot, courtyard |
| 017 | Train | Portrait, blue sweater, no scarf, neutral background |
| 018 | Train | Upper body, blue sweater, no jacket/scarf, reading |
| 019 | Train | Full body, blue sweater, no jacket/scarf, lakeside |
| 020 | Train | Upper body, cream jacket and scarf, windy bridge |
| v01 | Validation | Portrait, soft smile, golden sunset |
| v02 | Validation | Full body, holding umbrella, rainy street |
| v03 | Validation | Seated at cafe, cream jacket and scarf |
| v04 | Validation | Upper body, blue sweater, no scarf, library |

Write captions based on what each final image actually shows. Start each caption with `soraskychar`. Describe outfit changes explicitly. Do not put evaluation/held-out images into the training folder. Do not horizontally flip the dataset automatically: satchel placement and any asymmetrical accessories should remain consistent.

## Reference generation prompt

The built-in imagegen tool generated `assets/sora-reference.png` with this specification:

> One standalone full-body anime illustration of Sora, an original adult female sky courier. Short teal bob, amber eyes, cream utility jacket with brass buttons, red scarf, brown crossbody satchel, navy trousers, brown ankle boots. Friendly determined expression, standing in front three-quarter view, both hands and feet visible. Clean ink linework and cel shading, plain warm light gray background. No text, watermark, panels, or grid.
