# Sora character LoRA

An experimental adapter for an original adult anime sky courier. Trigger: `soraskychar`. Intended for local illustration experiments.

## Provenance

- Base: Waifu Diffusion 1.3, `hakurei/waifu-diffusion`, revision `342d18da939534326d8571b7a8b5195f43800db6`.
- Original pretrained lineage: Stable Diffusion 1.4, as described by the Waifu Diffusion 1.3 model card.
- Adapter: `outputs/sora-20261007-233343/sora.safetensors`.
- Training: 400 steps, U-Net-only rank/alpha 8 LoRA, 20 synthetic captioned images. Four reference images were held out.
- Modifications: additional low-rank weights trained to represent Sora; the original base weights are not included or modified in this repository.
- Data: generated with the built-in imagegen tool, visually reviewed and captioned. Dataset generation prompts and hashes are in `docs/dataset-manifest.json`.

## Use and limitations

Start at strength 0.8 with `solo` in the prompt. Identity improved on the inspected seed-42 samples. Duplicate people, hands, outfit details, satchel placement, and mixed background styles can still occur. Only a small qualitative evaluation was performed. Read `docs/training-results.md` and inspect `docs/training-results.html`.

## Base-model license notice

The base model identifies its license as CreativeML OpenRAIL-M. The included adapters are distributed with that model license and its use restrictions; a copy is in `LICENSE-MODEL.txt`. That file is a model-license notice, not a blanket software license for all repository contents. Dependency code retains its upstream licenses and is downloaded separately by setup.

Sources: [Waifu Diffusion 1.3 model card](https://huggingface.co/hakurei/waifu-diffusion-v1-3), [pinned branch model card](https://huggingface.co/hakurei/waifu-diffusion/blob/fp16/README.md), [original license text](https://huggingface.co/spaces/CompVis/stable-diffusion-license/blob/main/license.txt).
