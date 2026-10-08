"""Deletion checks use disposable fixtures, never the user's saved tests."""
import json
import shutil
import threading
import unittest
import uuid
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import server


class DeleteTests(unittest.TestCase):
    def setUp(self):
        self.base = server.ROOT / '.cache' / ('studio-delete-test-' + uuid.uuid4().hex)
        self.jobs = self.base / 'artifacts/jobs'
        self.jobs.mkdir(parents=True)
        self.targets = []
        for _ in range(2):
            path = self.jobs / uuid.uuid4().hex
            path.mkdir()
            for name in ('request.json', 'state.json', 'result.json', 'base.png', 'worker.log'):
                (path / name).write_bytes(b'test fixture')
            self.targets.append(path)
        self.sentinel = self.base / 'models/keep.txt'
        self.sentinel.parent.mkdir()
        self.sentinel.write_text('keep')
        self.controller = server.Controller()
        for attribute, value in [('STUDIO', self.base), ('JOBS', self.jobs), ('controller', self.controller)]:
            change = patch.object(server, attribute, value)
            change.start()
            self.addCleanup(change.stop)

    def tearDown(self):
        resolved = self.base.resolve()
        if not resolved.is_relative_to(server.ROOT / '.cache'):
            raise ValueError('Fixture cleanup leaves test storage')
        shutil.rmtree(resolved)

    def test_deletes_job_folders_and_preserves_other_storage(self):
        self.assertEqual(self.controller.delete_all(), 2)
        self.assertTrue(all(not path.exists() for path in self.targets))
        self.assertTrue(self.sentinel.is_file())
        self.assertEqual(self.controller.delete_all(), 0)

    def test_active_generation_blocks_deletion(self):
        self.controller.active = self.targets[0].name
        with self.assertRaises(BlockingIOError):
            self.controller.delete_all()
        self.assertTrue(all(path.exists() for path in self.targets))

    def test_unexpected_storage_root_blocks_deletion(self):
        with patch.object(server, 'JOBS', self.base / 'models'), self.assertRaises(ValueError):
            self.controller.delete_all()
        self.assertTrue(self.sentinel.exists())

    def test_http_delete_rejects_foreign_origin_and_clears_history(self):
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            url = f'http://127.0.0.1:{http.server_port}/api/jobs'
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(url, method='DELETE', headers={'Origin': 'https://example.org'}), timeout=5)
            self.assertEqual(error.exception.code, 403)
            self.assertTrue(all(path.exists() for path in self.targets))
            with urlopen(Request(url, method='DELETE'), timeout=5) as response:
                self.assertEqual(json.load(response)['deleted_jobs'], 2)
            with urlopen(url, timeout=5) as response:
                self.assertEqual(json.load(response)['jobs'], [])
        finally:
            http.shutdown()
            http.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
