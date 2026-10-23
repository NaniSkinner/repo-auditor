#!/usr/bin/env python3
"""Regenerate the explicit generic package allowlist after reviewing source edits."""
import hashlib
import json
from pathlib import Path

FILES = (
    '.gitignore', 'README.md', 'scripts_install.py', 'scripts_manifest.py',
    'docs/implementation-plan.md', 'docs/maintaining.md', 'docs/verification-1.2.md',
    'templates/target-profile.md', 'templates/run-ledger.json',
    'tests/test_install.py', 'tests/test_audit.py', 'repo-audit/SKILL.md',
    'repo-audit/agents/openai.yaml', 'repo-audit/scripts/audit.py',
    'repo-audit/references/contract.md', 'repo-audit/references/delegation.md',
    'repo-audit/references/evidence.md', 'repo-audit/references/project-verification.md',
    'repo-audit/references/pstack.md', 'repo-audit/references/runbook.md',
    'repo-audit/references/target-preparation.md',
)


def main():
    root = Path(__file__).resolve().parent
    entries = []
    for name in FILES:
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError(f'Expected a regular package file: {name}')
        entries.append({'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (root / 'package-manifest.json').write_text(json.dumps({'files': entries}, indent=2) + '\n')
    print(f'Manifest contains {len(entries)} explicit generic source files')


if __name__ == '__main__':
    main()
