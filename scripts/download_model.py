"""Download one pinned snapshot; re-runs reuse the recorded revision."""
import json
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download, snapshot_download

ROOT = Path(__file__).resolve().parents[1]


def main():
    character = json.loads((ROOT / "configs/character.json").read_text(encoding="utf-8"))
    model_id = character["model_id"]
    destination = ROOT / "models/waifu-diffusion"
    manifest_path = ROOT / "models/model-source.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["model_id"] != model_id:
            raise SystemExit("Recorded model differs from character config; use a fresh model directory.")
        revision = manifest["revision"]
        if character.get("model_revision") and revision != character["model_revision"]:
            raise SystemExit("Recorded revision differs from pinned config; use a fresh model directory.")
    else:
        revision = HfApi().model_info(model_id, revision=character.get("model_revision")).sha
        manifest = {"model_id": model_id, "revision": revision}
        # Record before download so an interrupted download resumes the same snapshot.
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    config_path = hf_hub_download(model_id, "unet/config.json", revision=revision, local_dir=destination)
    unet_config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if unet_config.get("cross_attention_dim") != 768 or unet_config.get("in_channels") != 4:
        raise SystemExit("Pinned model must be SD 1.x; refusing to download incompatible weights.")
    files = set(HfApi().list_repo_files(model_id, revision=revision))
    weights = []
    for component in ("unet", "vae", "text_encoder", "safety_checker"):
        stem = "diffusion_pytorch_model" if component in ("unet", "vae") else "model"
        safe = f"{component}/{stem}.safetensors"
        binary = f"{component}/{'diffusion_pytorch_model' if component in ('unet', 'vae') else 'pytorch_model'}.bin"
        chosen = safe if safe in files else binary
        if chosen not in files:
            raise SystemExit(f"Missing weights: {component}")
        weights.append(chosen)
    snapshot_download(
        repo_id=model_id,
        revision=revision,
        local_dir=destination,
        # One complete weight set; avoid downloading variant/format duplicates.
        allow_patterns=["model_index.json", "README.md", "LICENSE*", "unet/config.json",
                        "vae/config.json", "text_encoder/config.json", "tokenizer/*", "scheduler/*",
                        "safety_checker/config.json", "feature_extractor/*", *weights],
        max_workers=2,
    )
    print(f"Downloaded {model_id}@{revision} to {destination}")


if __name__ == "__main__":
    main()
