# DreamShaper 8 / Sora results

Completed on 2026-10-08. DreamShaper 8 trained successfully on the RTX 4050 Laptop GPU. The inspected samples show substantially better Sora identity than its untrained baseline, with a single character in all four evaluation scenes at every checkpoint. Start with the 400-step adapter at strength 0.8 and include `solo`.

- [Comparison gallery](../experiments/image/dreamshaper8/results/dreamshaper8-sora-001/comparison.html)
- [Final adapter](../experiments/image/dreamshaper8/results/dreamshaper8-sora-001/train/sora.safetensors)
- [Exact profile](../experiments/image/dreamshaper8/profile.json), [training manifest](../experiments/image/dreamshaper8/results/dreamshaper8-sora-001/train/manifest.json), [measured performance](../experiments/image/dreamshaper8/results/dreamshaper8-sora-001/metrics.json)
- Previous experiment: [Waifu Diffusion results](training-results.md), [gallery](training-results.html). Its original files remain in place.

## Setup and performance

Base: `Lykon/dreamshaper-8`, revision `a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917`, fp16 Safetensors. The creator describes it as an SD1.5-derived model. All four downloaded component hashes matched the pinned Hugging Face files. The fp16 files were renamed to standard local filenames for sd-scripts; tensor contents were unchanged. The inference safety checker remains enabled. [Model card](https://huggingface.co/Lykon/dreamshaper-8).

The same 20 captioned training images and 4 held-out references were used. Only source images/captions were copied into a new cache, keyed by model revision and dataset hashes. Original VAE latents were never reused. Training used the pinned sd-scripts trainer, rank/alpha 8, U-Net-only LoRA, batch 1, accumulation 4, fp16, checkpointing, SDPA, AdamW8bit, learning rate 0.0001, seed 42, and 400 optimizer steps / 16 epochs. Actual bucket: 384 x 576, configured resolution 512. A separate 10-step smoke test passed first.

| Measurement | DreamShaper 8 | Previous Waifu run |
| --- | --- | --- |
| Adapter metadata training duration | 17m27s | 12m53s |
| New trainer-launch wall duration | 17m41s | Not recorded with this method |
| Observed device memory | Maximum 2,504 MiB across 512 samples | Approximately 2,381 MiB in intermittent observations |
| Observed temperature | Maximum 89 C | Up to 84 C in intermittent observations |
| CUDA out-of-memory failures | None | None |

New GPU telemetry was sampled approximately every two seconds and measures total device usage, including other GPU contexts. It is not a CUDA allocator peak. The earlier run was not instrumented equivalently. This session's training was about 35% slower by adapter timestamps; these runs do not establish an intrinsic speed difference between bases. All five saved DreamShaper adapters have finite tensors and the expected step counts.

## Visual assessment

The four comparison prompts use seed 42, 28 inference steps, guidance 7, 512 x 512, and adapter strength 0.8. Settings and scheduler configs are recorded per generation. DreamShaper uses its stored DEIS scheduler; the old Waifu run used LMS. Each experiment's baseline-versus-adapter comparison is matched, while comparisons across bases include their scheduler differences.

| Test | Observed result |
| --- | --- |
| Portrait | Even 100 steps gives teal hair, amber eyes and the cream/red outfit. At 400 steps the style and appearance resemble the Sora references much more closely than the dark-haired baseline. Single subject throughout. |
| Mountain path | Later checkpoints add dark trousers and brown boots; 400 also adds a brown bag. The jacket remains green despite the cream-jacket prompt. |
| Cafe | Stronger identity and cream/red outfit at 200–400 steps. The 400-step image retains a cup and single character. Hands and outfit details still require inspection. |
| Blue sweater, no scarf | Identity improves, but every checkpoint adds a scarf or scarf-like blue/yellow neck garment. The baseline followed the no-scarf outfit more closely. This remains a failure. |
| Matched solo portrait | The 400-step adapter fixes the baseline's dark hair and layered teal scarf, producing recognizable Sora. |
| Additional sunset bridge prompt | The final adapter produces a recognizable full-body Sora with cream jacket, red scarf, navy trousers, boots and brown bag. She stands beside the bridge rather than clearly walking across it. |

Compared with the inspected earlier Waifu samples, the new images have fewer duplicate-subject problems. This is a small, single-seed qualitative test, not evidence that DreamShaper is universally better. Three of the 20 training images have the alternate sweater outfit; the default scarf/outfit dominates the dataset. That imbalance is a plausible contributor to the scarf failure, but has not been isolated experimentally. More seeds, poses, and outfit tests are needed before choosing a production adapter.

The [additional scene and exact prompt](../experiments/image/dreamshaper8/results/dreamshaper8-sora-001/inference/generation.json) and [image](../experiments/image/dreamshaper8/results/dreamshaper8-sora-001/inference/01.png) are included in the result export. No inference sample was blanked by the safety checker.

## Preservation and future experiments

[Preservation snapshot](../experiments/preserved-sd1.json): all 221 original files matched their pre-experiment SHA-256 hashes after full evaluation and the additional scene. This includes both original downloaded model folders, source images/captions, old latent caches, prior adapters and evaluation outputs, and original scripts/configs. Existing gallery files were unchanged. The previous final adapter retains SHA-256 `5cf41503ea4eef4057ebf113c3f8fedeefbe61224a082ce84261127e7f541004`; the new adapter is `8d65b6f33f9b5c484105a2997ecb3d2ed761693813d234e502c5b5d4335cd163`.

See [experiments/README.md](../experiments/README.md) for commands and the folder/backend extension contract. Image SD1.x LoRA is runnable. Text, video, and audio/voice have separate extension folders; their trainers are not implemented or tested yet. New image datasets should have their own source folders and character configs. Models, environments, latent caches, and raw logs stay local; the reviewed result export includes five adapters and 23 generated images.
