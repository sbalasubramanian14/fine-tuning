# DreamShaper 8 / Sora

Pinned `Lykon/dreamshaper-8` revision `a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917`, fp16 weights. Model card: https://huggingface.co/Lykon/dreamshaper-8. This is an SD1.5-derived model under CreativeML OpenRAIL-M; see the root `LICENSE-MODEL.txt` and the model card for applicable model terms.

The experiment uses the original 20 training images and 4 held-out references through isolated copies. Rank 8, alpha 8, U-Net-only LoRA, 400 steps, batch 1, accumulation 4, fp16, 8-bit AdamW, seed 42. Original training and evaluation settings are reused for comparison. The stored base scheduler is retained and recorded; cross-base comparisons may therefore also reflect scheduler differences.

`models/base/` holds only this model. Its fp16 variant files are materialized under default filenames for sd-scripts compatibility, with source mapping and SHA-256 hashes in `models/model-source.json`. `cache/` holds model-and-dataset-specific source copies and latents. `artifacts/<run>/` holds baseline, smoke, training, checkpoint comparisons, solo comparisons, logs, manifests, and `comparison.html`.

From the repository root: `.\experiments\run.ps1 -RunName dreamshaper8-sora-001`. See `../../README.md` for individual stages and extension rules.

Completed run: [results and limitations](../../../docs/dreamshaper8-results.md), [gallery](results/dreamshaper8-sora-001/comparison.html), [model card](MODEL_CARD.md). Use a new run name for another training experiment; `dreamshaper8-sora-001` is preserved and cannot be overwritten.
