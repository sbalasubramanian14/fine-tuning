# Stable Diffusion XL 1.0 Base

The original [Stability AI SDXL Base](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0),
pinned in `profile.json`, FP16 weights only. No refiner or LoRA is included.

From the repository root:

```powershell
.\experiments\image\sdxl-base\download.ps1
.\studio\start.ps1
```

The downloader fetches only the four FP16 components plus their configs and
tokenizers, verifies source SHA-256 hashes, and records the revision and hashes
in ignored `models/model-source.json`. Models stay inside this experiment's own
folder. Existing SD1.x models, adapters and datasets are not modified. Budget
6.46 GiB for weights and at least 1 GiB additional working space.

Refresh Studio and select **Stable Diffusion XL 1.0 · Base**. Begin at 1024×1024,
28 steps, guidance 5. The UI also supports 768×768 and portrait/landscape sizes.
The default uses the native 1024-pixel size recommended in the
[Diffusers SDXL guide](https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/stable_diffusion_xl).
768×768 remains a faster preview option; changing resolution does not guarantee
correct faces, anatomy or subject counts.
No LoRA or comparison mode is offered for this backend.

**Low VRAM** is the default for the 6 GB RTX 4050. **Balanced** memory mode
offloads whole components to system RAM between uses.
If GPU memory is exhausted during generation, the job retries with **Low VRAM**,
which offloads smaller submodules and may be substantially slower. Select Low
VRAM directly to avoid that first attempt. VAE tiling reduces decoding memory.
Every generation runs in a separate process. Result metadata records the memory
mode actually used, any fallback, timings and peak PyTorch GPU memory.

SDXL Base has no bundled SD1.x image safety checker. Its output is unfiltered;
the SD1.x image-filter toggle is not shown for this model. No filter was added.
Requests, generated images, metadata and logs stay in ignored Studio job storage.

This profile is for inference only. `experiments/run.ps1` does not implement
SDXL training; use the download launcher above. SD1.x adapters cannot be loaded
into SDXL. No training or adapter migration is performed by this setup.

## Local validation — 2026-10-09

All four source hashes verified at pinned revision
`462165984030d82259a11f4367a4eed129e94a7b`.

| Test | Effective mode | Generation time | Peak PyTorch allocated / reserved |
| --- | --- | --- | --- |
| 768×768, 28 steps, guidance 5, seed 42 | Low VRAM after Balanced CUDA OOM | 77.09 s | 2174.7 / 2186.0 MiB |
| 1024×1024, 8 steps, guidance 5, seed 42 | Low VRAM, selected directly | 29.47 s | 3854.5 / 3868.0 MiB |

Both saved images were nonblank and the expected dimensions. This is a loading
and memory smoke test, not a broad quality evaluation. The short 1024 test does
not establish the generation time or quality at 28 steps. Generation timings
exclude loading/checks; peak figures cover PyTorch memory, not total device use.

Balanced also failed after denoising in a 1024 test without a Python traceback.
Use **Low VRAM** on this 6 GB GPU; Balanced remains an optional mode to experiment
with other memory conditions or larger GPUs. Ordinary CUDA OOM exceptions in
Balanced trigger the documented fallback; a crashed worker cannot retry itself.

All 221 original preservation hashes matched, and all four DreamShaper and all
four SD1.5 weights matched their recorded hashes. UI test outputs stay local and
are excluded from Git. SDXL Base uses CreativeML Open RAIL++-M; see its model card
and downloaded license for provenance and terms.
