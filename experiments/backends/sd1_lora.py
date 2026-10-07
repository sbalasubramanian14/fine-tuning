"""Isolated SD1.x image backend. Existing scripts/configs are read-only inputs."""
import hashlib
import html
import json
import shutil
import subprocess
import sys
import threading
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_dataset import inspect


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def local_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Path must stay inside the repository: {value}')
    return path


class Experiment:
    def __init__(self, profile_path, profile, run_name):
        self.profile = profile
        self.profile_path = profile_path
        self.model = local_path(profile['model']['directory'])
        self.artifacts = local_path(profile['artifact_root'])
        self.cache = local_path(profile['cache_root'])
        # Writable locations must be separate from all original SD1 artifacts.
        for path in (self.model, self.artifacts, self.cache):
            if not path.is_relative_to(ROOT / 'experiments' / 'image'):
                raise ValueError('Image experiment storage must be inside experiments/image')
        for i, path in enumerate((self.model, self.artifacts, self.cache)):
            for other in (self.model, self.artifacts, self.cache)[i + 1:]:
                if path.is_relative_to(other) or other.is_relative_to(path):
                    raise ValueError('Model, artifacts and cache paths must be disjoint')
        self.run = self.artifacts / run_name
        self.character = json.loads(local_path(profile['character_config']).read_text(encoding='utf-8'))
        self.source_path = self.model.parent / 'model-source.json'
        # A clone lacks this workstation's ignored weights/latents. Protect its
        # own present files rather than requiring historical local downloads.
        self.preservation = ROOT / '.cache/experiments/preserved-sd1.json'
        self.model_verified = False

    def verify_model(self):
        if self.model_verified:
            return
        source = json.loads(self.source_path.read_text(encoding='utf-8'))
        spec = self.profile['model']
        if (source['model_id'], source['revision'], source['variant']) != (spec['id'], spec['revision'], spec['variant']):
            raise RuntimeError('Local model source differs from the experiment profile')
        hashes = source.get('weight_sha256', {})
        if len(hashes) != 4:
            raise RuntimeError('Model download is incomplete; run download first')
        for filename, expected in hashes.items():
            path = (self.model / filename).resolve()
            if not path.is_relative_to(self.model) or not path.is_file() or digest(path) != expected:
                raise RuntimeError(f'Local model weight failed integrity check: {filename}')
        self.model_verified = True

    def preserve(self):
        if self.preservation.exists():
            return self.verify()
        files = []
        for folder in ('configs', 'scripts', 'data', 'assets', 'models', 'outputs'):
            files.extend(p for p in (ROOT / folder).rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts)
        # Includes original model weights, cached latents and every prior output.
        records = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in sorted(files)}
        write_json(self.preservation, {
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'git_checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'files': records,
        })
        print(f'Preserved SHA-256 snapshot: {len(records)} original files', flush=True)

    def verify(self):
        if not self.preservation.is_file():
            raise RuntimeError('No preservation snapshot; run preserve first')
        records = json.loads(self.preservation.read_text(encoding='utf-8'))['files']
        changed = [name for name, expected in records.items()
                   if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
        if changed:
            raise RuntimeError('Preservation failed: ' + ', '.join(changed))
        print(f'Preservation verified: {len(records)} original files unchanged', flush=True)

    def download(self):
        from huggingface_hub import HfApi, hf_hub_download
        spec = self.profile['model']
        source = {'model_id': spec['id'], 'revision': spec['revision'], 'variant': spec['variant']}
        if spec['variant'] != 'fp16':
            raise ValueError('This backend downloads only the fp16 weight set')
        if self.source_path.exists():
            old = json.loads(self.source_path.read_text(encoding='utf-8'))
            if any(old.get(key) != value for key, value in source.items()):
                raise RuntimeError('Different model already occupies this directory')
        api = HfApi()
        info = api.model_info(spec['id'], revision=spec['revision'], files_metadata=True)
        if info.sha != spec['revision']:
            raise ValueError('Model revision must be an exact commit SHA')
        available = {item.rfilename: item for item in info.siblings}
        def fetch(filename):
            return Path(hf_hub_download(spec['id'], filename, revision=spec['revision'], local_dir=self.model))
        unet = json.loads(fetch('unet/config.json').read_text(encoding='utf-8'))
        if unet.get('cross_attention_dim') != 768 or unet.get('in_channels') != 4:
            raise ValueError('Only standard SD1.x models are supported')
        index = json.loads(fetch('model_index.json').read_text(encoding='utf-8'))
        if not index.get('safety_checker') or index['safety_checker'][0] is None:
            raise ValueError('This profile requires the model safety checker')
        mapping = {}
        for component in ('unet', 'vae', 'text_encoder', 'safety_checker'):
            stem = 'diffusion_pytorch_model' if component in ('unet', 'vae') else 'model'
            mapping[f'{component}/{stem}.fp16.safetensors'] = f'{component}/{stem}.safetensors'
        required_bytes = sum(available[name].size or 0 for name, target in mapping.items()
                             if not (self.model / target).exists())
        if shutil.disk_usage(ROOT).free < required_bytes + 512 * 2**20:
            raise RuntimeError(f'Need {required_bytes / 2**30:.2f} GiB plus 512 MiB headroom; previous models will not be removed')
        source['weight_mapping'] = mapping
        write_json(self.source_path, source)
        small_files = [name for name in available if name.endswith('.json') or name.startswith('tokenizer/')
                       or name in {'README.md', 'LICENSE', 'LICENSE.md'}]
        for name in small_files:
            fetch(name)
        hashes = {}
        for name, target in mapping.items():
            target_path = self.model / target
            if not target_path.is_file():
                downloaded = fetch(name)
                # Materialize standard filenames for sd-scripts; no second weight copy.
                downloaded.rename(target_path)
            hashes[target] = digest(target_path)
            expected = available[name].lfs.sha256 if available[name].lfs else None
            if expected and hashes[target] != expected:
                raise RuntimeError(f'Weight checksum differs from pinned Hugging Face source: {target}')
        source['weight_sha256'] = hashes
        source['local_filename_note'] = 'Pinned fp16 variant renamed to default filenames for sd-scripts compatibility; tensors unchanged.'
        write_json(self.source_path, source)
        print(f'Downloaded pinned fp16 model: {self.model}', flush=True)

    def dataset(self):
        spec = self.profile['dataset']
        train, errors = inspect(local_path(spec['train']), self.character['trigger'])
        validation, extra = inspect(local_path(spec['validation']), self.character['trigger'])
        errors.extend(extra)
        if len(train) < spec['min_train'] or len(validation) < spec['min_validation']:
            errors.append('Insufficient training or held-out images')
        if {r['pixel_sha256'] for r in train} & {r['pixel_sha256'] for r in validation}:
            errors.append('Train/validation leakage')
        if errors:
            raise ValueError('\n'.join(errors))
        source_records = {}
        for split, records in (('train', train), ('validation', validation)):
            for record in records:
                image = local_path(spec[split]) / record['filename']
                for path in (image, image.with_suffix('.txt')):
                    source_records[f'{split}/{path.name}'] = digest(path)
        key = hashlib.sha256(json.dumps({'model': self.profile['model'], 'files': source_records}, sort_keys=True).encode()).hexdigest()[:20]
        directory = self.cache / 'datasets' / key
        for split, records in (('train', train), ('validation', validation)):
            destination = directory / split
            destination.mkdir(parents=True, exist_ok=True)
            for record in records:
                image = local_path(spec[split]) / record['filename']
                for path in (image, image.with_suffix('.txt')):
                    target = destination / path.name
                    if target.exists() and digest(target) != source_records[f'{split}/{path.name}']:
                        raise RuntimeError(f'Working dataset modified: {target}')
                    if not target.exists():
                        shutil.copy2(path, target)
        write_json(directory / 'source.json', {'model': self.profile['model'], 'files': source_records})
        print(f'Dataset: {len(train)} train / {len(validation)} held-out; isolated cache {key}', flush=True)
        return directory, train, validation

    def new_stage(self, name):
        path = self.run / name
        if path.exists():
            raise RuntimeError(f'Stage exists, refusing overwrite: {path}')
        path.mkdir(parents=True)
        return path

    def train(self, smoke=False):
        self.verify_model()
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA unavailable')
        directory, train, validation = self.dataset()
        output = self.new_stage('smoke' if smoke else 'train')
        steps = self.profile['smoke_steps' if smoke else 'steps']
        config = tomllib.loads(local_path(self.profile['dataset_config']).read_text(encoding='utf-8'))
        dataset_text = local_path(self.profile['dataset_config']).read_text(encoding='utf-8')
        original = config['datasets'][0]['subsets'][0]['image_dir']
        dataset_text = dataset_text.replace(f'image_dir = "{original}"', f'image_dir = "{(directory / "train").as_posix()}"')
        (output / 'dataset.toml').write_text(dataset_text, encoding='utf-8')
        import re
        train_text = local_path(self.profile['training_config']).read_text(encoding='utf-8')
        train_text = re.sub(r'(?m)^max_train_steps = \d+$', f'max_train_steps = {steps}', train_text)
        train_text = re.sub(r'(?m)^logging_dir = .*$', f'logging_dir = "{(output / "logs").as_posix()}"', train_text)
        (output / 'train.toml').write_text(train_text, encoding='utf-8')
        trainer = ROOT / 'vendor/sd-scripts/train_network.py'
        manifest = {'profile': self.profile, 'character': self.character,
                    'model': json.loads(self.source_path.read_text(encoding='utf-8')),
                    'training_images': train, 'held_out_images': validation,
                    'trainer_revision': subprocess.check_output(['git', '-C', str(trainer.parent), 'rev-parse', 'HEAD'], text=True).strip(),
                    'gpu': torch.cuda.get_device_name(0), 'steps_requested': steps}
        write_json(output / 'manifest.json', manifest)
        with (output / 'packages.txt').open('w', encoding='utf-8') as handle:
            subprocess.run([sys.executable, '-m', 'pip', 'freeze', '--all'], stdout=handle, check=True)
        arguments = [sys.executable, '-m', 'accelerate.commands.launch', '--num_processes=1', '--num_machines=1',
                     '--mixed_precision=fp16', '--num_cpu_threads_per_process=2', str(trainer),
                     '--config_file', str(output / 'train.toml'), '--dataset_config', str(output / 'dataset.toml'),
                     '--pretrained_model_name_or_path', str(self.model), '--output_dir', str(output),
                     '--output_name', 'sora', '--max_train_steps', str(steps)]
        samples, stop = [], threading.Event()
        def monitor():
            while not stop.is_set():
                try:
                    sample = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu,temperature.gpu',
                                                      '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
                    samples.append({'elapsed_seconds': round(time.monotonic() - started, 2), 'memory_mib,utilization_percent,temperature_c': sample})
                except (OSError, subprocess.SubprocessError):
                    pass
                stop.wait(2)
        started = time.monotonic()
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        try:
            with (output / 'training.log').open('w', encoding='utf-8') as log:
                process = subprocess.Popen(arguments, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, encoding='utf-8', errors='replace')
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    print(line, end='', flush=True)
                code = process.wait()
            if code:
                raise RuntimeError(f'Trainer failed ({code}); see {output / "training.log"}')
            from safetensors import safe_open
            with safe_open(output / 'sora.safetensors', framework='pt') as handle:
                if int(handle.metadata()['ss_steps']) != steps:
                    raise RuntimeError('Adapter step count does not match requested training')
                if not all(torch.isfinite(handle.get_tensor(key)).all().item() for key in handle.keys()):
                    raise RuntimeError('Adapter contains non-finite tensors')
            manifest['adapter_sha256'] = digest(output / 'sora.safetensors')
            manifest['completed'] = True
        finally:
            stop.set()
            thread.join(timeout=12)
            manifest['wall_seconds'] = round(time.monotonic() - started, 2)
            write_json(output / 'manifest.json', manifest)
            write_json(output / 'gpu-samples.json', samples)
        print(f'Training completed: {output}', flush=True)

    def generate(self, name, adapter=None, solo=False, prompt=None):
        self.verify_model()
        import torch
        from diffusers import StableDiffusionPipeline
        output = self.new_stage(name)
        settings = self.profile['evaluation']
        pipe = StableDiffusionPipeline.from_pretrained(self.model, torch_dtype=torch.float16, local_files_only=True)
        if pipe.safety_checker is None:
            raise RuntimeError('Expected safety checker was not loaded')
        if adapter:
            pipe.load_lora_weights(str(adapter.parent), weight_name=adapter.name, local_files_only=True)
        pipe.enable_model_cpu_offload()
        pipe.enable_vae_slicing()
        prompts = [prompt] if prompt else ([settings['solo_prompt']] if solo else self.character['evaluation_prompts'])
        metadata = {'model': json.loads(self.source_path.read_text(encoding='utf-8')),
                    'lora': str(adapter) if adapter else None,
                    'scale': settings['lora_scale'], 'seed': settings['seed'], 'prompts': prompts,
                    'negative_prompt': self.character['negative_prompt'], 'steps': settings['steps'],
                    'guidance_scale': settings['guidance_scale'], 'width': settings['width'], 'height': settings['height'],
                    'scheduler': type(pipe.scheduler).__name__, 'scheduler_config': dict(pipe.scheduler.config),
                    'images': []}
        started = time.monotonic()
        for index, prompt in enumerate(prompts, 1):
            kwargs = {'cross_attention_kwargs': {'scale': settings['lora_scale']}} if adapter else {}
            result = pipe(prompt=prompt, negative_prompt=self.character['negative_prompt'], width=settings['width'],
                          height=settings['height'], num_inference_steps=settings['steps'], guidance_scale=settings['guidance_scale'],
                          generator=torch.Generator(device='cpu').manual_seed(settings['seed']), **kwargs)
            result.images[0].save(output / f'{index:02d}.png')
            metadata['images'].append({'file': f'{index:02d}.png', 'nsfw_content_detected': bool(result.nsfw_content_detected[0])})
            write_json(output / 'generation.json', metadata)
        metadata['wall_seconds'] = round(time.monotonic() - started, 2)
        write_json(output / 'generation.json', metadata)
        del pipe
        import gc
        gc.collect()
        torch.cuda.empty_cache()
        print(f'Generated: {output}', flush=True)

    def evaluate(self):
        for step in self.profile['evaluation']['checkpoints']:
            adapter = self.run / 'train' / f'sora-step{step:08d}.safetensors'
            if not adapter.is_file():
                raise RuntimeError(f'Checkpoint missing: {adapter}')
            self.generate(f'step-{step}', adapter)
        self.generate('solo-baseline', solo=True)
        self.generate('solo-final', self.run / 'train/sora.safetensors', solo=True)
        self.gallery()

    def gallery(self):
        from PIL import Image, ImageDraw
        count = len(self.character['evaluation_prompts'])
        labels = self.profile['evaluation'].get('labels')
        if labels is None:
            labels = ['Portrait', 'Mountain path', 'Cafe', 'Blue sweater'] if count == 4 else [f'Prompt {n}' for n in range(1, count + 1)]
        if len(labels) != count:
            raise ValueError('Evaluation labels must match prompt count')
        folders = ['baseline'] + [f'step-{step}' for step in self.profile['evaluation']['checkpoints']]
        title = html.escape(f'{self.profile["id"]}: {self.character.get("name", "image comparison")}')
        evaluation = self.profile['evaluation']
        width, height = evaluation['width'], evaluation['height']
        parts = [f'<!doctype html><meta charset="utf-8"><title>{title}</title>',
                 '<style>body{font:16px system-ui;max-width:1300px;margin:auto;padding:24px}img{width:100%}.row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}small{display:block}</style>',
                 f'<h1>{title}</h1><p>Seed {evaluation["seed"]}, {evaluation["steps"]} steps, guidance {evaluation["guidance_scale"]}, {width} x {height}, LoRA strength {evaluation["lora_scale"]}. Same prompts for each checkpoint. Held-out images are never trained.</p>']
        reference = None
        for folder in folders:
            settings = json.loads((self.run / folder / 'generation.json').read_text(encoding='utf-8'))
            if reference is None:
                reference = settings
            for key in ('model', 'seed', 'prompts', 'negative_prompt', 'steps', 'guidance_scale', 'width', 'height', 'scheduler', 'scheduler_config'):
                if settings[key] != reference[key]:
                    raise RuntimeError(f'Mismatched evaluation setting: {key}')
            sheet = Image.new('RGB', (width * 2, (height + 36) * ((count + 1) // 2)), 'white')
            draw = ImageDraw.Draw(sheet)
            parts.append(f'<h2>{html.escape(folder)}</h2><div class="row">')
            for index, label in enumerate(labels, 1):
                x, y = ((index - 1) % 2) * width, ((index - 1) // 2) * (height + 36)
                draw.text((x + 12, y + 10), f'{folder}: {label}', fill='black')
                with Image.open(self.run / folder / f'{index:02d}.png') as image:
                    sheet.paste(image.convert('RGB'), (x, y + 36))
                flag = settings['images'][index - 1]['nsfw_content_detected']
                parts.append(f'<div><img src="{folder}/{index:02d}.png"><small>{label}; filtered={flag}</small></div>')
            sheet.save(self.run / f'{folder}-sheet.png')
            parts.append('</div>')
        parts.append('<h2>Matched solo portrait</h2><div class="row"><img src="solo-baseline/01.png"><img src="solo-final/01.png"></div>')
        (self.run / 'comparison.html').write_text('\n'.join(parts), encoding='utf-8')

    def execute(self, action, adapter=None, prompt=None):
        if action in {'verify', 'preserve'}:
            return getattr(self, action)()
        self.preserve()
        if action == 'all' and self.run.exists():
            raise RuntimeError(f'Run exists, use a new name: {self.run}')
        self.run.mkdir(parents=True, exist_ok=True)
        recorded = self.run / 'profile.json'
        if recorded.exists() and json.loads(recorded.read_text(encoding='utf-8')) != self.profile:
            raise RuntimeError('Run profile changed; use a fresh run name')
        write_json(recorded, self.profile)
        print(f'Experiment run: {self.run}', flush=True)
        try:
            if action == 'all':
                self.download()
                self.dataset()
                self.generate('baseline')
                self.train(smoke=True)
                self.train()
                self.evaluate()
            elif action == 'download':
                self.download()
            elif action == 'baseline':
                self.generate('baseline')
            elif action == 'smoke':
                self.train(smoke=True)
            elif action == 'train':
                self.train()
            elif action == 'evaluate':
                self.evaluate()
            elif action == 'generate':
                self.generate('inference', adapter, prompt=prompt)
        finally:
            self.verify()
