"""Export a completed image experiment for review and Git, excluding models/caches/logs."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=Path, default=ROOT / 'experiments/image/dreamshaper8/profile.json')
    parser.add_argument('--run-name', required=True)
    args = parser.parse_args()
    profile_path = args.profile.resolve()
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    source_root = (ROOT / profile['artifact_root']).resolve()
    source = (source_root / args.run_name).resolve()
    destination_root = profile_path.parent / 'results'
    destination = (destination_root / args.run_name).resolve()
    if not source.is_relative_to(source_root) or not destination.is_relative_to(destination_root):
        parser.error('Run name escapes its storage directory')
    if not source.is_relative_to(ROOT / 'experiments/image') or not destination.is_relative_to(ROOT / 'experiments/image'):
        parser.error('Export must stay inside image experiment storage')
    manifest = json.loads((source / 'train/manifest.json').read_text(encoding='utf-8'))
    if not manifest.get('completed'):
        parser.error('Training is incomplete')
    with (source / 'train/sora.safetensors').open('rb') as handle:
        if hashlib.file_digest(handle, 'sha256').hexdigest() != manifest['adapter_sha256']:
            parser.error('Final adapter differs from its training manifest')
    folders = ['baseline', 'solo-baseline', 'solo-final'] + [f'step-{n}' for n in profile['evaluation']['checkpoints']]
    if (source / 'inference/generation.json').is_file():
        folders.append('inference')
    paths = [source / 'profile.json', source / 'comparison.html']
    paths += list(source.glob('*-sheet.png'))
    paths += [source / 'train' / name for name in ('manifest.json', 'train.toml', 'dataset.toml', 'packages.txt', 'gpu-samples.json')]
    paths += sorted((source / 'train').glob('*.safetensors'))
    for folder in folders:
        metadata_path = source / folder / 'generation.json'
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        if len(metadata['images']) != len(metadata['prompts']):
            parser.error(f'Generation incomplete: {folder}')
        paths.append(metadata_path)
        paths += [source / folder / image['file'] for image in metadata['images']]
    if destination.exists():
        parser.error(f'Export already exists: {destination}')
    if not all(path.is_file() for path in paths):
        parser.error('Required result files are missing')
    for path in paths:
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    from safetensors import safe_open
    import numpy as np
    adapters = {}
    for path in sorted((destination / 'train').glob('*.safetensors')):
        with safe_open(path, framework='np') as handle:
            if not all(np.isfinite(handle.get_tensor(key)).all() for key in handle.keys()):
                raise RuntimeError(f'Non-finite adapter: {path.name}')
            metadata = handle.metadata()
            adapters[path.name] = {'steps': int(metadata['ss_steps']), 'finite': True,
                                   'training_seconds': float(metadata['ss_training_finished_at']) - float(metadata['ss_training_started_at'])}
    samples = json.loads((source / 'train/gpu-samples.json').read_text(encoding='utf-8'))
    values = [list(map(float, sample['memory_mib,utilization_percent,temperature_c'].split(',')[0:3])) for sample in samples]
    metrics = {'wall_seconds_including_trainer_launch': manifest['wall_seconds'], 'adapters': adapters,
               'gpu_samples': len(samples), 'sampled_max_total_device_vram_mib': max(v[0] for v in values) if values else None,
               'sampled_max_temperature_c': max(v[2] for v in values) if values else None,
               'note': 'nvidia-smi sampled every approximately two seconds; total device memory, not a CUDA allocator peak.'}
    (destination / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(f'Exported {len(paths)} files to {destination}')


if __name__ == '__main__':
    main()
