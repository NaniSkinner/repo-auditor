import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts_install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_installs_exact_contract_and_explicit_skill(self):
        destination = self.root / 'source'
        receipt = installer.install(ROOT, destination, self.root / 'skills', self.root / 'agents')
        self.assertEqual((self.root / 'skills/repo-audit').resolve(), (destination / 'repo-audit').resolve())
        profile = Path(receipt['profile']).read_text()
        contract = (destination / 'repo-audit/references/contract.md').read_text()
        line = next(item for item in profile.splitlines() if item.startswith('developer_instructions'))
        self.assertIn(contract, json.loads(line.split('=', 1)[1]))
        self.assertIn('allow_implicit_invocation: false',
                      (destination / 'repo-audit/agents/openai.yaml').read_text())

    def test_manifest_copies_only_declared_files_and_rejects_stale_source(self):
        import hashlib
        source = self.root / 'curated'
        source.mkdir()
        (source / 'safe.txt').write_text('generic instructions')
        (source / 'local-target.txt').write_text('private target settings')
        manifest = {'files': [{'path': 'safe.txt', 'sha256': hashlib.sha256(
            (source / 'safe.txt').read_bytes()).hexdigest()}]}
        (source / 'package-manifest.json').write_text(json.dumps(manifest))
        destination = self.root / 'copy'
        installer.copy_package(source, destination)
        self.assertTrue((destination / 'safe.txt').exists())
        self.assertFalse((destination / 'local-target.txt').exists())
        (source / 'safe.txt').write_text('changed bytes')
        with self.assertRaisesRegex(ValueError, 'stale'):
            installer.copy_package(source, self.root / 'stale-copy')
        self.assertFalse((self.root / 'stale-copy').exists())

    def test_missing_manifest_refuses_to_copy(self):
        source = self.root / 'unmanifested'
        source.mkdir()
        (source / 'local-target.txt').write_text('private target settings')
        with self.assertRaisesRegex(ValueError, 'manifest is required'):
            installer.copy_package(source, self.root / 'unsafe-copy')
        self.assertFalse((self.root / 'unsafe-copy').exists())

    def test_relative_roots_remain_valid_from_another_working_directory(self):
        import os
        original = Path.cwd()
        try:
            os.chdir(self.root)
            destination = self.root / 'source'
            receipt = installer.install(ROOT, destination, Path('skills'), Path('agents'))
            self.assertTrue(Path(receipt['skill']).is_absolute())
            self.assertTrue(Path(receipt['profile']).is_absolute())
            os.chdir(self.root.parent)
            installer.refresh(destination)
            result = subprocess.run([sys.executable, str(destination / 'repo-audit/scripts/audit.py'),
                                     'self-check'], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            os.chdir(original)

    def test_existing_profile_is_not_modified(self):
        agents = self.root / 'agents'
        agents.mkdir()
        profile = agents / 'repo-auditor.toml'
        profile.write_text('owned by another installation')
        with self.assertRaises(ValueError):
            installer.install(ROOT, self.root / 'source', self.root / 'skills', agents)
        self.assertEqual(profile.read_text(), 'owned by another installation')
        self.assertFalse((self.root / 'source').exists())

    def test_refresh_embeds_updated_contract_and_self_check_passes(self):
        destination = self.root / 'source'
        receipt = installer.install(ROOT, destination, self.root / 'skills', self.root / 'agents')
        contract = destination / 'repo-audit/references/contract.md'
        contract.write_text(contract.read_text() + '\nNew explicit audit obligation.\n')
        updated = installer.refresh(destination)
        self.assertNotEqual(updated['contract_sha256'], receipt['contract_sha256'])
        self.assertIn('New explicit audit obligation.', Path(updated['profile']).read_text())
        result = subprocess.run([sys.executable, str(destination / 'repo-audit/scripts/audit.py'),
                                 'self-check'], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_refresh_refuses_profile_modified_outside_installation(self):
        destination = self.root / 'source'
        receipt = installer.install(ROOT, destination, self.root / 'skills', self.root / 'agents')
        profile = Path(receipt['profile'])
        profile.write_text('another owner edited this')
        with self.assertRaisesRegex(ValueError, 'outside this installation'):
            installer.refresh(destination)
        self.assertEqual(profile.read_text(), 'another owner edited this')

    def test_refresh_receipt_failure_restores_old_profile(self):
        destination = self.root / 'source'
        receipt = installer.install(ROOT, destination, self.root / 'skills', self.root / 'agents')
        profile = Path(receipt['profile'])
        original = profile.read_text()
        contract = destination / 'repo-audit/references/contract.md'
        contract.write_text(contract.read_text() + '\nUpdated requirement\n')
        actual = installer.atomic_write
        def fail_receipt(path, text):
            if path.name == 'installation.json':
                raise OSError('simulated publication failure')
            return actual(path, text)
        with patch.object(installer, 'atomic_write', side_effect=fail_receipt):
            with self.assertRaises(OSError):
                installer.refresh(destination)
        self.assertEqual(profile.read_text(), original)

    def test_failed_profile_publication_leaves_install_retryable(self):
        destination = self.root / 'source'
        with patch.object(installer, 'atomic_write', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                installer.install(ROOT, destination, self.root / 'skills', self.root / 'agents')
        self.assertFalse(destination.exists())
        self.assertFalse((self.root / 'skills/repo-audit').is_symlink())
        self.assertFalse((self.root / 'agents/repo-auditor.toml').exists())
        installer.install(ROOT, destination, self.root / 'skills', self.root / 'agents')

    def test_nested_destination_is_rejected_before_copy(self):
        with patch.object(installer.shutil, 'copytree', side_effect=RuntimeError('unsafe copy reached')):
            with self.assertRaises(ValueError):
                installer.install(ROOT, ROOT / 'nested', self.root / 'skills', self.root / 'agents')
        self.assertFalse((ROOT / 'nested').exists())

    def test_self_check_rejects_contract_profile_drift(self):
        destination = self.root / 'source'
        installer.install(ROOT, destination, self.root / 'skills', self.root / 'agents')
        command = [sys.executable, str(destination / 'repo-audit/scripts/audit.py'), 'self-check']
        valid = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        with (destination / 'repo-audit/references/contract.md').open('a') as stream:
            stream.write('\nChanged obligations\n')
        stale = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(stale.returncode, 1)
        self.assertIn('contract', stale.stderr.lower())


if __name__ == '__main__':
    unittest.main()
