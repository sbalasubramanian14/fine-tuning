"""SDXL Base inference only, with offloading for smaller GPUs."""
import gc
import hashlib
import json
import time

from catalog import local


def run(request, output, emit):
    import torch
    from diffusers import StableDiffusionXLPipeline
    if request.get('adapter') or request['mode'] != 'generate':
        raise ValueError('This SDXL backend supports base generation only')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable')
    profile = json.loads(local(request['profile']).read_text(encoding='utf-8'))
    model = local(profile['model']['directory'])
    source = json.loads((model.parent / 'model-source.json').read_text(encoding='utf-8'))
    if (source['model_id'], source['revision'], source['variant']) != (
            profile['model']['id'], profile['model']['revision'], 'fp16'):
        raise RuntimeError('Local SDXL source differs from the profile')
    config = json.loads((model / 'unet/config.json').read_text())
    if config.get('cross_attention_dim') != 2048 or config.get('addition_embed_type') != 'text_time':
        raise RuntimeError('Expected SDXL Base architecture')
    expected_files = [f'{component}/{"diffusion_pytorch_model" if component in ("unet", "vae") else "model"}.fp16.safetensors'
                      for component in ('unet', 'vae', 'text_encoder', 'text_encoder_2')]
    emit({'status': 'running', 'message': 'Checking SDXL weights', 'progress': 2})
    hashes = {}
    for name in expected_files:
        with (model / name).open('rb') as handle:
            hashes[name] = hashlib.file_digest(handle, 'sha256').hexdigest()
        if hashes[name] != source.get('weight_sha256', {}).get(name):
            raise RuntimeError(f'SDXL integrity check failed: {name}')
    settings = request['settings']
    width, height = map(int, settings['size'].split('x'))
    requested_mode = settings.get('memory_mode', 'Low VRAM')
    modes = ['Balanced', 'Low VRAM'] if requested_mode == 'Balanced' else ['Low VRAM']
    load_started = time.monotonic()
    for mode in modes:
        emit({'status': 'running', 'message': f'Loading SDXL · {mode}', 'progress': 5})
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model, torch_dtype=torch.float16, variant='fp16', use_safetensors=True,
            local_files_only=True, low_cpu_mem_usage=True, add_watermarker=False)
        pipe.set_progress_bar_config(disable=True)
        pipe.enable_vae_tiling()
        pipe.enable_vae_slicing()
        if mode == 'Low VRAM':
            pipe.enable_sequential_cpu_offload()
        else:
            pipe.enable_model_cpu_offload()
        torch.cuda.reset_peak_memory_stats()
        def callback(pipeline, step, timestep, kwargs):
            emit({'status': 'running', 'message': f'SDXL · step {step + 1}/{int(settings["steps"])} · {mode}',
                  'progress': round(10 + 85 * (step + 1) / settings['steps'])})
            return kwargs
        started = time.monotonic()
        retry = False
        try:
            result = pipe(request['prompt'], negative_prompt=settings['negative_prompt'],
                          width=width, height=height, num_inference_steps=int(settings['steps']),
                          guidance_scale=settings['guidance'],
                          generator=torch.Generator(device='cpu').manual_seed(int(settings['seed'])),
                          callback_on_step_end=callback)
            result.images[0].save(output / 'base.png')
            metadata = {'request': request, 'model_source': source, 'weight_sha256': hashes,
                        'adapter_sha256': None, 'image_filter_enabled': False, 'image_filter_available': False,
                        'scheduler': type(pipe.scheduler).__name__, 'scheduler_config': dict(pipe.scheduler.config),
                        'memory_mode_effective': mode, 'memory_fallback': mode != requested_mode,
                        'gpu_peak_allocated_mib': round(torch.cuda.max_memory_allocated() / 2**20, 1),
                        'gpu_peak_reserved_mib': round(torch.cuda.max_memory_reserved() / 2**20, 1),
                        'generation_seconds': round(time.monotonic() - started, 2),
                        'load_and_generation_seconds': round(time.monotonic() - load_started, 2),
                        'outputs': [{'kind': 'image', 'label': 'SDXL Base', 'file': 'base.png', 'filtered': False}]}
        except torch.cuda.OutOfMemoryError:
            if mode == 'Low VRAM':
                raise
            retry = True
            emit({'status': 'running', 'message': 'GPU memory limit reached; retrying with Low VRAM offloading', 'progress': 5})
        finally:
            pipe = None
            gc.collect()
            torch.cuda.empty_cache()
        if not retry:
            return metadata
