"""Dispatch explicit model-family backends without changing the legacy pipeline."""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--action', choices=['all', 'download', 'baseline', 'smoke', 'train',
                                           'evaluate', 'generate', 'verify', 'preserve'], default='all')
    parser.add_argument('--run-name')
    parser.add_argument('--lora', type=Path)
    parser.add_argument('--prompt')
    args = parser.parse_args()
    if (args.lora or args.prompt) and args.action != 'generate':
        parser.error('--lora and --prompt are supported only for generate')
    profile_path = args.profile.resolve()
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    if profile.get('schema_version') != 1:
        parser.error('Unsupported profile schema')
    if (profile.get('type'), profile.get('backend')) != ('image', 'sd1_lora'):
        parser.error('This backend is not implemented; see experiments/README.md')
    if profile.get('mode') == 'legacy_reference':
        parser.error('The preserved legacy profile is read-only; use its documented original commands')
    run_name = args.run_name or datetime.now().strftime('%Y%m%d-%H%M%S')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', run_name):
        parser.error('Run name must contain only letters, numbers, underscores or hyphens')
    if args.action in {'baseline', 'smoke', 'train', 'evaluate'} and not args.run_name:
        parser.error('Supply --run-name to keep individual stages in one run')
    from backends.sd1_lora import Experiment
    experiment = Experiment(profile_path, profile, run_name)
    experiment.execute(args.action, adapter=args.lora.resolve() if args.lora else None, prompt=args.prompt)


if __name__ == '__main__':
    main()
