# Model experiments

Separate model profiles and artifacts, with the original working pipeline preserved.

| Folder | Status | Dataset and backend requirements |
| --- | --- | --- |
| `image/dreamshaper8/` | Runnable SD1.x LoRA experiment | Captioned images, held-out images, pinned Diffusers SD1.x base, sd-scripts |
| `image/waifu-diffusion-sora/` | Reference to completed experiment | Original files remain in `models/`, `data/`, `outputs/`, and `docs/` |
| `text/` | Extension documentation | Tokenized text or instruction/response pairs, text-specific trainer and evaluation |
| `video/` | Extension documentation | Clips/frame sequences and captions, temporal model trainer and evaluation |
| `audio/voice/` | Extension documentation | Audio/transcripts and speaker splits, speech-specific trainer and evaluation |

Run from the repository root:

```powershell
.\experiments\run.ps1 -RunName dreamshaper8-sora-001
```

This verifies preservation, downloads the pinned fp16 base, validates and copies only image/caption source files into a model-specific cache, generates a baseline, runs 10 smoke steps and 400 training steps, evaluates saved checkpoints, and verifies preservation again. An existing stage directory causes an error rather than overwriting artifacts. Each run records its exact profile, configs, dataset hashes, installed packages, trainer revision, GPU samples, elapsed time, and generation settings. The inference safety checker is retained.

Individual stages use the same run name:

```powershell
.\experiments\run.ps1 -Action download
.\experiments\run.ps1 -Action baseline -RunName dreamshaper8-sora-002
.\experiments\run.ps1 -Action smoke -RunName dreamshaper8-sora-002
.\experiments\run.ps1 -Action train -RunName dreamshaper8-sora-002
.\experiments\run.ps1 -Action evaluate -RunName dreamshaper8-sora-002
.\experiments\run.ps1 -Action verify
```

Models, latent caches, and raw run artifacts are ignored by Git. Profiles, source code, preservation hashes, and result documents are versioned. Original SD1.x artifacts retain their existing Git inclusion rules.

`preserved-sd1.json` is the historical hash record from the completed workstation experiment. Active preservation checks use a workspace-local snapshot in `.cache/experiments/preserved-sd1.json`. A fresh clone snapshots the original files actually present there; it does not require the historical machine's ignored base weights, latent caches or smoke outputs. Keep that local snapshot for subsequent experiments so changes to existing files are detected.

Generate another prompt using a trained adapter (omit `-Lora` for a base sample):

```powershell
.\experiments\run.ps1 -Action generate -Lora experiments/image/dreamshaper8/artifacts/dreamshaper8-sora-001/train/sora.safetensors -Prompt 'soraskychar, solo, adult woman, short teal hair, amber eyes, cream jacket, red scarf, anime illustration'
```

Export a completed run into its versioned `results/` folder:

```powershell
.\.venv\Scripts\python.exe experiments/export_results.py --run-name dreamshaper8-sora-001
```

The export includes adapters, configs, model/dataset manifests, GPU samples, and comparison images. It excludes base weights, source copies, latents, and raw training logs. Export refuses to overwrite a previous export.

To add another compatible SD1.x image model, copy the DreamShaper profile into a new image folder, give it a unique id and dedicated model/cache/artifact paths, pin a revision, and select appropriate data and evaluation settings. This backend checks the architecture and requires fp16 Safetensors components and a safety checker. SDXL, Flux, text, video, and voice require a new backend. Add the backend dispatch explicitly in `run.py`; unsupported types fail before any downloads or training. Future backends should implement download, dataset validation/preparation, baseline, smoke, train, evaluate, and preserve/verify stages, with model-specific cache identity and reproducible manifests.

For a new image dataset, place it in the new experiment's own `data/train/` and `data/validation/` folders; use matching captions and a distinct character config. Update `dataset`, `character_config`, and any training/evaluation settings in that profile. Keep the original Sora files unchanged so its preservation checks remain useful. Model compatibility, hardware fit, licenses, caption accuracy, and held-out quality must be checked for each experiment.
