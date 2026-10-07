"""Request boundary tests; no weights loaded and no GPU required."""
import unittest
from unittest.mock import patch

import catalog


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.model = {
            'id': 'test', 'label': 'Test image', 'available': True,
            'backend': 'image_sd1', 'profile': 'test/profile.json',
            'adapters': [{'id': 'own-adapter'}],
            'fields': [
                {'id': 'steps', 'label': 'Steps', 'type': 'number', 'default': 28, 'min': 1, 'max': 60, 'step': 1},
                {'id': 'strength', 'label': 'Strength', 'type': 'number', 'default': .8, 'min': 0, 'max': 2, 'step': .1},
                {'id': 'size', 'label': 'Size', 'type': 'select', 'default': '512x512', 'options': ['512x512']},
                {'id': 'negative', 'label': 'Negative', 'type': 'textarea', 'default': ''},
            ]}
        self.registry = patch.object(catalog, 'models', return_value=[self.model])
        self.registry.start()
        self.addCleanup(self.registry.stop)

    def request(self, **changes):
        return catalog.resolve_request({'model': 'test', 'prompt': '  example  ', **changes})

    def test_base_defaults_and_prompt_normalization(self):
        result = self.request()
        self.assertIsNone(result['adapter'])
        self.assertEqual(result['prompt'], 'example')
        self.assertEqual(result['settings']['steps'], 28)

    def test_compare_requires_compatible_adapter(self):
        for adapter in (None, 'other-model-adapter'):
            with self.subTest(adapter=adapter), self.assertRaises(ValueError):
                self.request(mode='compare', adapter=adapter)
        self.assertEqual(self.request(mode='compare', adapter='own-adapter')['adapter'], 'own-adapter')

    def test_numeric_boundaries(self):
        for key, value in [('steps', 0), ('steps', 61), ('steps', 2.5), ('steps', True),
                           ('strength', float('nan')), ('strength', float('inf')), ('strength', -1)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.request(settings={key: value})

    def test_input_and_model_boundaries(self):
        for changes in ({'prompt': ''}, {'prompt': 'a' * 4001}, {'settings': []},
                        {'settings': {'size': '2048x2048'}}, {'settings': {'negative': 'a' * 2001}},
                        {'mode': 'unsupported'}, {'model': 'unknown'}):
            with self.subTest(changes=list(changes)), self.assertRaises(ValueError):
                self.request(**changes)
        self.model['available'] = False
        with self.assertRaises(ValueError):
            self.request()

    def test_profile_path_cannot_escape_repository(self):
        with self.assertRaises(ValueError):
            catalog.local('../outside')


if __name__ == '__main__':
    unittest.main()
