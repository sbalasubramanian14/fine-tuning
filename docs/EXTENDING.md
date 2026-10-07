# GPU performance and extending the training pipeline

Checked on 2026-10-08 against the completed run, local scripts, and upstream documentation. Suggested models and video workflows below have not been trained or benchmarked on this laptop.

## How the laptop performed

| Measurement | Observed result |
| --- | --- |
| GPU | RTX 4050 Laptop, 6 GB VRAM |
| System RAM | Approximately 15.2 GiB visible to Windows |
| Full run | 400 optimizer steps, 16 epochs, 20 images |
| Training duration from adapter metadata | 773.3 seconds, approximately 12 minutes 53 seconds |
| Training-loop time per optimizer step | Approximately 1.89 seconds, averaged from TensorBoard timestamps |
| Gradient accumulation | 4 microbatches per optimizer step |
| GPU memory snapshots | Approximately 2.4 GB during training; not a measured peak |
| CUDA memory errors | None in smoke or full training |
| Final logged average loss | 0.1197; not a visual-quality score |
| Training image bucket | 384x576, from configured resolution 512 |
| Final adapter size | Approximately 6.55 MiB |

This is a successful small LoRA workload for this GPU. It does not benchmark full-model training, 1024-resolution training, video, or maximum throughput. GPU utilization snapshots varied, and temperatures reached approximately 84 C during the run; there was no continuous telemetry, so sustained utilization and thermal throttling cannot be established. The observed memory headroom does not establish whether a larger architecture will fit.

## Can a better image base be used?

Yes. The current model is an older SD 1.x anime model selected for a modest VRAM budget. Better means better for the desired content and prompts, and must be checked with matched samples.

| Option | Fit for this laptop and repository |
| --- | --- |
| Another SD 1.5 illustration/anime checkpoint, such as DreamShaper 8 | Most practical next experiment. Its published configuration has the same 768 cross-attention dimension and four latent channels required here. Pin a revision, check component layout, retrain the LoRA on the same dataset, and compare baselines. Similar architecture makes memory fit plausible, not verified. |
| SDXL or an SDXL anime derivative | A separate training/inference profile is needed. The pinned trainer supports SDXL LoRA and documents 8 GB as feasible, 10 GB recommended. This 6 GB GPU is below that documented target. Reduced-resolution/offload experiments may work, but cannot be promised. |
| Larger transformer image models such as FLUX | Different loaders, training modules, quantization/caching, and memory controls are required. They are not supported by these launchers. Prefer a larger GPU for a straightforward training workflow. |

Sources: [DreamShaper 8](https://huggingface.co/Lykon/dreamshaper-8), [its architecture](https://huggingface.co/Lykon/dreamshaper-8/blob/main/unet/config.json), [pinned SDXL trainer guidance](https://github.com/kohya-ss/sd-scripts/blob/v0.10.6/docs/train_SDXL-en.md).

The existing adapter is tied to its model family. It cannot be loaded into SDXL or Wan as a compatible adapter. Transfer between SD 1.x checkpoints may work but changes behavior; retraining against the intended base is the reliable comparison.

## Can this fine-tune other datasets and arbitrary image models?

Other datasets: yes, for tasks such as subjects, products, illustration styles, or visual domains, provided the images and captions consistently represent the intended concept. A random mixture does not guarantee a useful result. An image-editing task with paired inputs/outputs needs a different dataset format and objective. This pipeline trains a small LoRA adapter rather than all base-model weights.

Current limitations are concrete:

- Model download and environment checks explicitly require SD 1.x; model storage paths are named for Waifu Diffusion.
- Training and inference scripts use fixed SD 1.x trainer/pipeline classes.
- Character name, trigger, prompts, and negative prompt are in `configs/character.json`.
- Dataset configuration controls the training path, repeats, buckets, and batch size. The validator defaults to `data/train` and `data/validation`, requires the configured trigger as the first caption tag, and defaults to 20/4 images.
- Changing `image_dir` alone does not change the validator's default directories. Those paths must be passed consistently through the launchers too.
- Cached latents must not be reused across a changed VAE/base model without validating or regenerating them.

A reusable extension should add per-experiment profiles for model ID/revision/family, model/cache directories, dataset and held-out paths, trigger/caption policy, evaluation prompts/seeds, and training parameters. It should dispatch the family-specific trainer and inference pipeline, record provenance, then validate -> baseline -> smoke -> train -> compare. That extension has not been implemented in this turn.

## Can video models be fine-tuned?

Yes, with video-specific trainers. Still images can teach appearance to supported video models, but cannot teach temporal motion; motion learning requires clips with consistent frame sampling, resolution, duration, frame rate, and captions. An SD image LoRA is not interchangeable with a Wan/CogVideoX LoRA.

For this laptop, start by testing short, low-resolution animation with a compatible SD 1.x base/character adapter and an existing AnimateDiff motion module. AnimateDiff supports personalized image models without retraining the motion module. This inference route still needs a memory smoke test; frame count and CPU offload affect feasibility. [Official AnimateDiff documentation](https://github.com/guoyww/AnimateDiff).

For actual modern video-model training, Wan with Musubi Tuner is a supported route, but this is a substantial hardware step up. Musubi recommends at least 24 GB VRAM for video training and 64 GB system RAM; requirements vary with settings. The laptop's 6 GB VRAM and roughly 16 GB RAM make that a difficult local target. Use a larger remote GPU or treat small-model, heavily offloaded training as an unverified experiment. [Musubi Tuner requirements](https://github.com/kohya-ss/musubi-tuner), [Wan training documentation](https://github.com/kohya-ss/musubi-tuner/blob/main/docs/wan.md).

Wan 2.1's official 1.3B baseline lists 8.19 GB VRAM for inference. Quantization/offload may reduce inference memory, but this figure does not establish fine-tuning memory or speed. [Official Wan 2.1 repository](https://github.com/Wan-Video/Wan2.1).

Practical progression: compare a stronger SD 1.5 base locally; make experiment profiles reusable; test existing motion-module inference; use a larger GPU when video-model fine-tuning is the objective.

## What is included in GitHub?

The public repository includes scripts, configs, tests, documentation, the generated captioned Sora dataset, design references and rejected source artifact, the full-run adapters/checkpoints, and the saved baseline/adapter comparisons. It excludes base-model downloads, environments, dependency checkout, latent caches, package caches, temporary files, and local TensorBoard logs. The included experiment outputs are explicitly allowlisted in `.gitignore`; future local runs stay excluded by default.
