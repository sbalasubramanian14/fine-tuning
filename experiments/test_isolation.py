"""Exercise the boundaries that protect previous experiments and dataset caches."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from backends import sd1_lora


class IsolationTests(unittest.TestCase):
    def setUp(self):
        temporary_root = sd1_lora.ROOT / '.cache/tmp'
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        self.root = Path(self.temp.name).resolve()
        self.patch = patch.object(sd1_lora, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        (self.root / 'configs').mkdir()
        (self.root / 'configs/character.json').write_text(json.dumps({'trigger': 'testchar'}))
        for split, colors in [('train', ['red', 'green']), ('validation', ['blue'])]:
            folder = self.root / 'data' / split
            folder.mkdir(parents=True)
            for i, color in enumerate(colors):
                Image.new('RGB', (256, 256), color).save(folder / f'{i}.png')
                (folder / f'{i}.txt').write_text('testchar, adult character')
        (self.root / 'data/train/old-latents.npz').write_bytes(b'old model cache')
        self.profile = {
            'model': {'id': 'test/model', 'revision': 'pinned', 'variant': 'fp16', 'directory': 'experiments/image/test/models/base'},
            'artifact_root': 'experiments/image/test/artifacts', 'cache_root': 'experiments/image/test/cache',
            'character_config': 'configs/character.json',
            'dataset': {'train': 'data/train', 'validation': 'data/validation', 'min_train': 2, 'min_validation': 1}}
        self.experiment = sd1_lora.Experiment(self.root / 'profile.json', self.profile, 'run')

    def tearDown(self):
        self.patch.stop()
        self.assertTrue(self.root.is_relative_to(sd1_lora.ROOT / '.cache/tmp'))
        self.temp.cleanup()

    def test_legacy_and_overlapping_storage_rejected(self):
        self.profile['model']['directory'] = 'models/waifu-diffusion'
        with self.assertRaises(ValueError):
            sd1_lora.Experiment(self.root / 'profile.json', self.profile, 'run')
        self.profile['model']['directory'] = self.profile['cache_root']
        with self.assertRaises(ValueError):
            sd1_lora.Experiment(self.root / 'profile.json', self.profile, 'run')

    def test_cache_copies_sources_only_and_rejects_edits(self):
        directory, _, _ = self.experiment.dataset()
        self.assertFalse(list(directory.rglob('*.npz')))
        self.assertEqual((directory / 'train/0.png').read_bytes(), (self.root / 'data/train/0.png').read_bytes())
        (directory / 'train/0.txt').write_text('modified caption')
        with self.assertRaises(RuntimeError):
            self.experiment.dataset()

    def test_model_revision_changes_cache_identity(self):
        original, _, _ = self.experiment.dataset()
        self.profile['model']['revision'] = 'different-vae'
        fresh, _, _ = self.experiment.dataset()
        self.assertNotEqual(original, fresh)

    def test_validation_leakage_rejected(self):
        (self.root / 'data/validation/0.png').write_bytes((self.root / 'data/train/0.png').read_bytes())
        with self.assertRaisesRegex(ValueError, 'leakage'):
            self.experiment.dataset()

    def test_existing_stage_cannot_be_overwritten(self):
        self.experiment.new_stage('train')
        with self.assertRaises(RuntimeError):
            self.experiment.new_stage('train')

    def test_preservation_detects_changed_original(self):
        with patch.object(sd1_lora.subprocess, 'check_output', return_value='git-sha'):
            self.experiment.preserve()
        self.experiment.verify()
        (self.root / 'data/train/0.txt').write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'Preservation failed'):
            self.experiment.verify()

    def make_model_record(self):
        hashes = {}
        for component in ('unet', 'vae', 'text_encoder', 'safety_checker'):
            path = self.experiment.model / component / 'model.safetensors'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(component.encode())
            hashes[f'{component}/model.safetensors'] = sd1_lora.digest(path)
        sd1_lora.write_json(self.experiment.source_path, {
            'model_id': 'test/model', 'revision': 'pinned', 'variant': 'fp16', 'weight_sha256': hashes})

    def test_local_model_corruption_rejected(self):
        self.make_model_record()
        (self.experiment.model / 'vae/model.safetensors').write_bytes(b'corrupt')
        with self.assertRaisesRegex(RuntimeError, 'integrity check'):
            self.experiment.verify_model()

    def test_local_model_wrong_revision_rejected(self):
        self.make_model_record()
        self.profile['model']['revision'] = 'another-model'
        with self.assertRaisesRegex(RuntimeError, 'differs'):
            self.experiment.verify_model()


if __name__ == '__main__':
    unittest.main()
