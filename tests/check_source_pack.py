#!/usr/bin/env python3
"""Offline reconstruction, integrity and negative controls; no network needed."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from source_pack import build_pack, canonical, git_hash, raw_cid, tree_hash

LOCK = ROOT / 'source-packs/central-efmw-v1.lock.json'
BUNDLE = ROOT / 'source-packs/central-efmw-v1.bundle.json'
REPORT = ROOT / 'source-packs/central-efmw-v1.report.json'


class SourcePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads(BUNDLE.read_bytes())
        cls.lock = json.loads(LOCK.read_bytes())
        cls.tmp = tempfile.TemporaryDirectory()
        cls.sources = Path(cls.tmp.name) / 'sources'
        cls.sources.mkdir()
        # Reconstruct only permitted objects from the shipped pack. Omitted source
        # blobs are intentionally unavailable; rebuilding must not request them.
        for archive in cls.bundle['archives']:
            repo = cls.sources / archive['repo'].split('/')[1]
            subprocess.run(['git', 'init', '--quiet', str(repo)], check=True)
            def write(kind, raw):
                return subprocess.run(['git', '-C', str(repo), 'hash-object', '-w', '-t', kind, '--stdin'],
                                      input=raw, check=True, stdout=subprocess.PIPE).stdout.decode().strip()
            assert write('commit', base64.b64decode(archive['commitObject'])) == archive['commit']
            for f in cls.bundle['files']:
                if f['repo'] == archive['repo']:
                    assert write('blob', base64.b64decode(f['base64'])) == f['provenance']['gitBlobSha']

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_hashes_and_rights(self):
        report = json.loads(REPORT.read_bytes())
        self.assertEqual(hashlib.sha256(BUNDLE.read_bytes()).hexdigest(), report['bundleSha256'])
        self.assertEqual(hashlib.sha256(LOCK.read_bytes()).hexdigest(), report['lockSha256'])
        self.assertEqual(len(self.bundle['files']), 99)
        self.assertEqual(sum(f['size'] for f in self.bundle['files']), 352723)
        self.assertEqual(len({(f['repo'], f['path']) for f in self.bundle['files']}), 99)
        for spec in self.lock['repositories']:
            self.assertEqual(tree_hash(spec['tree']), spec['gitTreeSha'])
        for f in self.bundle['files']:
            data = base64.b64decode(f['base64'], validate=True)
            self.assertEqual(len(data), f['size'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), f['sha256'])
            self.assertEqual(git_hash('blob', data), f['provenance']['gitBlobSha'])
            self.assertEqual(raw_cid(data), f['cid'])
            self.assertIn(f['provenance']['license']['spdx'], ('MIT', 'CC0-1.0'))
            self.assertNotIn(f['path'], ('UPSTREAM_SOURCES.json', 'extension-sources.json'))
        counts = {s: sum(r['status'] == s for r in report['repositories']) for s in
                  ('fully-mirrored', 'partially-cached', 'metadata-only')}
        self.assertEqual(counts, {'fully-mirrored': 2, 'partially-cached': 1, 'metadata-only': 11})

    def test_rebuild_offline_byte_identical(self):
        for number in range(2):
            out = Path(self.tmp.name) / ('rebuild' + str(number))
            build_pack(LOCK, self.sources, out)
            self.assertEqual((out / BUNDLE.name).read_bytes(), BUNDLE.read_bytes())
            self.assertEqual((out / REPORT.name).read_bytes(), REPORT.read_bytes())

    def reject(self, change, pattern):
        lock = copy.deepcopy(self.lock)
        change(lock)
        path = Path(self.tmp.name) / 'bad-lock.json'
        path.write_bytes(canonical(lock))
        with self.assertRaisesRegex(ValueError, pattern):
            build_pack(path, self.sources, Path(self.tmp.name) / 'bad-output')

    def test_license_required(self):
        self.reject(lambda l: l['repositories'][0]['license'].update(spdx=None), 'license')

    def test_missing_license_notice(self):
        self.reject(lambda l: l['repositories'][0]['includedPaths'].remove('LICENSE'), 'license')

    def test_tree_tampering(self):
        self.reject(lambda l: l['repositories'][0]['tree'].pop(), 'Git tree')

    def test_exact_commit_required(self):
        self.reject(lambda l: l['repositories'][0].update(commit='main'), 'unpinned')

    def test_cap_is_error_not_silent_truncation(self):
        self.reject(lambda l: l['limits'].update(maxTotalBytes=1), 'cap')


if __name__ == '__main__':
    unittest.main()
