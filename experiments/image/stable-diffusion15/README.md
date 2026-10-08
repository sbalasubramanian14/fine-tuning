# Stable Diffusion 1.5 base

An isolated profile for the original SD1.5 base weights, using the maintained
[mirror of the deprecated Runway repository](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5),
pinned to revision `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`.
This is distinct from the fine-tuned DreamShaper 8 and Waifu models.

Download only, from the repository root:

```powershell
.\experiments\run.ps1 -Profile experiments/image/stable-diffusion15/profile.json -Action download
```

The four FP16 components total approximately 2.55 GiB. The downloader requires
an additional 512 MiB of free space and never removes previous models.
Once downloaded, refresh Local Model Studio and select this model. Start at
512×512, 28 steps and guidance 7. It initially has no trained adapter; use base
generation. Existing Sora adapters remain associated with their training bases.

The profile reuses the original Sora source dataset/configuration only as inputs
for optional future training; no SD1.5 training has been run. Its models, caches
and run artifacts use separate folders. Invoking the runner without `-Action`
starts training as part of the full workflow, so use the download command above
when you only want to try the base model.

## Local validation

Downloaded and verified all four components against the pinned Hugging Face
SHA-256 hashes on 2026-10-08. The Studio API successfully generated one unfiltered,
nonblank 512×512 landscape at 28 steps, guidance 7 and seed 42 on the RTX 4050.
Generation took 8.75 seconds (excluding checks/loading). The filter was enabled.
This confirms loading and inference, not a broad image-quality evaluation.
The test request, image and metadata remain in ignored Studio job storage.
All 221 original preservation hashes matched after download. No SD1.5 LoRA has
been trained, and no old model or adapter was replaced.
