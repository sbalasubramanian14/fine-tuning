"""Catch missing captions, bad images, duplicates, and validation leakage."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def inspect(directory, trigger):
    errors, records, seen = [], [], {}
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in EXTENSIONS)
    stems = set()
    for path in paths:
        if path.stem.lower() in stems:
            errors.append(f"{path.name}: shared filename stem; use unique names")
        stems.add(path.stem.lower())
        caption_path = path.with_suffix(".txt")
        if not caption_path.exists():
            errors.append(f"{path.name}: missing .txt caption")
            caption = ""
        else:
            caption = caption_path.read_text(encoding="utf-8-sig").strip()
            if not caption or caption.split(",")[0].strip() != trigger:
                errors.append(f"{path.name}: caption must start with '{trigger},'")
        try:
            with Image.open(path) as image:
                image.load()
                width, height = image.size
                if min(width, height) < 256:
                    errors.append(f"{path.name}: image is smaller than 256 pixels on one side")
                if image.mode not in {"RGB", "L"}:
                    errors.append(f"{path.name}: use flattened RGB or grayscale images, got {image.mode}")
                pixels = image.convert("RGB")
                digest = hashlib.sha256(f"{width},{height}:".encode() + pixels.tobytes()).hexdigest()
                if digest in seen:
                    errors.append(f"{path.name}: exact pixel duplicate of {seen[digest]}")
                seen[digest] = path.name
                records.append({"filename": path.name, "width": width, "height": height,
                                "pixel_sha256": digest, "caption": caption})
        except (OSError, ValueError) as error:
            errors.append(f"{path.name}: unreadable image ({error})")
    return records, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-dir", type=Path, default=ROOT / "data/train")
    parser.add_argument("--validation-dir", type=Path, default=ROOT / "data/validation")
    parser.add_argument("--min-train", type=int, default=20)
    parser.add_argument("--min-validation", type=int, default=4)
    args = parser.parse_args()
    trigger = json.loads((ROOT / "configs/character.json").read_text(encoding="utf-8"))["trigger"]
    train, errors = inspect(args.train_dir, trigger)
    validation, validation_errors = inspect(args.validation_dir, trigger)
    errors.extend(validation_errors)
    if len(train) < args.min_train:
        errors.append(f"Need {args.min_train} training images; found {len(train)}")
    if len(validation) < args.min_validation:
        errors.append(f"Need {args.min_validation} held-out images; found {len(validation)}")
    train_hashes = {record["pixel_sha256"] for record in train}
    for record in validation:
        if record["pixel_sha256"] in train_hashes:
            errors.append(f"Validation leakage: {record['filename']} is also in training")
    if errors:
        print("Dataset not ready:\n" + "\n".join(f"- {error}" for error in errors))
        raise SystemExit(1)
    print(f"Dataset ready: {len(train)} training images, {len(validation)} held-out images.")
    print("Manually check identity consistency, anatomy, caption accuracy, and near-duplicates.")


if __name__ == "__main__":
    main()
