#!/usr/bin/env python3
"""Deterministic, rights-gated mode of mirror_corpus.py (stdlib + git only)."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_hash(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def raw_cid(data):
    return 'b' + base64.b32encode(b'\x01\x55\x12\x20' + hashlib.sha256(data).digest()).decode().lower().rstrip('=')


def safe_path(path):
    return (isinstance(path, str) and bool(path) and not path.startswith('/')
            and not any(p in ('', '.', '..') for p in path.split('/'))
            and not any(c in path for c in '\\\0\r\n'))


def tree_hash(entries):
    """Reconstruct the exact recursive Git tree from all leaf entries."""
    root = {}
    for item in entries:
        path = item['path']
        if not safe_path(path):
            raise ValueError('Unsafe path: ' + path)
        node = root
        parts = path.split('/')
        for part in parts[:-1]:
            if part not in node:
                node[part] = {}
            if not isinstance(node[part], dict):
                raise ValueError('Tree path conflict')
            node = node[part]
        if parts[-1] in node:
            raise ValueError('Duplicate tree path')
        if item['mode'] not in ('100644', '100755', '120000', '160000'):
            raise ValueError('Unsupported Git mode')
        if not re.fullmatch('[0-9a-f]{40}', item['gitBlobSha']):
            raise ValueError('Invalid Git object ID')
        node[parts[-1]] = (item['mode'], item['gitBlobSha'])

    def encode(node):
        pairs = []
        for name, value in node.items():
            directory = isinstance(value, dict)
            mode, oid = ('40000', encode(value)) if directory else value
            pairs.append(((name + ('/' if directory else '')).encode(),
                          mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(oid)))
        return git_hash('tree', b''.join(v for _, v in sorted(pairs)))
    return encode(root)


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120).stdout


def mime_type(path):
    return {'.md': 'text/markdown', '.txt': 'text/plain', '.lean': 'text/plain',
            '.json': 'application/json', '.html': 'text/html', '.js': 'application/javascript',
            '.py': 'text/x-python', '.toml': 'text/plain', '.yml': 'text/plain',
            '.yaml': 'text/plain', '.css': 'text/css'}.get(Path(path).suffix, 'text/plain')


def build_pack(lock_path, source_root, out, fetch=False):
    lock_bytes = Path(lock_path).read_bytes()
    lock = json.loads(lock_bytes)
    if lock.get('format') != 'monolithic-source-lock-v1':
        raise ValueError('Unsupported lock')
    catalog_bytes = (ROOT / 'corpus-index.json').read_bytes()
    catalog = json.loads(catalog_bytes)
    known = {r['id']: r for r in catalog['repositories']}
    files, archives, coverage = [], [], []
    used, seen_repos = 0, set()
    for spec in sorted(lock['repositories'], key=lambda r: r['repo']):
        rid, commit = spec['repo'], spec['commit']
        if rid not in known or rid in seen_repos or not re.fullmatch('[0-9a-f]{40}', commit):
            raise ValueError('Unknown/duplicate repository or unpinned commit')
        seen_repos.add(rid)
        if tree_hash(spec['tree']) != spec['gitTreeSha']:
            raise ValueError('Incomplete or changed Git tree: ' + rid)
        selected = set(spec['includedPaths'])
        by_path = {e['path']: e for e in spec['tree']}
        if len(selected) != len(spec['includedPaths']) or not selected <= by_path.keys():
            raise ValueError('Duplicate or unknown selected paths')
        status = 'metadata-only'
        captured, captured_bytes = 0, 0
        if selected:
            license = spec['license']
            if license.get('spdx') not in ('MIT', 'CC0-1.0') or license.get('path') not in selected:
                raise ValueError('Explicit supported license and included notice required')
            if license['gitBlobSha'] != by_path[license['path']]['gitBlobSha']:
                raise ValueError('License object mismatch')
            local = Path(source_root) / known[rid]['name']
            if fetch:
                local.mkdir(parents=True, exist_ok=True)
                if not (local / '.git').exists():
                    git(local, 'init', '--quiet')
                # Fetch the exact locked object, never the moving default branch.
                git(local, '-c', 'credential.interactive=never', 'fetch', '--quiet', '--depth=1',
                    'https://github.com/' + rid + '.git', commit)
            raw_commit = git(local, 'cat-file', 'commit', commit)
            if git_hash('commit', raw_commit) != commit or raw_commit.splitlines()[0] != b'tree ' + spec['gitTreeSha'].encode():
                raise ValueError('Commit/tree binding mismatch')
            # Read Git blobs, not the working tree: no filters, symlink traversal or accidental dirty files.
            license_bytes = git(local, 'cat-file', 'blob', license['gitBlobSha'])
            license = {**license, 'sha256': sha256(license_bytes)}
            entries = []
            for entry in sorted(spec['tree'], key=lambda e: e['path'].encode()):
                entry = dict(entry)
                path = entry['path']
                if path not in selected:
                    entry.update(disposition='omitted', reason=spec['omissionReason'])
                    entries.append(entry)
                    continue
                if entry['mode'] not in ('100644', '100755') or entry['type'] != 'blob':
                    raise ValueError('Cannot include symlink/submodule')
                data = git(local, 'cat-file', 'blob', entry['gitBlobSha'])
                if git_hash('blob', data) != entry['gitBlobSha'] or len(data) != entry['size']:
                    raise ValueError('Blob mismatch: ' + path)
                if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError('LFS pointer needs explicit exclusion: ' + path)
                used += len(data)
                if len(data) > lock['limits']['maxFileBytes'] or used > lock['limits']['maxTotalBytes']:
                    raise ValueError('Pack size cap exceeded (no silent truncation)')
                entry.update(disposition='included', sha256=sha256(data), cid=raw_cid(data))
                entries.append(entry)
                provenance = {'repository': rid, 'commit': commit, 'gitBlobSha': entry['gitBlobSha'],
                              'gitMode': entry['mode'], 'license': license,
                              'sourceUrl': 'https://github.com/' + rid + '/blob/' + commit + '/' + quote(path, safe='/')}
                files.append({'repo': rid, 'path': path, 'mime': mime_type(path), 'size': len(data),
                              'source': provenance['sourceUrl'], 'provenance': provenance,
                              'sha256': entry['sha256'], 'cid': entry['cid'],
                              'base64': base64.b64encode(data).decode()})
                captured += 1
                captured_bytes += len(data)
            status = 'fully-mirrored' if captured == len(spec['tree']) else 'partially-cached'
            archives.append({'repo': rid, 'commit': commit, 'gitTreeSha': spec['gitTreeSha'],
                             'sourcePack': {'id': lock['id'], 'lockSha256': sha256(lock_bytes)},
                             'commitObject': base64.b64encode(raw_commit).decode(), 'license': license,
                             'entries': entries, 'status': status})
        coverage.append({'repo': rid, 'commit': commit, 'gitTreeSha': spec['gitTreeSha'], 'status': status,
                         'treeFiles': len(spec['tree']), 'capturedFiles': captured,
                         'capturedBytes': captured_bytes, 'license': spec['license'],
                         'omitted': [{'path': e['path'], 'reason': spec['omissionReason']}
                                     for e in spec['tree'] if e['path'] not in selected]})
    # Use stable catalog identity fields; build.py may add release coverage later.
    repos = [{k: v for k, v in known[rid].items() if k not in ('archive', 'status')}
             for rid in sorted(seen_repos)]
    bundle = {'format': 'monolithic-atlas-bundle-v1', 'snapshotDate': lock['snapshotDate'],
              'createdAt': lock['snapshotDate'] + 'T00:00:00Z', 'scope': lock['scope'],
              'rightsNotice': lock['rightsNotice'], 'sourcePack': {'id': lock['id'], 'lockSha256': sha256(lock_bytes)},
              'repositories': repos, 'archives': archives, 'files': files}
    bundle_bytes = canonical(bundle)
    report = {'format': 'monolithic-source-report-v1', 'id': lock['id'], 'snapshotDate': lock['snapshotDate'],
              'scope': lock['scope'], 'rightsNotice': lock['rightsNotice'],
              'lockSha256': sha256(lock_bytes), 'bundleFile': lock['id'] + '.bundle.json',
              'bundleSha256': sha256(bundle_bytes), 'capturedFiles': len(files), 'capturedBytes': used,
              'repositories': coverage}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / report['bundleFile']).write_bytes(bundle_bytes)
    (out / (lock['id'] + '.report.json')).write_bytes(canonical(report))
    print(f"{lock['id']}: {len(files)} files, {used} source bytes, {len(archives)} repositories with content")
    return bundle, report
