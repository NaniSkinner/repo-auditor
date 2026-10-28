#!/usr/bin/env python3
"""Install personal audit resources or refresh a profile owned by this checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


def profile_text(skill, contract):
    instructions = (
        'You are Watson, the dedicated repository auditor. Accept only repository audits, audit '
        'continuations, and bounded verification setup. Return unrelated work to the caller.\n'
        f'Before work, read {skill}/SKILL.md and its Pstack integration and runbook resources. '
        'Resolve Pstack from the live installed catalog. Do not assume sticky inheritance. '
        'The contract below is embedded from the canonical source. Read its supporting resources '
        'and inspect actual artifacts before verdicts. Target-specific settings are external '
        'run inputs, never permanent role instructions.\n\n' + contract)
    return ('name = "repo-auditor"\n'
            'description = "Watson, the dedicated Audit Agent. Repository audit and verification-path agent. '
            'Use only for explicit repo-audit tasks, not general development or PR lifecycle work."\n'
            'developer_instructions = ' + json.dumps(instructions, ensure_ascii=False) + '\n'
            '\n[features]\nmemories = false\n')


def receipt_for(source, skill, profile, contract, generated):
    version = re.search(r'Contract version ([0-9]+\.[0-9]+\.[0-9]+)\.', contract)
    return {
        'source': str(source), 'skill': str(skill), 'profile': str(profile),
        'contract_version': version.group(1) if version else 'unknown',
        'contract_sha256': hashlib.sha256(contract.encode()).hexdigest(),
        'profile_sha256': hashlib.sha256(generated.encode()).hexdigest(),
        'runtime_profile_discovery': 'requires-supported-new-session-check',
    }


def atomic_write(path, text):
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            os.chmod(temporary, 0o600)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def refresh(source):
    """Regenerate an unchanged receipt-owned profile, preserving other owners' files."""
    source = source.expanduser().resolve()
    receipt_path = source / 'installation.json'
    previous = json.loads(receipt_path.read_text())
    if Path(previous['source']).resolve() != source:
        raise ValueError('Installation source moved')
    skill, profile = Path(previous['skill']), Path(previous['profile'])
    if not skill.is_symlink() or skill.resolve() != source / 'repo-audit':
        raise ValueError('Skill link ownership changed')
    if profile.is_symlink():
        raise ValueError('Refusing to replace a linked profile')
    original = profile.read_text()
    if hashlib.sha256(profile.read_bytes()).hexdigest() != previous['profile_sha256']:
        raise ValueError('Profile changed outside this installation; reconcile it first')
    contract = (source / 'repo-audit/references/contract.md').read_text()
    generated = profile_text(skill, contract)
    receipt = receipt_for(source, skill, profile, contract, generated)
    atomic_write(profile, generated)
    try:
        atomic_write(receipt_path, json.dumps(receipt, indent=2) + '\n')
    except OSError:
        atomic_write(profile, original)
        raise
    return receipt


def copy_package(source, destination):
    source = source.expanduser().resolve()
    manifest = source / 'package-manifest.json'
    if not manifest.is_file():
        raise ValueError('Package manifest is required; build the curated manifest first')
    entries = json.loads(manifest.read_text())['files']
    for item in entries:
        relative = Path(item['path'])
        path = source / relative
        if relative.is_absolute() or '..' in relative.parts or path.is_symlink():
            raise ValueError('Unsafe package path')
        if not path.resolve().is_relative_to(source):
            raise ValueError('Package path escapes source')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Package manifest is stale')
    destination.mkdir()
    for item in entries:
        path = destination / item['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / item['path'], path)
    shutil.copy2(manifest, destination / 'package-manifest.json')


def install(source, destination, skills_root, agents_root):
    source, destination = source.expanduser().resolve(), destination.expanduser().resolve()
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('Source and destination must not contain each other')
    skills_root, agents_root = skills_root.expanduser().resolve(), agents_root.expanduser().resolve()
    skill, profile = skills_root / 'repo-audit', agents_root / 'repo-auditor.toml'
    for path in (destination, skill, profile):
        if path.exists() or path.is_symlink():
            raise ValueError(f'Refusing to replace existing path: {path}')
    contract = (source / 'repo-audit/references/contract.md').read_text()
    generated = profile_text(skill, contract)
    destination.parent.mkdir(parents=True, exist_ok=True)
    skills_root.mkdir(parents=True, exist_ok=True)
    agents_root.mkdir(parents=True, exist_ok=True)
    copied = linked = published = False
    try:
        with tempfile.TemporaryDirectory(prefix='.audit-install-', dir=destination.parent) as temp:
            staged = Path(temp) / 'source'
            copy_package(source, staged)
            staged.rename(destination)
            copied = True
        skill.symlink_to(destination / 'repo-audit', target_is_directory=True)
        linked = True
        with profile.open('x') as stream:
            published = True
            os.chmod(profile, 0o600)
            stream.write(generated)
        receipt = receipt_for(destination, skill, profile, contract, generated)
        atomic_write(destination / 'installation.json', json.dumps(receipt, indent=2) + '\n')
    except (OSError, ValueError, KeyError):
        if published:
            profile.unlink()
        if linked:
            skill.unlink()
        if copied:
            shutil.rmtree(destination)
        raise
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--skills-root', type=Path)
    parser.add_argument('--agents-root', type=Path)
    args = parser.parse_args()
    try:
        if args.refresh:
            if any((args.destination, args.skills_root, args.agents_root)):
                raise ValueError('Refresh uses existing ownership receipt, not new destinations')
            receipt = refresh(args.source)
        else:
            if not all((args.destination, args.skills_root, args.agents_root)):
                raise ValueError('Fresh install needs destination, skills-root and agents-root')
            receipt = install(args.source, args.destination, args.skills_root, args.agents_root)
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
