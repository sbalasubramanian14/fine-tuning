"""Make each run self-contained and record exactly what it was trained on."""
import argparse
import json
import re
import subprocess
import tomllib
from pathlib import Path

from validate_dataset import inspect

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=400)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    dataset = (ROOT / "configs/dataset.toml").read_text(encoding="utf-8")
    relative_path = tomllib.loads(dataset)["datasets"][0]["subsets"][0]["image_dir"]
    absolute_path = (ROOT / relative_path).resolve().as_posix()
    dataset = dataset.replace(f'image_dir = "{relative_path}"', f'image_dir = "{absolute_path}"')
    (output / "dataset.toml").write_text(dataset, encoding="utf-8")
    train_config = (ROOT / "configs/train.toml").read_text(encoding="utf-8")
    train_config = re.sub(r"(?m)^max_train_steps = \d+$", f"max_train_steps = {args.steps}", train_config)
    (output / "train.toml").write_text(train_config, encoding="utf-8")
    character = json.loads((ROOT / "configs/character.json").read_text(encoding="utf-8"))
    model_source = json.loads((ROOT / "models/model-source.json").read_text(encoding="utf-8"))
    train, errors = inspect(ROOT / relative_path, character["trigger"])
    if errors:
        raise SystemExit("\n".join(errors))
    trainer_revision = subprocess.check_output(
        ["git", "-C", str(ROOT / "vendor/sd-scripts"), "rev-parse", "HEAD"], text=True
    ).strip()
    manifest = {"character": character, "model": model_source, "trainer_revision": trainer_revision,
                "training_images": train}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with (output / "packages.txt").open("w", encoding="utf-8") as handle:
        subprocess.run([__import__("sys").executable, "-m", "pip", "freeze", "--all"],
                       stdout=handle, check=True)


if __name__ == "__main__":
    main()
