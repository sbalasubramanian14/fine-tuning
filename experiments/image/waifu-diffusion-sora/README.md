# Preserved Waifu Diffusion / Sora experiment

This folder registers the completed SD1.x experiment without relocating its files. `profile.json` records the original model, adapter hash, results, and Git checkpoint. `../../preserved-sd1.json` additionally records byte hashes of all original model/data/output files and original configurations/scripts before DreamShaper training.

Existing inference remains:

```powershell
.\scripts\generate.ps1 -Lora outputs/sora-20261007-233343/sora.safetensors -Prompt 'soraskychar, solo, 1girl, adult woman, short teal hair, amber eyes, cream jacket, red scarf, portrait, white background, anime illustration'
```

Results: `docs/training-results.md` and `docs/training-results.html`. The reference profile is deliberately read-only; launching a new run uses a new runnable profile and separate storage.
