"""Local SD1.x prompt/LoRA comparison backend; base files remain read-only."""
import hashlib
import json
import time
from pathlib import Path

from catalog import ROOT, local


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def run(request, output, emit):
    import torch
    from diffusers import StableDiffusionPipeline
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable. Run the repository setup and check the driver.')
    profile = json.loads(local(request['profile']).read_text(encoding='utf-8'))
    model = local(profile['model']['directory'])
    unet = json.loads((model / 'unet/config.json').read_text(encoding='utf-8'))
    if unet.get('cross_attention_dim') != 768 or unet.get('in_channels') != 4:
        raise RuntimeError('This backend supports SD1.x image models')
    source_path = model.parent / 'model-source.json'
    source = json.loads(source_path.read_text(encoding='utf-8'))
    if (source['model_id'], source['revision']) != (profile['model']['id'], profile['model']['revision']):
        raise RuntimeError('Local model source differs from the selected profile')
    emit({'status': 'running', 'message': 'Checking and loading model', 'progress': 2})
    weights = {}
    for component in ('unet', 'vae', 'text_encoder', 'safety_checker'):
        files = list((model / component).glob('*.safetensors')) or list((model / component).glob('*.bin'))
        if len(files) != 1:
            raise RuntimeError(f'Expected one weight file for {component}')
        key = files[0].relative_to(model).as_posix()
        weights[key] = sha(files[0])
        expected = source.get('weight_sha256', {}).get(key)
        if expected and expected != weights[key]:
            raise RuntimeError(f'Model integrity check failed: {component}')
    settings = request['settings']
    filter_enabled = settings.get('image_filter', 'On') == 'On'
    loader_options = {} if filter_enabled else {'safety_checker': None, 'requires_safety_checker': False}
    pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float16, local_files_only=True, **loader_options)
    if filter_enabled and pipe.safety_checker is None:
        raise RuntimeError('The expected inference safety checker is missing')
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_slicing()
    width, height = map(int, settings['size'].split('x'))
    modes = ['base', 'lora'] if request['mode'] == 'compare' else ['lora' if request['adapter'] else 'base']
    metadata = {'request': request, 'model_source': source, 'weight_sha256': weights,
                'image_filter_enabled': filter_enabled,
                'scheduler': type(pipe.scheduler).__name__, 'scheduler_config': dict(pipe.scheduler.config),
                'adapter_sha256': sha(local(request['adapter'])) if request['adapter'] else None,
                'outputs': []}
    started = time.monotonic()
    for index, mode in enumerate(modes):
        if mode == 'lora':
            adapter = local(request['adapter'])
            pipe.load_lora_weights(str(adapter.parent), weight_name=adapter.name, local_files_only=True)
        label = 'With LoRA' if mode == 'lora' else 'Base model'
        def callback(pipeline, step, timestep, kwargs):
            emit({'status': 'running', 'message': f'{label} · step {step + 1}/{int(settings["steps"])}',
                  'progress': round(10 + 85 * (index + (step + 1) / settings['steps']) / len(modes))})
            return kwargs
        extra = {'cross_attention_kwargs': {'scale': settings['strength']}} if mode == 'lora' else {}
        result = pipe(request['prompt'], negative_prompt=settings['negative_prompt'], width=width, height=height,
                      num_inference_steps=int(settings['steps']), guidance_scale=settings['guidance'],
                      generator=torch.Generator(device='cpu').manual_seed(int(settings['seed'])),
                      callback_on_step_end=callback, **extra)
        filename = f'{mode}.png'
        result.images[0].save(output / filename)
        metadata['outputs'].append({'kind': 'image', 'label': label, 'file': filename,
                                    'filtered': bool(result.nsfw_content_detected[0]) if result.nsfw_content_detected is not None else False})
    metadata['generation_seconds'] = round(time.monotonic() - started, 2)
    return metadata
