# Sora training handoff

## Local Model Studio added 2026-10-08

Launch `studio/start.ps1`; browser URL `http://127.0.0.1:7860`. The local server
uses the existing environment and standard-library HTTP. It offers both image
models, base-only / LoRA-only generation, matched comparisons, checkpoint and
sampling controls, progress, saved history and image/settings downloads. Original
weights and adapters are read without modification. Outputs stay in ignored
`studio/artifacts/jobs/`.

Five request-validation tests passed. Real GPU tests covered both models and
standalone base/LoRA modes; each comparison matched the corresponding existing
experiment PNGs byte for byte. Browser testing used project-local Agent Browser
0.38.2 with installed Chrome in a separate profile. See `studio/README.md` for
usage, extension contracts and existing apps. Only image inference is implemented;
future text chat needs conversation handling, and voice/video need their own
loaders and training/inference backends. Agent Browser is a local test tool and is
not required to run the UI.

## Latest experiment — DreamShaper 8 completed 2026-10-08

The original Waifu Diffusion / Sora experiment below is preserved in place. `experiments/image/waifu-diffusion-sora/profile.json` registers it in the new structure. `experiments/preserved-sd1.json` records 221 original file hashes; all matched after DreamShaper training, full evaluation and an additional scene. Original models, data/captions/latents, scripts/configs, adapters and evaluation files were not changed.

DreamShaper 8 is pinned to `Lykon/dreamshaper-8` revision `a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917`. Separate model/cache/artifact paths are under `experiments/image/dreamshaper8/`. The 10-step smoke test, fresh 400-step run, all checkpoint evaluations, matched solo portrait and additional sunset bridge scene passed. Full training took 17m27s by adapter metadata / 17m41s including trainer launch; sampled maximum device memory was 2,504 MiB and temperature 89 C. No CUDA OOM. All saved adapters are finite.

Recommended starting adapter: `experiments/image/dreamshaper8/results/dreamshaper8-sora-001/train/sora.safetensors`, strength 0.8, with `solo`. New final SHA-256: `8d65b6f33f9b5c484105a2997ecb3d2ed761693813d234e502c5b5d4335cd163`. The versioned result export includes five adapters, configs/manifests, telemetry and 23 images. Raw artifacts are in `experiments/image/dreamshaper8/artifacts/dreamshaper8-sora-001/` and ignored by Git. Read `docs/dreamshaper8-results.md` and the exported `comparison.html`; jacket color, scarves on alternate outfits, hands and precise action obedience remain limitations.

`experiments/run.ps1` is the new profile-based launcher; its default action starts a fresh full pipeline, so do not invoke it merely to inspect results. See `experiments/README.md` for individual stages, new-prompt generation and exports. Eight isolation/integrity tests passed. Existing `scripts/` launchers retain their original behavior. Image SD1.x LoRA is implemented; text, video and audio/voice folders are extension documentation and require their own backends.

## Status — completed 2026-10-07

The authorized local fine-tuning pipeline completed: installation, pinned model download, baseline inference, 10-step smoke training, fresh 400-step training, final inference, and comparison of 100/200/300/400-step checkpoints. GPU memory fit and adapter loading are now verified. The user subsequently requested GitHub publication and explicitly chose a public repository on 2026-10-08.

Recommended starting adapter: `outputs/sora-20261007-233343/sora.safetensors`. Use strength 0.8 and include `solo` for single-person prompts. The adapter improves identity substantially, with remaining duplicate-subject, anatomy, and outfit-detail limitations. See `docs/training-results.md` and `docs/training-results.html` for actual findings and images. The gallery includes the successful matched solo portrait test and four held-out references.

## Character and dataset

- Original adult character Sora, a sky courier: short teal bob, amber eyes, cream jacket, red scarf, brown satchel, navy trousers, brown boots. Trigger: `soraskychar`.
- Reference: `assets/sora-reference.png`, with exact prompt in the adjacent `.prompt.txt` file.
- 20 distinct captioned training images in `data/train/`; 4 held-out references in `data/validation/`. Three training images show a blue sweater without jacket/scarf.
- Accepted images visually reviewed; captions corrected to actual content. Rejected image with wrong bag placement preserved in `assets/rejected/` and excluded from training.
- Dataset review gallery: `docs/dataset-gallery.html`. Full generation prompts, corrected captions, hashes, dimensions, and reviews: `docs/dataset-manifest.json`.
- Validator and five tests passed: no missing captions, broken images, exact pixel duplicates, or train/validation overlap. Held-out references were never trained on.

