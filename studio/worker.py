"""A process per GPU request releases memory between models and adapters."""
import json
import sys
from pathlib import Path

from backends.image_sd1 import run as image_run
from backends.image_sdxl import run as sdxl_run

BACKENDS = {'image_sd1': image_run, 'image_sdxl': sdxl_run}


def emit(event):
    print('STUDIO_EVENT:' + json.dumps(event), flush=True)


if __name__ == '__main__':
    output = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parent / 'artifacts/jobs'
    if not output.is_relative_to(root):
        raise ValueError('Job output leaves studio storage')
    request = json.loads((output / 'request.json').read_text(encoding='utf-8'))
    result = BACKENDS[request['backend']](request, output, emit)
    (output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    emit({'status': 'done', 'message': 'Ready', 'progress': 100})
