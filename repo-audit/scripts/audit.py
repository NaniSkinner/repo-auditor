#!/usr/bin/env python3
"""Capture bounded audit commands and validate evidence receipts, not business truth."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid


VERSION = '1.2.0'
SECTIONS = ('baseline', 'architecture', 'feature_map', 'environment_recipe',
            'verification_assessment', 'defects', 'limitations', 'completion')
PSTACK_RESOURCES = (
    'skills/poteto-mode/SKILL.md',
    'skills/poteto-mode/references/codex-agent-runtime.md',
    'skills/poteto-mode/references/poteto-agent-prompt.md',
    'skills/poteto-mode/playbooks/investigation.md',
    'skills/poteto-mode/playbooks/eval.md',
    'skills/how/SKILL.md', 'skills/why/SKILL.md', 'skills/swarm/SKILL.md',
    'skills/interrogate/SKILL.md', 'skills/principle-prove-it-works/SKILL.md',
    'skills/create-verification-skill/SKILL.md',
    'skills/maintain-verification-skill/SKILL.md')
SAFE_ENV = ('PATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR', 'TMP', 'TEMP',
            'SYSTEMROOT', 'WINDIR')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    value = json.loads(path.read_text())
    require(isinstance(value, dict), f'{path.name} must contain an object')
    return value


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, indent=2)
        stream.write('\n')


def identity(repo):
    def git(*args):
        return subprocess.run(['git', '-C', str(repo), *args], check=True,
                              capture_output=True, timeout=15).stdout.decode().strip()
    root = str(Path(git('rev-parse', '--show-toplevel')).resolve())
    require(root == str(repo.resolve()), 'Pass the repository root, not a subdirectory')
    return {'root': root, 'head': git('rev-parse', 'HEAD'),
            'dirty': bool(git('status', '--porcelain', '--untracked-files=normal'))}


def contained(root, relative, allow_empty=False):
    require(isinstance(relative, str) and bool(relative), 'Empty artifact reference')
    candidate = (root / relative).resolve()
    require(candidate.is_relative_to(root.resolve()), 'Artifact escapes run directory')
    require(candidate.is_file() and (allow_empty or candidate.stat().st_size > 0),
            f'Missing or empty artifact: {relative}')
    return candidate


def nonempty(record, keys):
    require(isinstance(record, dict), 'Expected an object')
    for key in keys:
        require(isinstance(record.get(key), str) and record[key].strip(),
                f'Missing text field: {key}')


def text_list(record, key):
    value = record.get(key)
    require(isinstance(value, list) and bool(value) and
            all(isinstance(item, str) and item.strip() for item in value),
            f'Missing nonempty list: {key}')


def initialize(args):
    repo, output = Path(args.repo).resolve(), Path(args.out).resolve()
    require(not output.is_relative_to(repo), 'Keep audit output outside the target repository')
    source = identity(repo)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest = {
        'schema_version': 1, 'tool_version': VERSION, 'audit_id': str(uuid.uuid4()),
        'created_at': datetime.now(timezone.utc).isoformat(), 'target': source,
        'scope': args.scope,
        'environment': dict.fromkeys(('label', 'build', 'actor', 'configuration', 'fixtures'),
                                    'unconfirmed'),
        'dependency_receipt': None,
        'target_profile': ({'path': str(Path(args.target_profile).absolute()),
                            'resolved_path': str(Path(args.target_profile).resolve()),
                            'sha256': digest(Path(args.target_profile))}
                           if args.target_profile else None),
    }
    write_json(output / 'manifest.json', manifest)
    write_json(output / 'report.json', {
        'schema_version': 1, 'audit_id': manifest['audit_id'],
        'sections': dict.fromkeys(SECTIONS, ''), 'workflows': [], 'claims': [],
        'calibrations': [], 'recommendation': 'needs-human',
        'completion': {'status': 'partial', 'coverage_exceptions': []},
        'review': {'status': 'pending', 'reviewer': '', 'evidence': []},
    })
    print(json.dumps({'initialized': str(output), 'audit_id': manifest['audit_id'],
                      'target': source, 'scope': args.scope}))


def test_count(output, parser):
    if parser == 'unittest':
        matches = re.findall(r'Ran (\d+) tests? in ', output)
        skipped = re.findall(r'skipped=(\d+)', output)
        return max(0, int(matches[-1]) - (int(skipped[-1]) if skipped else 0)) if matches else 0
    if parser == 'pytest':
        summaries = re.findall(r'(?m)^.*(?:\d+ passed|\d+ failed|no tests ran|\d+ skipped).*$'
                               , output)
        if not summaries:
            return 0
        return sum(int(value) for value in re.findall(r'(\d+) (?:passed|failed)', summaries[-1]))
    return None


def required_external_scripts(command, repo):
    scripts = set()
    for position, argument in enumerate(command):
        if argument.endswith(('.py', '.js', '.mjs', '.sh', '.rb')):
            if position == 0 and '/' not in argument:
                path = Path(shutil.which(argument) or repo / argument).resolve()
            else:
                path = (repo / argument).resolve()
            if not path.is_relative_to(repo):
                scripts.add(str(path))
    return scripts


def capture(args):
    run = Path(args.run).resolve()
    manifest_path = run / 'manifest.json'
    manifest = read_json(manifest_path)
    require(manifest['scope'] in ('verification', 'setup'),
            'Inspection scope does not authorize command execution through capture')
    require(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', args.id), 'Unsafe evidence ID')
    require(0 < args.timeout <= 3600, 'Timeout must be within 0 and 3600 seconds')
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    require(bool(command), 'No command supplied')
    require(args.kind != 'test' or args.parser != 'none', 'Tests need a supported count parser')
    repo = Path(manifest['target']['root'])
    before = identity(repo)
    require(before == manifest['target'], 'Source identity changed before capture')
    inputs = [{'path': str(Path(item).absolute()),
               'resolved_path': str(Path(item).resolve()), 'sha256': digest(Path(item))}
              for item in args.input]
    require(required_external_scripts(command, repo) <= {item['resolved_path'] for item in inputs},
            'External scenario scripts require an explicit --input fingerprint')
    folder = run / 'evidence' / args.id
    folder.mkdir(parents=True, mode=0o700, exist_ok=False)
    output = folder / 'output.txt'
    environment = {key: os.environ[key] for key in SAFE_ENV if key in os.environ}
    environment.update({'CI': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
    start = time.monotonic()
    timed_out = False
    execution_state, error_category, exit_code = 'completed', None, None
    with output.open('xb') as stream:
        os.chmod(output, 0o600)
        try:
            process = subprocess.Popen(command, cwd=repo, env=environment, stdin=subprocess.DEVNULL,
                                       stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        except OSError as error:
            execution_state, error_category = 'launch-error', type(error).__name__
        else:
            try:
                process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=10)
            exit_code = process.returncode
    try:
        after = identity(repo)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        after = None
        execution_state = 'observation-error'
        error_category = type(error).__name__
    # A shell-free child still has host filesystem access permitted by its real sandbox.
    receipt = {
        'schema_version': 1, 'audit_id': manifest['audit_id'], 'id': args.id,
        'tool_version': VERSION, 'inputs': inputs,
        'kind': args.kind, 'parser': args.parser,
        'manifest_sha256': digest(manifest_path), 'command': command,
        'cwd': str(repo), 'target_before': before, 'target_after': after,
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'duration_seconds': round(time.monotonic() - start, 4),
        'exit_code': exit_code, 'timed_out': timed_out,
        'execution_state': execution_state, 'error_category': error_category,
        'output': 'output.txt', 'output_sha256': digest(output),
        'executed_tests': test_count(output.read_text(errors='replace'), args.parser),
    }
    write_json(folder / 'receipt.json', receipt)
    print(json.dumps({'captured': args.id, 'exit_code': exit_code,
                      'execution_state': execution_state, 'error_category': error_category,
                      'timed_out': timed_out, 'executed_tests': receipt['executed_tests'],
                      'source_changed': before != after}))


def load_evidence(run, evidence_id, manifest):
    require(isinstance(evidence_id, str) and
            re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', evidence_id), 'Unsafe evidence ID')
    path = contained(run, f'evidence/{evidence_id}/receipt.json')
    receipt = read_json(path)
    require(receipt.get('id') == evidence_id and receipt.get('audit_id') == manifest['audit_id'],
            'Evidence belongs to another run')
    require(receipt.get('manifest_sha256') == digest(run / 'manifest.json'),
            'Manifest changed after evidence capture')
    state = receipt.get('execution_state', 'completed')
    require(state in ('completed', 'launch-error', 'observation-error'), 'Unknown execution state')
    require(receipt.get('target_before') == manifest['target'], 'Source changed before capture')
    if state == 'observation-error':
        require(receipt.get('target_after') is None and bool(receipt.get('error_category')),
                'Missing observation failure category')
    else:
        require(receipt.get('target_after') == manifest['target'], 'Source changed during capture')
    require(receipt.get('cwd') == manifest['target']['root'], 'Evidence cwd differs from target')
    require((type(receipt.get('exit_code')) is int or
             (state != 'completed' and receipt.get('exit_code') is None)) and
            type(receipt.get('timed_out')) is bool,
            'Malformed execution result')
    if state == 'launch-error':
        require(receipt.get('exit_code') is None and bool(receipt.get('error_category')),
                'Malformed launch failure')
    require(receipt.get('kind') in ('command', 'test', 'outcome'), 'Unknown evidence kind')
    require(receipt.get('parser') in ('none', 'pytest', 'unittest'), 'Unknown count parser')
    command, inputs = receipt.get('command'), receipt.get('inputs', [])
    require(isinstance(command, list) and bool(command) and
            all(isinstance(item, str) for item in command), 'Missing command identity')
    require(isinstance(inputs, list), 'Malformed input fingerprints')
    input_paths = set()
    for item in inputs:
        nonempty(item, ('path', 'sha256'))
        source = Path(item['path'])
        require(str(source.resolve()) == item.get('resolved_path', item['path']),
                'Evidence input target changed')
        require(source.is_file() and digest(source) == item['sha256'], 'Evidence input changed')
        input_paths.add(str(source.resolve()))
    require(required_external_scripts(command, Path(manifest['target']['root'])) <= input_paths,
            'External scenario input fingerprint is missing')
    artifact = contained(path.parent, receipt.get('output'), allow_empty=True)
    require(receipt.get('output_sha256') == digest(artifact), 'Evidence output changed')
    if receipt['kind'] == 'test' and state == 'completed':
        actual = test_count(artifact.read_text(errors='replace'), receipt['parser'])
        require(actual == receipt.get('executed_tests') and actual > 0,
                'No executed tests or count mismatch')
    return receipt


def validate(args):
    run = Path(args.run).resolve()
    manifest, report = read_json(run / 'manifest.json'), read_json(run / 'report.json')
    require(manifest.get('schema_version') == 1 and report.get('schema_version') == 1,
            'Unsupported schema version')
    require(report.get('audit_id') == manifest.get('audit_id'), 'Report belongs to another run')
    require(manifest.get('scope') in ('inspection', 'verification', 'setup'), 'Unknown scope')
    require(isinstance(manifest.get('target'), dict), 'Missing target identity')
    require(identity(Path(manifest['target']['root'])) == manifest['target'], 'Source is stale')
    profile = manifest.get('target_profile')
    if profile is not None:
        nonempty(profile, ('path', 'resolved_path', 'sha256'))
        path = Path(profile['path'])
        require(str(path.resolve()) == profile['resolved_path'], 'Target profile target changed')
        require(path.is_file() and digest(path) == profile['sha256'], 'Target profile changed')
    sections = report.get('sections')
    require(isinstance(sections, dict), 'Missing assessment sections')
    for key in SECTIONS:
        contained(run, sections.get(key))
    require(report.get('recommendation') in ('needs-human', 'do-not-ship', 'ship'),
            'Unknown recommendation')
    workflows = report.get('workflows')
    require(isinstance(workflows, list) and bool(workflows), 'No workflow inventory')
    workflow_ids, selected, required_workflows = set(), set(), set()
    for workflow in workflows:
        nonempty(workflow, ('id', 'reason'))
        require(workflow['id'] not in workflow_ids, 'Duplicate workflow ID')
        require(type(workflow.get('selected')) is bool and type(workflow.get('critical')) is bool,
                'Workflow selection and critical flags must be boolean')
        require(type(workflow.get('required', False)) is bool,
                'Workflow required flag must be boolean')
        workflow_ids.add(workflow['id'])
        if workflow['critical'] or workflow['selected'] or workflow.get('required', False):
            required_workflows.add(workflow['id'])
        if workflow['selected']:
            selected.add(workflow['id'])
    require(bool(selected), 'Select at least one assessed workflow')
    claims = report.get('claims')
    require(isinstance(claims, list) and bool(claims), 'No claims assessed')
    ids, covered, passed = set(), set(), set()
    for claim in claims:
        nonempty(claim, ('id', 'workflow', 'claim', 'scope', 'source_of_truth', 'procedure',
                         'expected', 'observed', 'status', 'reason', 'next_check'))
        require(claim['id'] not in ids, 'Duplicate claim ID')
        ids.add(claim['id'])
        require(claim['workflow'] in selected, 'Claim references an unselected workflow')
        covered.add(claim['workflow'])
        for key in ('prerequisites', 'false_pass_risks', 'invalidation'):
            text_list(claim, key)
        require(claim['status'] in ('PASS', 'FAIL', 'BLOCKED', 'INCONCLUSIVE'), 'Unknown claim status')
        cleanup = claim.get('cleanup')
        nonempty(cleanup, ('status', 'detail'))
        require(cleanup['status'] in ('complete', 'not-needed', 'blocked', 'retained-approved'),
                'Unknown cleanup state')
        if cleanup['status'] == 'retained-approved':
            nonempty(cleanup, ('approval', 'approval_reference', 'disposition',
                               'cleanup_instructions', 'fixture_owner'))
            text_list(cleanup, 'fixture_ids')
        require(isinstance(claim.get('evidence'), list), 'Evidence must be a list')
        receipts = [load_evidence(run, item, manifest) for item in claim['evidence']]
        if claim['status'] in ('PASS', 'FAIL'):
            require(receipts, 'Conclusive claim has no execution evidence')
            require(manifest['scope'] != 'inspection', 'Inspection cannot assert runtime PASS or FAIL')
            require(all(item.get('execution_state', 'completed') == 'completed' for item in receipts),
                    'Conclusive claim uses an unavailable or unobserved execution')
        if claim['status'] == 'PASS':
            require(not manifest['target']['dirty'], 'Runtime PASS requires a clean pinned source')
            environment = manifest.get('environment')
            nonempty(environment, ('label', 'build', 'actor', 'configuration', 'fixtures'))
            require('unconfirmed' not in environment.values(), 'Environment identity is unconfirmed')
            require(cleanup['status'] != 'blocked', 'PASS with blocked cleanup')
            require(all(item['exit_code'] == 0 and not item['timed_out'] for item in receipts),
                    'PASS uses unsuccessful execution')
            require(any(item['kind'] == 'outcome' for item in receipts),
                    'PASS needs an outcome check, not only unit tests or build commands')
            passed.add(claim['workflow'])
    require(covered == selected, 'Selected workflow lacks an assessment')
    calibrated = set()
    require(isinstance(report.get('calibrations'), list), 'Missing calibration list')
    for calibration in report['calibrations']:
        nonempty(calibration, ('workflow', 'good', 'broken', 'restored_good', 'fault',
                               'expected_failure', 'observed_failure'))
        require(calibration['workflow'] in selected, 'Calibration workflow is unknown')
        require(len({calibration[key] for key in ('good', 'broken', 'restored_good')}) == 3,
                'Calibration requires three distinct captured evidence IDs')
        good = load_evidence(run, calibration['good'], manifest)
        broken = load_evidence(run, calibration['broken'], manifest)
        restored = load_evidence(run, calibration['restored_good'], manifest)
        require(good.get('execution_state', 'completed') ==
                broken.get('execution_state', 'completed') ==
                restored.get('execution_state', 'completed') == 'completed',
                'Calibration requires observed executions')
        require(good['kind'] == broken['kind'] == restored['kind'] == 'outcome', 'Calibrate outcome checks')
        require(good['exit_code'] == 0 and not good['timed_out'], 'Known-good check failed')
        require(broken['exit_code'] != 0 and not broken['timed_out'],
                'Known-broken check did not produce a bounded failure')
        require(calibration.get('restored') is True, 'Calibration fixture was not restored')
        require(restored['exit_code'] == 0 and not restored['timed_out'],
                'Restored-good check failed')
        calibrated.add(calibration['workflow'])
    require(passed <= calibrated, 'PASS workflow lacks good, broken and restored-good calibration')
    review = report.get('review')
    require(isinstance(review, dict) and review.get('status') in ('pending', 'complete', 'blocked'),
            'Missing independent review status')
    if review['status'] == 'complete':
        nonempty(review, ('reviewer',))
        text_list(review, 'evidence')
        for item in review['evidence']:
            contained(run, item)
    if args.require_review:
        require(review['status'] == 'complete', 'Independent review is not complete')
    completion = report.get('completion')
    exceptions = {}
    if completion is not None:
        require(isinstance(completion, dict) and
                completion.get('status') in ('complete', 'partial', 'waiting'),
                'Unknown execution completion status')
        entries = completion.get('coverage_exceptions', [])
        require(isinstance(entries, list), 'Malformed coverage exceptions')
        for exception in entries:
            nonempty(exception, ('workflow', 'reason', 'approval', 'approval_reference'))
            workflow = exception['workflow']
            require(workflow in required_workflows, 'Coverage exception workflow is not required')
            require(workflow not in exceptions, 'Duplicate coverage exception')
            exceptions[workflow] = exception
    if args.require_completion:
        require(review['status'] == 'complete', 'Execution completion requires independent review')
        require(completion is not None and completion['status'] == 'complete',
                'Execution completion is not complete')
        require(manifest['scope'] != 'inspection', 'Inspection is not completed runtime diagnosis')
        nonempty(manifest.get('environment'), ('label', 'build', 'actor', 'configuration', 'fixtures'))
        require('unconfirmed' not in manifest['environment'].values(),
                'Environment identity is unconfirmed')
        executed_workflows = required_workflows - exceptions.keys()
        require(bool(executed_workflows & selected),
                'Completed diagnosis needs executed coverage beyond accepted exceptions')
        for workflow in executed_workflows:
            require(workflow in selected, 'Required workflow remains outside executed scope')
            for claim in (item for item in claims if item['workflow'] == workflow):
                require(claim['status'] in ('PASS', 'FAIL'),
                        'Required workflow has unresolved diagnostic claims')
                require(claim['cleanup']['status'] != 'blocked',
                        'Required workflow has unresolved cleanup')
                receipts = [load_evidence(run, item, manifest) for item in claim['evidence']]
                require(any(item['kind'] == 'outcome' for item in receipts) and
                        all(item.get('execution_state', 'completed') == 'completed' and
                            not item['timed_out'] for item in receipts),
                        'Completed diagnosis requires bounded observed outcome execution')
    all_pass = all(item['status'] == 'PASS' for item in claims)
    if args.require_runtime or report['recommendation'] == 'ship':
        require(all_pass, 'Required runtime coverage has unresolved claims')
        require(required_workflows <= selected,
                'Required or critical workflows remain outside verified scope')
        dependency = read_json(contained(run, manifest.get('dependency_receipt')))
        require(dependency.get('ready') is True, 'Required Pstack dependencies are missing')
        resources = dependency.get('resources')
        require(isinstance(resources, list) and bool(resources), 'Missing dependency resource inventory')
        require(all(isinstance(item, dict) for item in resources), 'Malformed dependency inventory')
        required_roles = set(PSTACK_RESOURCES) | {'evidence-first'}
        roles = [item.get('role') for item in resources]
        require(all(isinstance(role, str) for role in roles) and len(roles) == len(set(roles))
                and required_roles <= set(roles), 'Required dependency roles are missing or duplicated')
        for item in resources:
            nonempty(item, ('path', 'sha256'))
            path = Path(item['path'])
            require(path.is_file() and digest(path) == item['sha256'], 'Dependency evidence is stale')
    if report['recommendation'] == 'ship':
        require(review['status'] == 'complete', 'Ship recommendation lacks independent review')
    print(json.dumps({'result': 'RECEIPT_VALID', 'audit_id': manifest['audit_id'],
                      'claims': dict(Counter(item['status'] for item in claims)),
                      'independent_review': review['status'],
                      'execution_completion': completion['status'] if completion else 'unspecified',
                      'semantic_truth': 'requires outcome and independent evidence review',
                      'recommendation': report['recommendation']}))


def doctor(args):
    root = Path(args.pstack_root).expanduser().resolve()
    paths = [(relative, root / relative) for relative in PSTACK_RESOURCES]
    if args.evidence_first:
        paths.append(('evidence-first', Path(args.evidence_first).expanduser().resolve()))
    if args.verify_pr:
        paths.append(('verify-pr', Path(args.verify_pr).expanduser().resolve()))
    missing = [str(path) for role, path in paths if not path.is_file()]
    if not args.evidence_first:
        missing.append('evidence-first: supply --evidence-first for full workflow readiness')
    result = {'ready': not missing, 'tool_version': VERSION,
              'pstack_root': str(root), 'missing': missing,
              'resources': [{'role': role, 'path': str(path), 'sha256': digest(path)}
                            for role, path in paths if path.is_file()],
              'hook_inheritance': 'not-established-for-repo-auditor',
              'sandbox': 'inherited-from-parent-not-enforced-by-this-script'}
    if args.out:
        write_json(Path(args.out), result)
    print(json.dumps(result, indent=2))
    return 0 if result['ready'] else 1


def self_check(args):
    source = Path(__file__).resolve().parents[2]
    receipt = read_json(source / 'installation.json')
    require(Path(receipt['source']).resolve() == source, 'Installation source moved')
    contract = source / 'repo-audit/references/contract.md'
    require(digest(contract) == receipt.get('contract_sha256'), 'Canonical contract changed')
    profile = Path(receipt['profile'])
    require(digest(profile) == receipt.get('profile_sha256'), 'Generated profile changed')
    require(Path(receipt['skill']).resolve() == source / 'repo-audit', 'Skill target changed')
    print(json.dumps({'result': 'INSTALLATION_VALID', 'contract_sha256': digest(contract),
                      'runtime_discovery': 'requires-supported-runtime-evidence'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    init = commands.add_parser('init')
    init.add_argument('--repo', required=True)
    init.add_argument('--out', required=True)
    init.add_argument('--target-profile', help='Optional target profile file to fingerprint')
    init.add_argument('--scope', choices=('inspection', 'verification', 'setup'), default='inspection')
    init.set_defaults(handler=initialize)
    cap = commands.add_parser('capture')
    cap.add_argument('--run', required=True)
    cap.add_argument('--id', required=True)
    cap.add_argument('--kind', choices=('command', 'test', 'outcome'), required=True)
    cap.add_argument('--parser', choices=('none', 'pytest', 'unittest'), default='none')
    cap.add_argument('--timeout', type=float, required=True)
    cap.add_argument('--input', action='append', default=[], help='Approved scenario file to fingerprint')
    cap.add_argument('command', nargs=argparse.REMAINDER)
    cap.set_defaults(handler=capture)
    val = commands.add_parser('validate')
    val.add_argument('--run', required=True)
    val.add_argument('--require-review', action='store_true')
    val.add_argument('--require-runtime', action='store_true')
    val.add_argument('--require-completion', action='store_true',
                     help='Require completed diagnostic coverage and independent review')
    val.set_defaults(handler=validate)
    doc = commands.add_parser('doctor')
    doc.add_argument('--pstack-root', required=True)
    doc.add_argument('--evidence-first')
    doc.add_argument('--verify-pr')
    doc.add_argument('--out')
    doc.set_defaults(handler=doctor)
    check = commands.add_parser('self-check')
    check.set_defaults(handler=self_check)
    args = parser.parse_args()
    try:
        return args.handler(args) or 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'result': 'REJECTED', 'reason': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
