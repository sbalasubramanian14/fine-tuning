"""Generate matched baseline/LoRA evaluations with identical prompts and seeds."""
import argparse
import json
from datetime import datetime
from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lora", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scale", type=float, default=0.8)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA unavailable; run setup.ps1")
    character = json.loads((ROOT / "configs/character.json").read_text(encoding="utf-8"))
    pipe = StableDiffusionPipeline.from_pretrained(
        ROOT / "models/waifu-diffusion", torch_dtype=torch.float16, local_files_only=True
    )
    if args.lora:
        adapter = args.lora.resolve()
        if not adapter.is_file():
            raise SystemExit(f"LoRA missing: {adapter}")
        pipe.load_lora_weights(str(adapter.parent), weight_name=adapter.name, local_files_only=True)
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_slicing()
    name = "lora" if args.lora else "baseline"
    output = ROOT / "outputs" / f"{name}-{datetime.now():%Y%m%d-%H%M%S-%f}"
    output.mkdir(parents=True)
    prompts = [args.prompt] if args.prompt else character["evaluation_prompts"]
    metadata = {"lora": str(args.lora) if args.lora else None, "scale": args.scale,
                "seed": args.seed, "prompts": prompts, "negative_prompt": character["negative_prompt"],
                "steps": 28, "guidance_scale": 7.0, "width": 512, "height": 512}
    metadata["model"] = json.loads((ROOT / "models/model-source.json").read_text(encoding="utf-8"))
    metadata["images"] = []
    (output / "generation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    for index, prompt in enumerate(prompts, start=1):
        # Reinitialize for every prompt and every baseline/adapter run.
        kwargs = {"cross_attention_kwargs": {"scale": args.scale}} if args.lora else {}
        result = pipe(prompt=prompt, negative_prompt=character["negative_prompt"],
                      width=512, height=512, num_inference_steps=28, guidance_scale=7.0,
                      generator=torch.Generator(device="cpu").manual_seed(args.seed), **kwargs)
        result.images[0].save(output / f"{index:02d}.png")
        flags = result.nsfw_content_detected
        metadata["images"].append({"file": f"{index:02d}.png",
                                   "nsfw_content_detected": bool(flags[0]) if flags is not None else None})
        (output / "generation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved images and generation settings: {output}")


if __name__ == "__main__":
    main()
