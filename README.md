# Local anime character LoRA

An SD 1.x character LoRA experiment for an NVIDIA RTX 4050 Laptop GPU with 6 GB VRAM, on Windows. The original character is **Sora**, an adult sky courier. Trigger: `soraskychar`.

## Current state

- Repository, configuration, setup scripts, dataset validator, training launcher, and inference script created.
- Character reference: `assets/sora-reference.png`, generated using the built-in imagegen tool.
- Full reference generation prompt: `assets/sora-reference.prompt.txt`.
- Dataset complete: 20 captioned training images in `data/train/` and 4 held-out images in `data/validation/`.
- Browse `docs/dataset-gallery.html`; full prompts, corrected captions, hashes, and visual reviews are in `docs/dataset-manifest.json`.
- Project-local Python 3.11 and CUDA dependencies installed; GPU access verified.
- The 10-step smoke and fresh 400-step full run passed. Adapter: `outputs/sora-20261007-233343/sora.safetensors`. Baseline and 100/200/300/400-step inference were completed and visually compared.
- [Results and limitations](docs/training-results.md) and [comparison gallery](docs/training-results.html). Identity improves substantially; include `solo` to reduce duplicate subjects. Hands and outfit details still need inspection.

Local checks completed: five dataset-validator tests passed; all Python files compile; PowerShell scripts and TOML/JSON configurations pass syntax checks. These checks do not validate CUDA training or dependency installation.

The images were generated with the built-in imagegen tool and visually reviewed. One image with the satchel on the wrong hip was replaced; its rejected version is preserved under `assets/rejected/`. This is a small synthetic learning dataset. The repository includes the captioned dataset, reference images, trained Sora adapters, and evaluation samples. Environments, caches, base-model weights, latent caches, and other runs are excluded from Git.

Read [GPU performance and extension options](docs/EXTENDING.md) for other image datasets, base models, and video training. The included Sora adapter is associated with the base model's [CreativeML OpenRAIL-M license](LICENSE-MODEL.txt); see [model provenance](MODEL_CARD.md).

## One-command local workflow

From a normal PowerShell terminal with download access:

```powershell
cd F:\projects\fine-tuning
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

This installs the environment, downloads the model, validates the dataset, generates baseline samples, runs the 10-step smoke test, trains a fresh 400-step adapter, and generates comparison samples. It stops on errors. Pass `-SmokeOnly` to stop after baseline generation and the smoke test.

For an agent session, read `docs/HANDOFF.md` before running the pipeline.

## 1. Install the isolated environment

Run these commands in a normal PowerShell terminal with internet access:

```powershell
cd F:\projects\fine-tuning
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\download-model.ps1
```

The execution policy flag applies only to this PowerShell process; the scripts do not change your system policy. Setup downloads uv, installs Python 3.11 inside `.tools/python`, creates `.venv`, clones sd-scripts at `v0.10.6`, and installs CUDA-enabled PyTorch 2.6.0 plus the trainer dependencies. If Python 3.11 is already installed, pass `-PythonPath 'C:\path\to\python.exe'` to setup instead.

Downloads require several GB and the environment/model/cache can consume tens of GB. All project tools, caches, model weights, logs, and outputs stay in this folder. Existing system Python is left alone. Setup checks CUDA and package compatibility; individual runs record the installed package versions.

The model is Waifu Diffusion 1.3 from `hakurei/waifu-diffusion`, pinned to SD 1.x revision `342d18da939534326d8571b7a8b5195f43800db6` (the `fp16` branch). The repository's default branch contains SD 2.x weights and is incompatible with this configuration. The downloader checks the architecture before fetching weights, downloads one complete weight format, and records the exact revision in `models/model-source.json`. Its weights use CreativeML OpenRAIL-M, not an unrestricted Apache/MIT license. Read the model card before distributing outputs or adapters.

## 2. Prepare the character dataset

Read `docs/dataset-plan.md`. Put at least 20 distinct images in `data/train/` and 4 held-out images in `data/validation/`. Each image needs a matching UTF-8 text caption. For example:

```text
data/train/001.png
data/train/001.txt
```

Caption example:

```text
soraskychar, 1girl, adult woman, short teal hair, amber eyes, cream jacket, red scarf, brown satchel, upper body, smiling, white background, anime illustration
```

Caption only visible details. The trigger is the first comma-separated tag and is kept fixed when the remaining tags are shuffled. Do not train on grids, turnaround sheets, watermarked images, near-duplicates, or inconsistent character designs. The reference image is a design anchor; a single image is not a usable character dataset.

Validate:

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_dataset.py
```

The validator catches missing captions, undersized/broken images, duplicate pixels, and overlap with held-out images. You must also inspect character identity and anatomy visually. Validation images are never included in the training dataset.

## 3. Generate the baseline and train

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\generate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\train.ps1 -Smoke
```

The smoke run uses 10 optimizer steps to verify the environment and memory fit. Its adapter is a diagnostic artifact, not a finished model. If it succeeds, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\train.ps1
```

Training starts a fresh run with 400 optimizer steps, rank/alpha 8, U-Net-only LoRA, fp16, batch size 1, gradient accumulation 4, gradient checkpointing, cached latents, and 8-bit AdamW. The text encoder is frozen. This is a conservative starting configuration, not a guarantee that every 6 GB setup will fit or that 400 steps is optimal. Each run records a dataset manifest, model/trainer revisions, configuration, and package versions. Checkpoints are saved every 100 steps and at completion. Smoke and real training have separate directories. Compare earlier checkpoints too: a small dataset can overfit before the last checkpoint.

Monitor loss in `logs/` with TensorBoard and inspect several checkpoints. If CUDA runs out of memory, close other GPU apps first. If it still fails, reduce `resolution` to 384 in `configs/dataset.toml`, then repeat the smoke run. Do not launch the full run until smoke passes.

## 4. Compare before and after

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\generate.ps1 -Lora .\outputs\sora-YOUR-RUN-TIMESTAMP\sora.safetensors
```

`generate.ps1` without `-Lora` creates a baseline. With `-Lora`, it runs the same prompts with the same seeds using adapter strength 0.8. Results go to separate folders under `outputs/`, including settings in `generation.json`. Default prompts test portrait likeness, full-body appearance, a new scene, and a different outfit. Use the held-out references to assess likeness; they are not automatically scored by this script. Look for improvements in the face, hair, and colors without memorizing the original poses/backgrounds.

Custom prompt:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\generate.ps1 -Lora .\outputs\sora-YOUR-RUN-TIMESTAMP\sora.safetensors -Prompt 'soraskychar, 1girl, short teal hair, amber eyes, walking through a rainy city, anime illustration'
```

## Sources

- [Waifu Diffusion model card](https://huggingface.co/hakurei/waifu-diffusion)
- [sd-scripts trainer and Windows setup](https://github.com/kohya-ss/sd-scripts/tree/v0.10.6)
- [Dataset configuration reference](https://github.com/kohya-ss/sd-scripts/blob/v0.10.6/docs/config_README-en.md)
- [uv Python installations](https://docs.astral.sh/uv/guides/install-python/)
