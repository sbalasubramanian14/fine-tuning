"""Record hashes, actual captions, provenance, and completed visual reviews."""
import json
import html
from pathlib import Path

from validate_dataset import inspect

ROOT = Path(__file__).resolve().parents[1]


def write_gallery(records):
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>Sora character dataset</title>',
             '<style>body{font:16px/1.5 system-ui,sans-serif;margin:32px auto;max-width:1280px;padding:0 24px;background:#f5f3ee;color:#232323}h1{font-size:36px;margin-bottom:8px}h2{margin-top:48px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px}figure{margin:0}img{width:100%;height:360px;object-fit:contain;background:#e8e5de}figcaption{padding:8px 0}small{display:block;color:#555;font-size:13px}a{color:inherit}</style>',
             '<h1>Sora character dataset</h1>',
             '<p>Original adult sky courier. Synthetic reference images for a local LoRA experiment. Click an image to view it at full size.</p>']
    for split, label in [('train', 'Training images'), ('validation', 'Held-out references')]:
        subset = [record for record in records if record['split'] == split]
        parts.append(f'<h2>{label} ({len(subset)})</h2><div class="grid">')
        for record in subset:
            image_url = html.escape('../' + record['image'], quote=True)
            caption = html.escape(record['caption'])
            image_id = html.escape(record['id'])
            parts.append(f'<figure><a href="{image_url}"><img src="{image_url}" alt="Sora image {image_id}" loading="lazy"></a><figcaption><b>{image_id}</b><small>{caption}</small></figcaption></figure>')
        parts.append('</div>')
    parts.append('</html>')
    (ROOT / 'docs/dataset-gallery.html').write_text('\n'.join(parts), encoding='utf-8')


def main():
    character = json.loads((ROOT / 'configs/character.json').read_text(encoding='utf-8'))
    records = []
    for split in ('train', 'validation'):
        images, errors = inspect(ROOT / 'data' / split, character['trigger'])
        if errors:
            raise SystemExit('\n'.join(errors))
        for image in images:
            source_path = ROOT / 'docs/dataset-sources' / (Path(image['filename']).stem + '.json')
            source = json.loads(source_path.read_text(encoding='utf-8'))
            if not source['review'].startswith('Accepted:'):
                raise SystemExit(f"Visual review incomplete: {image['filename']}")
            # Use the corrected caption from disk rather than the initial generation caption.
            source['caption'] = image['caption']
            source.update({key: image[key] for key in ('width', 'height', 'pixel_sha256')})
            source_path.write_text(json.dumps(source, indent=2), encoding='utf-8')
            records.append(source)
    manifest = {'character': character['name'], 'trigger': character['trigger'],
                'kind': 'synthetic images generated with the built-in imagegen tool',
                'reference': 'assets/sora-reference.png',
                'train_count': sum(record['split'] == 'train' for record in records),
                'validation_count': sum(record['split'] == 'validation' for record in records),
                'images': records}
    (ROOT / 'docs/dataset-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    write_gallery(records)
    print(f"Recorded {manifest['train_count']} training and {manifest['validation_count']} held-out images.")


if __name__ == '__main__':
    main()
