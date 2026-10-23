import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / 'repo-audit/scripts/audit.py'


class AuditGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'project'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        (self.repo / 'app.txt').write_text('healthy\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.run_dir = self.root / 'run'

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              capture_output=True, text=True, timeout=10).stdout

    def cli(self, *args, expected=0, env=None):
        result = subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                                capture_output=True, text=True, timeout=15, env=env)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def initialize(self, scope='verification'):
        self.cli('init', '--repo', self.repo, '--out', self.run_dir, '--scope', scope)
        path = self.run_dir / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['environment'] = {'label': 'isolated-local', 'build': 'fixture-commit',
                                   'actor': 'synthetic', 'configuration': 'no-services',
                                   'fixtures': 'disposable'}
        path.write_text(json.dumps(manifest))

    def capture(self, identifier, code, kind='outcome', parser='none', timeout='3'):
        self.cli('capture', '--run', self.run_dir, '--id', identifier,
                 '--kind', kind, '--parser', parser, '--timeout', timeout,
                 '--', sys.executable, '-c', code)

    def complete_report(self):
        self.initialize()
        self.capture('good', 'print("persisted and read back")')
        self.capture('broken', 'raise SystemExit("record missing after write")')
        self.capture('restored-good', 'print("restored record persisted and read back")')
        report = json.loads((self.run_dir / 'report.json').read_text())
        (self.run_dir / 'assessment.md').write_text('Synthetic assessment and bounded scope.\n')
        for key in report['sections']:
            report['sections'][key] = 'assessment.md'
        report['workflows'] = [{'id': 'save', 'selected': True,
                                'critical': True, 'reason': 'Persistent user outcome'}]
        report['claims'] = [{
            'id': 'persist', 'workflow': 'save', 'claim': 'Submitted data survives readback',
            'scope': 'Synthetic local CLI', 'prerequisites': ['clean fixture'],
            'source_of_truth': 'independent readback', 'procedure': 'write then fresh read',
            'expected': 'same stored value', 'observed': 'same stored value',
            'status': 'PASS', 'reason': 'Readback matched the literal expected value',
            'evidence': ['good'], 'false_pass_risks': ['cached response'],
            'invalidation': ['code or fixture change'],
            'cleanup': {'status': 'complete', 'detail': 'Disposable fixture removed'},
            'next_check': 'Repeat after a relevant change'}]
        report['calibrations'] = [{
            'workflow': 'save', 'good': 'good', 'broken': 'broken',
            'restored_good': 'restored-good',
            'fault': 'Write omitted', 'expected_failure': 'Record absent on readback',
            'observed_failure': 'Record missing after write',
            'restored': True}]
        report['review'] = {'status': 'pending', 'reviewer': '', 'evidence': []}
        self.write_report(report)
        return report

    def write_report(self, report):
        (self.run_dir / 'report.json').write_text(json.dumps(report))

    def validate(self, *args, expected=0):
        return self.cli('validate', '--run', self.run_dir, *args, expected=expected)

    def test_known_good_receipt_is_accepted_without_claiming_review(self):
        self.complete_report()
        result = self.validate()
        self.assertIn('RECEIPT_VALID', result.stdout)
        self.assertIn('pending', result.stdout)

    def test_required_review_cannot_be_skipped(self):
        self.complete_report()
        self.validate('--require-review', expected=1)

    def test_honest_blocker_is_a_valid_assessment_not_a_runtime_pass(self):
        report = self.complete_report()
        report['claims'][0].update(status='BLOCKED', evidence=[], observed='No access',
                                   reason='Test account unavailable')
        report['calibrations'] = []
        self.write_report(report)
        self.validate()
        self.validate('--require-runtime', expected=1)

    def test_incomplete_template_is_rejected(self):
        self.initialize()
        self.validate(expected=1)

    def test_missing_evidence_is_rejected(self):
        report = self.complete_report()
        report['claims'][0]['evidence'] = ['nonexistent']
        self.write_report(report)
        self.validate(expected=1)

    def test_tampered_output_is_rejected(self):
        self.complete_report()
        (self.run_dir / 'evidence/good/output.txt').write_text('invented success')
        self.validate(expected=1)

    def test_source_changed_since_capture_invalidates_result(self):
        self.complete_report()
        (self.repo / 'app.txt').write_text('changed\n')
        self.validate(expected=1)

    def test_new_commit_invalidates_result(self):
        self.complete_report()
        self.git('commit', '--allow-empty', '-qm', 'new head')
        self.validate(expected=1)

    def test_positive_claim_cannot_use_failed_command(self):
        report = self.complete_report()
        report['claims'][0]['evidence'] = ['broken']
        self.write_report(report)
        self.validate(expected=1)

    def test_negative_control_is_required_for_pass(self):
        report = self.complete_report()
        report['calibrations'] = []
        self.write_report(report)
        self.validate(expected=1)

    def test_successful_negative_control_does_not_calibrate(self):
        report = self.complete_report()
        report['calibrations'][0]['broken'] = 'good'
        self.write_report(report)
        self.validate(expected=1)

    def test_zero_test_exit_success_is_not_a_pass(self):
        report = self.complete_report()
        self.capture('empty', 'print("no tests ran in 0.01s")', kind='test', parser='pytest')
        report['claims'][0]['evidence'] = ['empty']
        self.write_report(report)
        self.validate(expected=1)

    def test_skipped_only_tests_are_not_executed_checks(self):
        report = self.complete_report()
        self.capture('skips', 'print("3 skipped in 0.01s")', kind='test', parser='pytest')
        report['claims'][0]['evidence'] = ['skips']
        self.write_report(report)
        self.validate(expected=1)

    def test_real_test_output_records_executed_count(self):
        self.initialize()
        self.capture('tests', 'import unittest; unittest.main()', kind='test', parser='unittest')
        receipt = json.loads((self.run_dir / 'evidence/tests/receipt.json').read_text())
        self.assertEqual(receipt['executed_tests'], 0)

    def test_claim_cannot_escape_run_directory(self):
        report = self.complete_report()
        report['sections']['baseline'] = '../private.txt'
        (self.root / 'private.txt').write_text('outside')
        self.write_report(report)
        self.validate(expected=1)

    def test_symlink_evidence_escape_is_rejected(self):
        report = self.complete_report()
        outside = self.root / 'elsewhere.txt'
        outside.write_text('outside')
        (self.run_dir / 'escape.md').symlink_to(outside)
        report['sections']['baseline'] = 'escape.md'
        self.write_report(report)
        self.validate(expected=1)

    def test_duplicate_claim_ids_are_rejected(self):
        report = self.complete_report()
        report['claims'].append(copy.deepcopy(report['claims'][0]))
        self.write_report(report)
        self.validate(expected=1)

    def test_uncovered_selected_workflow_is_rejected(self):
        report = self.complete_report()
        report['workflows'].append({'id': 'export', 'selected': True,
                                    'critical': True, 'reason': 'Requested'})
        self.write_report(report)
        self.validate(expected=1)

    def test_inspection_cannot_claim_runtime_pass(self):
        report = self.complete_report()
        manifest = json.loads((self.run_dir / 'manifest.json').read_text())
        manifest['scope'] = 'inspection'
        (self.run_dir / 'manifest.json').write_text(json.dumps(manifest))
        self.validate(expected=1)

    def test_capture_does_not_inherit_provider_credentials(self):
        self.initialize()
        env = dict(os.environ, AUDITOR_SECRET='should-not-reach-child')
        self.cli('capture', '--run', self.run_dir, '--id', 'environment',
                 '--kind', 'command', '--timeout', '3', '--', sys.executable,
                 '-c', 'import os; assert "AUDITOR_SECRET" not in os.environ', env=env)
        receipt = json.loads((self.run_dir / 'evidence/environment/receipt.json').read_text())
        self.assertEqual(receipt['exit_code'], 0)

    def test_capture_is_append_only_and_timeout_is_preserved(self):
        self.initialize()
        self.capture('slow', 'import time; time.sleep(2)', timeout='0.1')
        receipt = json.loads((self.run_dir / 'evidence/slow/receipt.json').read_text())
        self.assertTrue(receipt['timed_out'])
        self.cli('capture', '--run', self.run_dir, '--id', 'slow', '--kind', 'command',
                 '--timeout', '3', '--', sys.executable, '-c', 'print(1)', expected=1)

    def test_non_audit_artifact_cannot_claim_ship(self):
        report = self.complete_report()
        report['recommendation'] = 'ship'
        self.write_report(report)
        self.validate(expected=1)

    def test_malformed_json_has_a_bounded_failure(self):
        self.initialize()
        (self.run_dir / 'report.json').write_text('{')
        result = self.validate(expected=1)
        self.assertNotIn('Traceback', result.stderr)

    def test_doctor_names_missing_dependencies(self):
        result = self.cli('doctor', '--pstack-root', self.root / 'missing', expected=1)
        self.assertIn('missing', result.stdout.lower())

    def test_runtime_gate_rejects_ready_only_dependency_receipt(self):
        report = self.complete_report()
        manifest_path = self.run_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['dependency_receipt'] = 'dependencies.json'
        manifest_path.write_text(json.dumps(manifest))
        (self.run_dir / 'dependencies.json').write_text('{"ready": true}')
        for path in self.run_dir.glob('evidence/*/receipt.json'):
            receipt = json.loads(path.read_text())
            receipt['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            path.write_text(json.dumps(receipt))
        result = self.validate('--require-runtime', expected=1)
        self.assertIn('dependency', result.stderr.lower())

    def test_silent_assertion_can_supply_outcome_evidence(self):
        report = self.complete_report()
        self.capture('silent', 'assert 2 + 2 == 4')
        report['claims'][0]['evidence'] = ['silent']
        self.write_report(report)
        self.validate()

    def test_complete_runtime_gate_accepts_current_dependencies(self):
        report = self.complete_report()
        pstack = self.root / 'pstack'
        roles = ('poteto-mode/SKILL.md', 'poteto-mode/references/codex-agent-runtime.md',
                 'poteto-mode/references/poteto-agent-prompt.md',
                 'poteto-mode/playbooks/investigation.md', 'poteto-mode/playbooks/eval.md',
                 'how/SKILL.md', 'why/SKILL.md', 'swarm/SKILL.md', 'interrogate/SKILL.md',
                 'principle-prove-it-works/SKILL.md', 'create-verification-skill/SKILL.md',
                 'maintain-verification-skill/SKILL.md')
        for role in roles:
            path = pstack / 'skills' / role
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic dependency for structural gate coverage.\n')
        evidence_first = self.root / 'evidence-first.md'
        evidence_first.write_text('Synthetic evidence dependency.\n')
        self.cli('doctor', '--pstack-root', pstack, '--evidence-first', evidence_first,
                 '--out', self.run_dir / 'dependencies.json')
        manifest_path = self.run_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['dependency_receipt'] = 'dependencies.json'
        manifest_path.write_text(json.dumps(manifest))
        self.capture('fresh-good', 'print("asserted outcome")')
        self.capture('fresh-bad', 'raise SystemExit("expected missing record")')
        self.capture('fresh-restored', 'assert True')
        report['claims'][0]['evidence'] = ['fresh-good']
        report['calibrations'][0].update(good='fresh-good', broken='fresh-bad',
                                          restored_good='fresh-restored')
        (self.run_dir / 'review.md').write_text('Synthetic reviewer receipt for structural coverage.\n')
        report['review'] = {'status': 'complete', 'reviewer': 'synthetic-review-fixture',
                            'evidence': ['review.md']}
        self.write_report(report)
        self.validate('--require-review', '--require-runtime')

    def test_changed_external_oracle_invalidates_evidence(self):
        report = self.complete_report()
        scenario = self.run_dir / 'scenario.py'
        scenario.write_text('assert 2 + 2 == 4\n')
        self.cli('capture', '--run', self.run_dir, '--id', 'oracle', '--kind', 'outcome',
                 '--input', scenario, '--timeout', '3', '--', sys.executable, str(scenario))
        report['claims'][0]['evidence'] = ['oracle']
        self.write_report(report)
        self.validate()
        scenario.write_text('pass\n')
        result = self.validate(expected=1)
        self.assertIn('input', result.stderr.lower())

    def test_direct_script_requires_input_fingerprint(self):
        self.initialize()
        script = self.run_dir / 'scenario.sh'
        script.write_text('#!/bin/sh\nexit 0\n')
        script.chmod(0o700)
        result = self.cli('capture', '--run', self.run_dir, '--id', 'direct',
                          '--kind', 'outcome', '--timeout', '3', '--', script, expected=1)
        self.assertIn('input', result.stderr.lower())

    def test_retargeted_declared_config_invalidates_evidence(self):
        report = self.complete_report()
        first, second, link = (self.run_dir / name for name in ('first.json', 'second.json', 'config.json'))
        first.write_text('{"mode":"first"}')
        second.write_text('{"mode":"second"}')
        link.symlink_to(first)
        self.cli('capture', '--run', self.run_dir, '--id', 'config', '--kind', 'outcome',
                 '--input', link, '--timeout', '3', '--', sys.executable, '-c', 'assert True')
        report['claims'][0]['evidence'] = ['config']
        self.write_report(report)
        self.validate()
        link.unlink()
        link.symlink_to(second)
        result = self.validate(expected=1)
        self.assertIn('input', result.stderr.lower())

    def test_unavailable_command_retains_blocked_attempt(self):
        report = self.complete_report()
        self.cli('capture', '--run', self.run_dir, '--id', 'unavailable', '--kind', 'outcome',
                 '--timeout', '3', '--', self.root / 'missing-program')
        receipt = json.loads((self.run_dir / 'evidence/unavailable/receipt.json').read_text())
        self.assertEqual(receipt['execution_state'], 'launch-error')
        self.assertIsNone(receipt['exit_code'])
        report['claims'][0].update(status='BLOCKED', evidence=['unavailable'],
                                   observed='Command unavailable', reason='Missing prerequisite')
        report['calibrations'] = []
        self.write_report(report)
        self.validate()
        report['claims'][0]['status'] = 'PASS'
        self.write_report(report)
        self.validate(expected=1)

    def test_post_run_identity_failure_retains_execution_result(self):
        self.initialize()
        self.cli('capture', '--run', self.run_dir, '--id', 'identity-loss', '--kind', 'command',
                 '--timeout', '3', '--', sys.executable, '-c',
                 'from pathlib import Path; Path(".git").rename(".git-moved")')
        receipt = json.loads((self.run_dir / 'evidence/identity-loss/receipt.json').read_text())
        self.assertEqual(receipt['exit_code'], 0)
        self.assertEqual(receipt['execution_state'], 'observation-error')
        self.assertIsNone(receipt['target_after'])

    def reviewed_report(self):
        report = self.complete_report()
        (self.run_dir / 'review.md').write_text('Independent synthetic review evidence.\n')
        report['review'] = {'status': 'complete', 'reviewer': 'synthetic-reviewer',
                            'evidence': ['review.md']}
        report['completion'] = {'status': 'complete', 'coverage_exceptions': []}
        return report

    def test_restoration_requires_separate_successful_outcome_capture(self):
        report = self.complete_report()
        calibration = report['calibrations'][0]
        for restored in (None, 'good', 'broken', 'missing'):
            with self.subTest(restored=restored):
                calibration['restored_good'] = restored
                self.write_report(report)
                self.validate(expected=1)
        self.capture('restoration-timeout', 'import time; time.sleep(2)', timeout='0.1')
        self.capture('restoration-command', 'assert True', kind='command')
        self.capture('restoration-failed', 'raise SystemExit(1)')
        for restored in ('restoration-timeout', 'restoration-command', 'restoration-failed'):
            calibration['restored_good'] = restored
            self.write_report(report)
            self.validate(expected=1)

    def test_restored_true_without_evidence_is_rejected(self):
        report = self.complete_report()
        del report['calibrations'][0]['restored_good']
        self.write_report(report)
        self.validate(expected=1)

    def test_retained_fixture_requires_explicit_approval_and_owned_disposition(self):
        report = self.reviewed_report()
        cleanup = {'status': 'retained-approved', 'detail': 'Synthetic fixture retained',
                   'fixture_ids': ['synthetic-record-1'], 'fixture_owner': 'local-audit-run',
                   'approval': 'Human approved retaining the owned synthetic fixture',
                   'approval_reference': 'approval.md', 'disposition': 'Retain until investigation ends',
                   'cleanup_instructions': 'Delete synthetic-record-1 after review'}
        report['claims'][0]['cleanup'] = cleanup
        self.write_report(report)
        self.validate('--require-completion')
        for key in ('approval', 'approval_reference', 'fixture_ids', 'fixture_owner',
                    'disposition', 'cleanup_instructions'):
            with self.subTest(missing=key):
                changed = copy.deepcopy(report)
                del changed['claims'][0]['cleanup'][key]
                self.write_report(changed)
                self.validate(expected=1)

    def test_completion_allows_product_failure_but_runtime_does_not(self):
        report = self.reviewed_report()
        report['claims'][0].update(status='FAIL', evidence=['broken'],
                                   observed='Stored record missing', reason='Outcome assertion failed')
        report['calibrations'] = []
        self.write_report(report)
        self.validate('--require-completion')
        self.validate('--require-runtime', expected=1)

    def test_completion_requires_review_and_completed_status(self):
        report = self.reviewed_report()
        self.write_report(report)
        self.validate('--require-completion')
        for status in ('partial', 'waiting'):
            report['completion']['status'] = status
            self.write_report(report)
            self.validate()
            self.validate('--require-completion', expected=1)
        report['completion']['status'] = 'complete'
        report['review']['status'] = 'pending'
        self.write_report(report)
        self.validate('--require-completion', expected=1)

    def test_completion_rejects_unresolved_required_claims_and_cleanup(self):
        report = self.reviewed_report()
        for status in ('BLOCKED', 'INCONCLUSIVE'):
            report['claims'][0]['status'] = status
            self.write_report(report)
            self.validate()
            self.validate('--require-completion', expected=1)
        report['claims'][0].update(status='FAIL', evidence=['broken'])
        report['claims'][0]['cleanup']['status'] = 'blocked'
        self.write_report(report)
        self.validate('--require-completion', expected=1)

    def test_completion_cannot_hide_unselected_critical_or_required_work(self):
        report = self.reviewed_report()
        for critical, required in ((True, False), (False, True)):
            report['workflows'].append({'id': 'export', 'selected': False,
                                        'critical': critical, 'required': required,
                                        'reason': 'Required user outcome'})
            self.write_report(report)
            self.validate()
            self.validate('--require-completion', expected=1)
            report['workflows'].pop()

    def test_completion_accepts_explicit_human_coverage_exception(self):
        report = self.reviewed_report()
        report['workflows'].append({'id': 'export', 'selected': False,
                                    'critical': True, 'reason': 'Required user outcome'})
        exception = {'workflow': 'export', 'reason': 'Fixture access unavailable',
                     'approval': 'Human accepts the diagnostic coverage exception',
                     'approval_reference': 'human-decision-17'}
        report['completion']['coverage_exceptions'] = [exception]
        self.write_report(report)
        self.validate('--require-completion')
        for key in ('reason', 'approval', 'approval_reference'):
            with self.subTest(missing=key):
                changed = copy.deepcopy(report)
                del changed['completion']['coverage_exceptions'][0][key]
                self.write_report(changed)
                self.validate('--require-completion', expected=1)
        report['completion']['coverage_exceptions'].append(copy.deepcopy(exception))
        self.write_report(report)
        self.validate('--require-completion', expected=1)

    def test_completion_exception_can_accept_selected_blocked_workflow(self):
        report = self.reviewed_report()
        report['workflows'].append({'id': 'export', 'selected': True,
                                    'critical': True, 'reason': 'Required user outcome'})
        claim = copy.deepcopy(report['claims'][0])
        claim.update(id='export-check', workflow='export', status='BLOCKED', evidence=[],
                     observed='Fixture unavailable', reason='Missing access')
        report['claims'].append(claim)
        report['completion']['coverage_exceptions'] = [
            {'workflow': 'export', 'reason': 'Fixture access unavailable',
             'approval': 'Human accepted the blocked diagnostic scope',
             'approval_reference': 'human-decision-18'}]
        self.write_report(report)
        self.validate('--require-completion')
        report['completion']['coverage_exceptions'] = []
        self.write_report(report)
        self.validate('--require-completion', expected=1)

    def test_completion_rejects_source_only_or_all_excepted_reports(self):
        report = self.reviewed_report()
        report['claims'][0].update(status='BLOCKED', evidence=[],
                                   observed='Source inspection only', reason='Execution unavailable')
        report['calibrations'] = []
        report['completion']['coverage_exceptions'] = [
            {'workflow': 'save', 'reason': 'Execution unavailable',
             'approval': 'Human accepts exception', 'approval_reference': 'human-decision-19'}]
        self.write_report(report)
        self.validate('--require-completion', expected=1)

    def test_completion_requires_outcome_execution_not_just_commands_or_timeouts(self):
        report = self.reviewed_report()
        self.capture('build', 'assert True', kind='command')
        self.capture('timeout', 'import time; time.sleep(2)', timeout='0.1')
        report['claims'][0]['status'] = 'FAIL'
        report['calibrations'] = []
        for evidence in ('build', 'timeout'):
            report['claims'][0]['evidence'] = [evidence]
            self.write_report(report)
            self.validate()
            self.validate('--require-completion', expected=1)

    def test_schema_one_without_optional_completion_still_validates(self):
        report = self.complete_report()
        del report['completion']
        manifest_path = self.run_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        del manifest['target_profile']
        manifest_path.write_text(json.dumps(manifest))
        for path in self.run_dir.glob('evidence/*/receipt.json'):
            receipt = json.loads(path.read_text())
            receipt['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            path.write_text(json.dumps(receipt))
        self.write_report(report)
        self.validate()
        self.validate('--require-completion', expected=1)

    def test_optional_target_profile_is_fingerprinted_without_interpreting_it(self):
        profile = self.root / 'target-profile.json'
        profile.write_text('{"target":"synthetic-local"}')
        self.cli('init', '--repo', self.repo, '--out', self.run_dir,
                 '--scope', 'verification', '--target-profile', profile)
        manifest = json.loads((self.run_dir / 'manifest.json').read_text())
        self.assertEqual(manifest['target_profile']['path'], str(profile.absolute()))
        self.assertEqual(manifest['target_profile']['sha256'],
                         hashlib.sha256(profile.read_bytes()).hexdigest())

    def test_changed_or_retargeted_profile_invalidates_report(self):
        report = self.complete_report()
        first, second, link = (self.root / name for name in ('one.json', 'two.json', 'profile.json'))
        first.write_text('{"target":"one"}')
        second.write_text('{"target":"two"}')
        link.symlink_to(first)
        manifest_path = self.run_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['target_profile'] = {'path': str(link), 'resolved_path': str(first.resolve()),
                                      'sha256': hashlib.sha256(first.read_bytes()).hexdigest()}
        manifest_path.write_text(json.dumps(manifest))
        for path in self.run_dir.glob('evidence/*/receipt.json'):
            receipt = json.loads(path.read_text())
            receipt['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            path.write_text(json.dumps(receipt))
        self.write_report(report)
        self.validate()
        first.write_text('{"target":"changed"}')
        self.assertIn('profile', self.validate(expected=1).stderr.lower())
        first.write_text('{"target":"one"}')
        link.unlink()
        link.symlink_to(second)
        self.assertIn('profile', self.validate(expected=1).stderr.lower())


if __name__ == '__main__':
    unittest.main()
