"""Verify browser job data cannot enter an ordinary git add/push workflow."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LocalStorageTests(unittest.TestCase):
    def test_all_browser_runtime_files_are_ignored(self):
        paths = [f'studio/artifacts/jobs/example/{name}' for name in
                 ('request.json', 'state.json', 'result.json', 'worker.log',
                  'base.png', 'lora.png', 'voice.wav', 'video.mp4')]
        result = subprocess.run(['git', 'check-ignore', '--no-index', '-z', '--stdin'],
                                cwd=ROOT, input=('\0'.join(paths) + '\0').encode(),
                                capture_output=True, check=True)
        self.assertEqual(set(result.stdout.decode().rstrip('\0').split('\0')), set(paths))

    def test_no_browser_runtime_files_are_tracked(self):
        result = subprocess.run(['git', 'ls-files', '--', 'studio/artifacts'],
                                cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.strip(), '', 'Browser data must not be tracked')


if __name__ == '__main__':
    unittest.main()
