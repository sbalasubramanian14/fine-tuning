"""Download only pinned SDXL Base FP16 weights; no refiner or training."""
import hashlib
import json
import shutil
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[3]
PROFILE = Path(__file__).with_name('profile.json')


def download():
    profile = json.loads(PROFILE.read_text(encoding='utf-8'))
    spec = profile['model']
    model = (ROOT / spec['directory']).resolve()
    if not model.is_relative_to(PROFILE.parent / 'models'):
        raise ValueError('SDXL storage must stay in its own models folder')
    source_path = model.parent / 'model-source.json'
    if source_path.exists():
        old = json.loads(source_path.read_text(encoding='utf-8'))
        if (old['model_id'], old['revision']) != (spec['id'], spec['revision']):
            raise ValueError('Different weights already occupy this directory')
    info = HfApi().model_info(spec['id'], revision=spec['revision'], files_metadata=True)
    if info.sha != spec['revision']:
        raise ValueError('Profile must pin an exact revision')
    files = {item.rfilename: item for item in info.siblings}
    weights = [f'{component}/{"diffusion_pytorch_model" if component in ("unet", "vae") else "model"}.fp16.safetensors'
               for component in ('unet', 'vae', 'text_encoder', 'text_encoder_2')]
    needed = sum(files[name].size for name in weights if not (model / name).is_file())
    if shutil.disk_usage(ROOT).free < needed + 2**30:
        raise RuntimeError(f'Need {needed / 2**30:.2f} GiB plus 1 GiB headroom')
    small = [name for name in files if name.endswith('.json') or name.startswith(('tokenizer/', 'tokenizer_2/'))
             or name in ('README.md', 'LICENSE.md', 'LICENSE')]
    for name in small:
        hf_hub_download(spec['id'], name, revision=spec['revision'], local_dir=model)
    unet = json.loads((model / 'unet/config.json').read_text())
    if unet.get('cross_attention_dim') != 2048 or unet.get('addition_embed_type') != 'text_time':
        raise ValueError('Expected standard SDXL architecture')
    hashes = {}
    for name in weights:
        print(f'Downloading/checking {name}', flush=True)
        path = Path(hf_hub_download(spec['id'], name, revision=spec['revision'], local_dir=model))
        with path.open('rb') as handle:
            hashes[name] = hashlib.file_digest(handle, 'sha256').hexdigest()
        expected = files[name].lfs.sha256
        if hashes[name] != expected:
            raise RuntimeError(f'Source checksum mismatch: {name}')
        print(f'Verified {name}', flush=True)
    source_path.write_text(json.dumps({'model_id': spec['id'], 'revision': spec['revision'],
                                      'variant': spec['variant'], 'weight_sha256': hashes}, indent=2), encoding='utf-8')
    print('SDXL Base download complete; all four weights verified', flush=True)


if __name__ == '__main__':
    download()
