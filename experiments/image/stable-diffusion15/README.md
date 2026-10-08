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
