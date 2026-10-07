# Sora training results

Local training and inference completed on 2026-10-07. The 400-step adapter learns Sora's teal bob, amber eyes, cream jacket, red scarf, and much of the reference illustration style. It is a useful first character LoRA, with remaining composition and anatomy limitations.

## Saved adapter

- Recommended starting adapter: `outputs/sora-20261007-233343/sora.safetensors` (6,871,576 bytes).
- SHA-256: `5cf41503ea4eef4057ebf113c3f8fedeefbe61224a082ce84261127e7f541004`.
- Earlier checkpoints: `sora-step00000100.safetensors`, `sora-step00000200.safetensors`, `sora-step00000300.safetensors` in the same directory. The 400-step checkpoint is also retained.
- Starting inference strength: 0.8. Add `solo` for a single-person composition.

## Verified run

Python 3.11.17, PyTorch 2.6.0+cu124, torchvision 0.21.0+cu124, sd-scripts v0.10.6 (commit `6e14642f3bc756cd947803eac0e7c9be4acdf964`), PEFT 0.14.0, SciPy 1.15.3, NVIDIA RTX 4050 Laptop GPU (6 GB).

Base model: Waifu Diffusion 1.3, `hakurei/waifu-diffusion` revision `342d18da939534326d8571b7a8b5195f43800db6` (SD 1.x fp16 branch). The repository's main branch is SD 2.x and was rejected after inspecting its architecture; the downloader now validates this before fetching large weights. [Model card](https://huggingface.co/hakurei/waifu-diffusion/blob/fp16/README.md).

The 10-step smoke run passed, followed by a fresh 400-step run over 16 epochs, taking approximately 13 minutes for training. Rank/alpha 8, U-Net-only LoRA, fp16, batch 1, accumulation 4, checkpointing, cached latents, SDPA, 8-bit AdamW, learning rate 0.0001. Configured resolution 512 produced a 384×576 bucket for the portrait dataset. GPU samples during training were approximately 2.4 GB in use; this is not a measured peak. No CUDA out-of-memory error occurred. Final logged average loss was approximately 0.1197; it does not measure identity quality.

All saved adapters have finite tensors. The run directory contains the exact configurations, dataset hashes, model/trainer revisions, and installed packages. Dataset validation and five validator tests passed; 20 training images were used and all four held-out images remained excluded.

## Matched evaluation

Open [the comparison gallery](training-results.html) to inspect the original images and held-out references. All checkpoints use the same four prompts, seed 42, negative prompt, 28 inference steps, guidance 7, and 512×512 size. Adapter strength is 0.8.

| Checkpoint | Observed result |
| --- | --- |
| Baseline | Wrong hair/eye colors and frequent two-person compositions; weak resemblance to Sora. |
| 100 steps | Some style/outfit learning, but weak identity. Sweater sample was blanked by the inference filter; repeating it recorded `nsfw_content_detected: true`. |
| 200 steps | Teal hair and amber eyes emerge. Full-body result includes boots and a bag, though bag placement and jacket differ from the reference. Other prompts still produce two people. |
| 300 steps | Stronger identity and a better-framed full-body image. Portrait, cafe, and sweater still produce two people; sweater retains an unwanted scarf. |
| 400 steps | Strongest likeness in this sample set. Cafe produces one recognizable Sora in a new setting. Sweater follows the blue outfit without a scarf. Original portrait and sweater prompts still produce two people; mountain figure is small and has blue-colored hand/detail artifacts. |

The additional matched portrait test inserts `solo` into the original prompt. Baseline stays unlike Sora; the 400-step adapter produces a single woman with teal hair, amber eyes, cream jacket, and red scarf. This successful test is included in the gallery. Earlier checkpoints remain useful for comparing scene framing; the final adapter is the recommended starting point for likeness.

This is a qualitative review on one seed, not a quantitative held-out benchmark. Pose/background changes suggest useful generalization, but do not establish absence of memorization. Hands, outfit details, satchel consistency, and duplicate subjects still need inspection for each generated image.

## Generate another sample

From the repository root:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\generate.ps1 -Lora .\outputs\sora-20261007-233343\sora.safetensors -Prompt 'soraskychar, solo, 1girl, adult woman, short teal hair, amber eyes, cream jacket, red scarf, portrait, white background, anime illustration'

Generation records settings under `outputs/`. New generation metadata also records the model revision and inference-filter flags.

## Output directories

- Baseline: `outputs/baseline-20261007-233227-405483/`.
- 100 steps: `outputs/lora-20261007-234751-618633/`.
- 200 steps: `outputs/lora-20261007-234835-953116/`.
- 300 steps: `outputs/lora-20261007-234919-156362/`.
- 400 steps: `outputs/lora-20261007-234708-190982/`.
- Solo baseline: `outputs/baseline-20261007-235014-606857/`.
- Solo 400 steps: `outputs/lora-20261007-235034-613270/`.
- Filter diagnostic: `outputs/lora-20261007-235104-037504/`.
- Contact sheets and comparison index: `outputs/evaluation-sora-20261007-233343/`.
