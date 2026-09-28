#!/usr/bin/env python3
"""Export only a validated Unity Web player to a GitHub Pages deployment checkout."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

# Keep Git blobs below GitHub's 100 MiB limit; Pages reconstructs larger player files.
PART_BYTES = 48 * 1024 * 1024
ALLOWED_ROOTS = {'Build', 'StreamingAssets', 'TemplateData'}
ALLOWED_FILES = {'index.html', '.nojekyll', 'ThirdPartyNotices.txt'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def package(source, destination, revision, part_bytes=PART_BYTES):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError('Build and deployment directories must be separate.')
    if not (source / 'index.html').is_file() or not (source / 'Build').is_dir():
        raise ValueError('Expected a completed Unity Web build.')
    html = (source / 'index.html').read_text()
    if '{{{' in html or 'autoSyncPersistentDataPath:true' not in html:
        raise ValueError('Expected the processed HELLSCRIPT template with persistent saves.')
    files = sorted(p for p in source.rglob('*') if p.is_file())
    for path in files:
        relative = path.relative_to(source)
        if path.is_symlink() or (relative.parts[0] not in ALLOWED_ROOTS and relative.as_posix() not in ALLOWED_FILES):
            raise ValueError('Unexpected build artifact: ' + str(relative))
    # Only this tool's dedicated generated export is replaced; repository management files stay intact.
    export = destination / 'player'
    if export.exists():
        marker = export / 'manifest.json'
        if not marker.is_file() or json.loads(marker.read_text()).get('format') != 'hellscript-web-v1':
            raise ValueError('Refusing to replace an unrecognized player directory.')
        shutil.rmtree(export)
    export.mkdir(parents=True)
    manifest = {'format': 'hellscript-web-v1', 'sourceRevision': revision, 'files': []}
    for path in files:
        relative = path.relative_to(source).as_posix()
        data = path.read_bytes()
        record = {'path': relative, 'bytes': len(data), 'sha256': digest(data), 'parts': []}
        for i, offset in enumerate(range(0, max(1, len(data)), part_bytes)):
            part = data[offset:offset + part_bytes]
            name = f'objects/{record["sha256"]}.{i:03d}'
            output = export / name
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(part)
            record['parts'].append({'path': name, 'sha256': digest(part)})
        manifest['files'].append(record)
    (export / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def assemble(export, output):
    export, output = Path(export).resolve(), Path(output).resolve()
    manifest = json.loads((export / 'manifest.json').read_text())
    if manifest.get('format') != 'hellscript-web-v1':
        raise ValueError('Unknown player export format.')
    if output.exists():
        raise ValueError('Assembly output must be a new directory.')
    records = []
    for record in manifest['files']:
        target = (output / record['path']).resolve()
        if output not in target.parents:
            raise ValueError('Invalid output path.')
        chunks = []
        for part in record['parts']:
            path = (export / part['path']).resolve()
            if export not in path.parents:
                raise ValueError('Invalid part path.')
            data = path.read_bytes()
            if digest(data) != part['sha256']:
                raise ValueError('Corrupt build part: ' + part['path'])
            chunks.append(data)
        data = b''.join(chunks)
        if len(data) != record['bytes'] or digest(data) != record['sha256']:
            raise ValueError('Corrupt build file: ' + record['path'])
        records.append((target, data))
    for target, data in records:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (output / 'build-info.json').write_text(json.dumps({
        'sourceRevision': manifest['sourceRevision'],
        'bytes': sum(r['bytes'] for r in manifest['files']),
        'files': [{k: r[k] for k in ('path', 'bytes', 'sha256')} for r in manifest['files']]
    }, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    pack = commands.add_parser('package')
    pack.add_argument('build', type=Path)
    pack.add_argument('destination', type=Path)
    pack.add_argument('--revision', required=True)
    unpack = commands.add_parser('assemble')
    unpack.add_argument('export', type=Path)
    unpack.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'package':
        result = package(args.build, args.destination, args.revision)
        print(f'Packaged {len(result["files"])} files, {sum(r["bytes"] for r in result["files"])} bytes')
    else:
        assemble(args.export, args.output)
        print('Verified and assembled the complete Web player.')