## Environment and corrected model pin

Windows / PowerShell, NVIDIA RTX 4050 Laptop GPU, 6141 MiB VRAM. Project-local Python 3.11.17 in `.tools/python`, environment in `.venv`. PyTorch 2.6.0+cu124, torchvision 0.21.0+cu124, PEFT 0.14.0, SciPy 1.15.3; trainer sd-scripts v0.10.6 / commit `6e14642f3bc756cd947803eac0e7c9be4acdf964`. Exact installed packages are recorded per run.

The earlier handoff incorrectly assumed `hakurei/waifu-diffusion` main was SD 1.x. It contains SD 2.x (1024 attention dimension). `configs/character.json` now pins Waifu Diffusion 1.3 / SD 1.x revision `342d18da939534326d8571b7a8b5195f43800db6`, from the fp16 branch. The downloader checks architecture before fetching weights and downloads one complete format per component. Current source record: `models/model-source.json`.

Incompatible downloads are retained in `models/waifu-diffusion-incompatible-sd2/`, with `models/incompatible-sd2-source.json`. Source images and rejected artifacts are preserved. Shared scripts set project-local Hugging Face, uv, pip, Torch, and temporary paths. Initial installation used default pip cache/temp paths before that correction. No API key is needed.

Terminal HTTPS through Windows curl failed inside the sandbox with `SEC_E_NO_CREDENTIALS`; the pipeline ran with approved escalation. No system Python changes were made. Setup now installs the previously missing SciPy dependency required by the model's LMS scheduler.

## Run artifacts

- Baseline: `outputs/baseline-20261007-233227-405483/`.
- Smoke: `outputs/smoke-20261007-233251/sora.safetensors` (10 steps, passed).
- Full run: `outputs/sora-20261007-233343/` (400 optimizer steps, 16 epochs, approximately 13 minutes).
- Full run includes final adapter, 100/200/300/400-step checkpoints, exact training/dataset configurations, manifest, and package list. All adapter tensors are finite.
- Actual bucket: 384×576 with configured resolution 512. Batch 1, accumulation 4, rank/alpha 8, U-Net-only LoRA, fp16, checkpointing, cached latents, SDPA, 8-bit AdamW. Observed GPU samples were about 2.4 GB; no peak-memory instrumentation was used and no CUDA OOM occurred.
- Matched evaluation: 4 prompts per checkpoint, seed 42, 28 inference steps, guidance 7, 512×512, strength 0.8. Output directories and visual assessments are in the results document.
- Inference filter blanked the 100-step sweater sample; an identical rerun confirmed the flag. New generation metadata records filter flags and model revision. The filter remains enabled.
- Final adapter SHA-256: `5cf41503ea4eef4057ebf113c3f8fedeefbe61224a082ce84261127e7f541004`.

## Further use

Run `scripts/generate.ps1 -Lora outputs/sora-20261007-233343/sora.safetensors -Prompt 'soraskychar, solo, 1girl, adult woman, short teal hair, amber eyes, cream jacket, red scarf, portrait, white background, anime illustration'` for a new sample.

`scripts/start.ps1` still starts a fresh complete pipeline when invoked; existing trained outputs are preserved. Another training run is optional, not needed to finish the original task. Evaluate more seeds and poses before drawing broader quality conclusions. See `docs/EXTENDING.md` for verified GPU performance and researched image/video extension options. Repository publication includes source, dataset, adapters, and comparison samples, while excluding downloaded base models, environments, and caches; check `git remote -v` and `git log` for publication state.

Sources: [Waifu Diffusion 1.3 model card](https://huggingface.co/hakurei/waifu-diffusion/blob/fp16/README.md), [pinned trainer](https://github.com/kohya-ss/sd-scripts/tree/v0.10.6).
