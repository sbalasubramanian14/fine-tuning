import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def main():
    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable. Run setup.ps1 and check the NVIDIA driver.")
    properties = torch.cuda.get_device_properties(0)
    print(f"GPU: {properties.name}; VRAM: {properties.total_memory / 2**30:.2f} GiB")
    model = ROOT / "models/waifu-diffusion"
    if not (model / "model_index.json").is_file():
        raise SystemExit("Model missing; run scripts/download-model.ps1")
    unet_config = json.loads((model / "unet/config.json").read_text(encoding="utf-8"))
    if unet_config.get("cross_attention_dim") != 768 or unet_config.get("in_channels") != 4:
        raise SystemExit("This experiment requires a standard SD 1.x model, not SD 2/SDXL.")
    for component in ("unet", "vae", "text_encoder"):
        if not any(p.suffix in {".bin", ".safetensors"} for p in (model / component).iterdir()):
            raise SystemExit(f"Model weights incomplete: {component}; rerun download-model.ps1")
    if not (ROOT / "vendor/sd-scripts/train_network.py").is_file():
        raise SystemExit("Trainer missing; run scripts/setup.ps1")
    print("Environment checks passed. The smoke run will measure whether training fits VRAM.")


if __name__ == "__main__":
    main()
