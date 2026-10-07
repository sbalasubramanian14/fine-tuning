"""Loopback-only local model UI. No web packages or environment changes needed."""
import argparse
import json
import mimetypes
import re
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from catalog import ROOT, models, resolve_request

STUDIO = Path(__file__).resolve().parent
JOBS = STUDIO / 'artifacts/jobs'


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


class Controller:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = None

    def submit(self, payload):
        request = resolve_request(payload)
        with self.lock:
            if self.active:
                raise BlockingIOError('A generation is already running. Wait for it to finish.')
            job_id = uuid.uuid4().hex
            output = JOBS / job_id
            output.mkdir(parents=True)
            state = {'id': job_id, 'status': 'queued', 'message': 'Starting', 'progress': 0,
                     'created_utc': datetime.now(timezone.utc).isoformat(), 'request': request}
            write_json(output / 'request.json', request)
            write_json(output / 'state.json', state)
            self.active = job_id
        threading.Thread(target=self.run, args=(output, state), daemon=True).start()
        return dict(state)

    def run(self, output, state):
        try:
            with (output / 'worker.log').open('w', encoding='utf-8') as log:
                process = subprocess.Popen([sys.executable, '-u', str(STUDIO / 'worker.py'), str(output)], cwd=ROOT,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                           encoding='utf-8', errors='replace')
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    if line.startswith('STUDIO_EVENT:'):
                        state.update(json.loads(line[len('STUDIO_EVENT:'):]))
                        # Mark done only after the worker exits and result exists.
                        if state['status'] == 'done':
                            state['status'] = 'running'
                        with self.lock:
                            write_json(output / 'state.json', state)
                code = process.wait()
            if code:
                lines = (output / 'worker.log').read_text(encoding='utf-8').splitlines()
                raise RuntimeError(next((line for line in reversed(lines) if 'Error:' in line), 'Generation failed; inspect worker.log'))
            result = json.loads((output / 'result.json').read_text(encoding='utf-8'))
            state.update(status='done', message='Ready', progress=100, result=result)
        except Exception as error:
            state.update(status='error', message=str(error))
        finally:
            with self.lock:
                write_json(output / 'state.json', state)
                self.active = None

    def job(self, job_id):
        if not re.fullmatch(r'[0-9a-f]{32}', job_id):
            raise FileNotFoundError('Job not found')
        with self.lock:
            state = json.loads((JOBS / job_id / 'state.json').read_text(encoding='utf-8'))
        if state['status'] in {'queued', 'running'} and job_id != self.active:
            state.update(status='error', message='Server restarted before this request finished')
        return state


controller = Controller()


class Handler(BaseHTTPRequestHandler):
    def respond(self, code, value):
        body = json.dumps(value).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def file(self, path):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        if self.headers.get('Host') not in hosts:
            self.respond(403, {'error': 'Use the local studio URL'})
            return False
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://{host}' for host in hosts}:
            self.respond(403, {'error': 'Cross-origin requests are disabled'})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        path = urlsplit(self.path).path
        try:
            static = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}
            if path in static:
                return self.file(STUDIO / 'web' / static[path])
            if path == '/api/models':
                return self.respond(200, {'models': models()})
            if path == '/api/jobs':
                ids = sorted(JOBS.glob('*/state.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:30]
                return self.respond(200, {'jobs': [controller.job(p.parent.name) for p in ids]})
            match = re.fullmatch(r'/api/jobs/([0-9a-f]{32})(?:/files/([a-zA-Z0-9_.-]+))?', path)
            if match:
                state = controller.job(match[1])
                if match[2]:
                    allowed = {'request.json', 'result.json'} | {o.get('file') for o in state.get('result', {}).get('outputs', [])}
                    if match[2] not in allowed:
                        raise FileNotFoundError('File not found')
                    return self.file(JOBS / match[1] / match[2])
                return self.respond(200, state)
            self.respond(404, {'error': 'Not found'})
        except FileNotFoundError:
            self.respond(404, {'error': 'Not found'})
        except Exception as error:
            self.respond(500, {'error': str(error)})

    def do_POST(self):
        if not self.local_request():
            return
        if self.path != '/api/jobs':
            return self.respond(404, {'error': 'Not found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536 or self.headers.get_content_type() != 'application/json':
                raise ValueError('Send a JSON request under 64 KiB')
            payload = json.loads(self.rfile.read(length))
            self.respond(202, controller.submit(payload))
        except BlockingIOError as error:
            self.respond(409, {'error': str(error)})
        except (ValueError, KeyError, TypeError) as error:
            self.respond(400, {'error': str(error)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=7860)
    args = parser.parse_args()
    JOBS.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Local Model Studio: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
