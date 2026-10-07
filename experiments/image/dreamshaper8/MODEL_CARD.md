# Sora LoRA for DreamShaper 8

Experimental image adapter for Sora, an original adult anime sky courier. Trigger: `soraskychar`. Use with the pinned DreamShaper 8 base and start at strength 0.8 with `solo` in the prompt.

Base: `Lykon/dreamshaper-8`, revision `a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917`, derived from SD1.5. The base model is downloaded separately. This repository distributes additional rank-8 U-Net LoRA weights trained for 400 steps on 20 synthetic, reviewed and captioned images; four reference images were held out. Source prompts/hashes are in `docs/dataset-manifest.json` at the repository root.

Final adapter: `results/dreamshaper8-sora-001/train/sora.safetensors`, SHA-256 `8d65b6f33f9b5c484105a2997ecb3d2ed761693813d234e502c5b5d4335cd163`. Earlier checkpoints and a small single-seed evaluation are included. Identity improved on inspected samples; jacket color, alternate outfits, hands, bag placement and action obedience remain imperfect. See [results](../../../docs/dreamshaper8-results.md).

The base identifies its model license as CreativeML OpenRAIL-M. Adapters are distributed with the underlying model license and use restrictions; see [license notice](../../../LICENSE-MODEL.txt) and the [creator's model card](https://huggingface.co/Lykon/dreamshaper-8). This is a model-license notice, not a blanket software license for the repository.
