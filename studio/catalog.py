"""Expose local experiment profiles and only adapters belonging to each model."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIZES = ['512x512', '384x576', '512x768', '768x512']


def local(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Profile path leaves the repository')
    return path


def image_models():
    models = []
    for path in sorted((ROOT / 'experiments/image').glob('*/profile.json')):
        profile = json.loads(path.read_text(encoding='utf-8'))
        if profile.get('backend') != 'sd1_lora' or profile.get('type') != 'image':
            continue
        model_dir = local(profile['model']['directory'])
        character = json.loads(local(profile.get('character_config', 'configs/character.json')).read_text(encoding='utf-8'))
        if profile.get('mode') == 'legacy_reference':
            files = list(local(profile['training_run']).glob('*.safetensors'))
        else:
            # Prefer versioned exports when both raw and exported runs exist.
            by_run = {}
            for base in (local(profile['artifact_root']), path.parent / 'results'):
                for adapter in sorted(base.glob('*/train/*.safetensors')):
                    by_run[(adapter.parent.parent.name, adapter.name)] = adapter
            files = list(by_run.values())
        adapters = []
        for adapter in sorted(files, key=lambda p: (p.name != 'sora.safetensors', str(p))):
            from safetensors import safe_open
            run = adapter.parent.name if profile.get('mode') == 'legacy_reference' else adapter.parent.parent.name
            with safe_open(adapter, framework='np') as handle:
                count = handle.metadata().get('ss_steps', '?')
            step = f'{"Final · " if "step" not in adapter.stem else ""}{count} steps'
            adapters.append({'id': adapter.relative_to(ROOT).as_posix(), 'label': f'{step} · {run}'})
        label = {'Lykon/dreamshaper-8': 'DreamShaper 8', 'hakurei/waifu-diffusion': 'Waifu Diffusion 1.3'}.get(profile['model']['id'], profile['model']['id'])
        models.append({'id': profile['id'], 'label': f'{label} · {character.get("name", "image")}',
                       'type': 'image', 'backend': 'image_sd1', 'profile': path.relative_to(ROOT).as_posix(),
                       'available': (model_dir / 'model_index.json').is_file(), 'adapters': adapters,
                       'default_prompt': profile.get('evaluation', {}).get('solo_prompt') or f'{character["trigger"]}, solo, {character["identity"]}, portrait, anime illustration',
                       'fields': [
                           {'id': 'negative_prompt', 'label': 'Negative prompt', 'type': 'textarea', 'default': character['negative_prompt']},
                           {'id': 'seed', 'label': 'Seed', 'type': 'number', 'default': 42, 'min': 0, 'max': 2147483647, 'step': 1},
                           {'id': 'steps', 'label': 'Steps', 'type': 'number', 'default': 28, 'min': 1, 'max': 60, 'step': 1},
                           {'id': 'guidance', 'label': 'Guidance', 'type': 'number', 'default': 7, 'min': 1, 'max': 15, 'step': 0.5},
                           {'id': 'size', 'label': 'Image size', 'type': 'select', 'default': '512x512', 'options': SIZES},
                           {'id': 'image_filter', 'label': 'Image filter', 'type': 'select', 'default': 'On', 'options': ['On', 'Off']},
                           {'id': 'strength', 'label': 'LoRA strength', 'type': 'number', 'default': 0.8, 'min': 0, 'max': 2, 'step': 0.1}
                       ]})
    return models


# Register new modality-specific catalog providers and matching worker backends.
PROVIDERS = [image_models]


def models():
    return [model for provider in PROVIDERS for model in provider()]


def resolve_request(payload):
    import math
    if not isinstance(payload, dict):
        raise ValueError('Request must be a JSON object')
    model = next((m for m in models() if m['id'] == payload.get('model')), None)
    if model is None or not model['available']:
        raise ValueError('Select an available local model')
    prompt = payload.get('prompt', '')
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
        raise ValueError('Enter a prompt between 1 and 4000 characters')
    mode = payload.get('mode', 'generate')
    if mode not in {'generate', 'compare'}:
        raise ValueError('Unknown generation mode')
    adapter_id = payload.get('adapter')
    adapter = next((a for a in model['adapters'] if a['id'] == adapter_id), None) if adapter_id else None
    if adapter_id and adapter is None:
        raise ValueError('Choose an adapter belonging to this base model')
    if mode == 'compare' and adapter is None:
        raise ValueError('Select a LoRA to compare it with the base')
    settings = payload.get('settings', {})
    if not isinstance(settings, dict):
        raise ValueError('Settings must be an object')
    clean = {}
    for field in model['fields']:
        key = field['id']
        value = settings.get(key, field['default'])
        if field['type'] == 'number':
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f'{field["label"]} must be a finite number')
            if not field['min'] <= value <= field['max'] or (field['step'] == 1 and value != int(value)):
                raise ValueError(f'{field["label"]} is outside its supported range')
        elif field['type'] == 'select':
            if value not in field['options']:
                raise ValueError(f'Unsupported {field["label"]}')
        elif not isinstance(value, str) or len(value) > 2000:
            raise ValueError(f'{field["label"]} must be at most 2000 characters')
        clean[key] = value
    return {'model': model['id'], 'model_label': model['label'], 'backend': model['backend'],
            'profile': model['profile'], 'adapter': adapter['id'] if adapter else None,
            'prompt': prompt.strip(), 'mode': mode, 'settings': clean}
