# Evidence format and command reference

The helper requires Python 3.9 or newer, Git, and a POSIX host for process-group timeout cleanup. It executes commands without a shell. It is a recorder and structural gate, not a sandbox, redactor, identity provider, or semantic judge. Tests and inspected project commands remain responsible for meaningful assertions.

For an installed package, run `python3 <skill-root>/scripts/audit.py self-check` before use. It rejects contract/profile drift and a moved skill target against the installation receipt. It does not prove runtime profile selection. Source drafts without an installation receipt must report that gap.

Use an output directory outside the target repository. Runtime PASS requires a clean pinned checkout. If the source is dirty, inspect it without declaring runtime PASS or create an authorized isolated snapshot. Keep synthetic runtime data outside the checkout. A dirty boolean is not a fingerprint of dirty contents.

## Initialize

```sh
python3 <skill-root>/scripts/audit.py init --repo <repository-root> --out <new-run-directory> --scope inspection
```

Use `verification` for an authorized bounded product run or `setup` when verification tooling changes are also authorized. These flags record scope. They do not grant authority or enforce filesystem permissions.

The run contains `manifest.json`, `report.json`, assessment documents, and `evidence/<id>/` directories. Complete the environment fields before capturing commands. Name the build or artifact identity, actor class, relevant configuration fingerprint without secrets, and fixture inventory. Treat these fields as claims requiring observation, not self-certifying strings. Do not edit the manifest after capture. Start a new run after a relevant identity or authority change.

Run dependency discovery into `dependencies.json` and set `manifest.dependency_receipt` to that relative path before capture. Include Evidence-First in the doctor invocation for the full workflow. Missing optional PR tools do not prevent a non-PR audit.

## Capture

```sh
python3 <skill-root>/scripts/audit.py capture --run <run> --id saved-record --kind outcome --timeout 30 -- <inspected-command> <arguments>
python3 <skill-root>/scripts/audit.py capture --run <run> --id unit-checks --kind test --parser pytest --timeout 120 -- python3 -m pytest <scoped-tests>
```

Each ID is new. Do not overwrite failed attempts. `command` captures setup or diagnostic execution. `test` requires the pytest or unittest count adapter. `outcome` must invoke an inspected scenario with literal expected observations and nonzero failure on violated criteria. The recorder cannot infer whether its label or assertions are honest.

Supply `--input <absolute-scenario-path>` for each approved external scenario or oracle file. External Python, JavaScript, shell, and Ruby script arguments require this fingerprint. Supply other loaded helpers and configuration files explicitly too. The gate checks current input hashes. It cannot discover every dynamically loaded dependency, so record that inventory during inspection. Never select secrets or excluded files as fingerprint inputs. Inline code remains in the captured argument array.

Declared inputs retain both the original absolute path and its resolved target. Retargeting a declared configuration symlink invalidates the evidence even when its previous target still exists. Hashes still do not provide an anti-forgery boundary against a writer with access to both evidence and receipts.

Child commands receive only a small environment allowlist. Provider credentials, HOME, and arbitrary application variables are not inherited. Approved credential wrappers can still retrieve credentials themselves. Inspect them and use the repository's rules. The child's real filesystem and network access depend on the host sandbox, not this filtering. Avoid credentials in arguments because command arrays are retained. Output files can contain sensitive data. Do not run excluded diagnostics or commands that dump secrets. Inspect minimum safe output rather than blindly loading logs into the model.

The recorder preserves exit code, timeout, before and after source identity, manifest hash, command, timing, output hash, and executed test count. CLI success means the attempt was recorded, not that the product passed. Read the receipt's `exit_code` and `timed_out` fields. Background child processes remain a project cleanup responsibility if their launcher exits before the timeout. Inspect commands that spawn daemons and stop owned processes explicitly.

Read `execution_state` as well. `launch-error` retains an unavailable-command attempt with no exit code. `observation-error` retains any execution result when the final source identity could not be observed. Error categories are content-free exception type names. These attempts can substantiate a BLOCKED or INCONCLUSIVE assessment, but cannot support a conclusive PASS or FAIL or calibration. Storage failures can still prevent durable receipt creation and must be reported from available tool evidence.

## Fill the assessment

`report.sections` contains paths to nonempty local artifacts for baseline, architecture, feature map, environment recipe, verification assessment, defects, limitations, and completion. Several sections can point to one well-structured report. The gate checks file presence, not prose quality. Record file and revision anchors for static observations there.

`workflows` is the discovered important-flow inventory. Every item needs a unique `id`, boolean `selected`, boolean `critical`, and selection or exclusion `reason`. Every selected workflow needs one or more claims. Inventory completeness requires human and independent review.

Every runtime matrix claim needs these fields:

| Field | Content |
| --- | --- |
| `id`, `workflow` | Unique claim ID and selected workflow ID. |
| `claim`, `scope`, `prerequisites` | User outcome, environment, actor, tenant, inputs, initial state, and dependencies. Prerequisites are a nonempty string list. |
| `source_of_truth` | Authoritative observer and why it proves the outcome. |
| `procedure`, `expected`, `observed` | Exact scenario, literal acceptance predicate, and actual observation. |
| `status`, `reason` | PASS, FAIL, BLOCKED, or INCONCLUSIVE, with its basis. |
| `evidence` | Capture IDs. Conclusive runtime claims require captured execution. Supplement with artifact references in the assessment. |
| `false_pass_risks` | Nonempty list covering the relevant deceptive successes and how they were ruled out. |
| `invalidation` | Nonempty list of changes that require fresh evidence. |
| `cleanup` | Object with `status` of complete, not-needed, retained-approved, or blocked, plus `detail` naming fixture state and recovery. |
| `next_check` | Smallest next check or condition for refreshing a completed check. |

PASS requires successful execution and an outcome check, confirmed environment fields, clean source, completed, unnecessary, or explicitly approved retained cleanup, and a good/broken/restored-good calibration for that workflow. Unit tests alone cannot satisfy it. FAIL requires an actual observed contradiction, not merely a command error. The reviewer checks this semantic distinction. BLOCKED and INCONCLUSIVE need honest reasons and next checks. An inspection-only audit uses those statuses for unexecuted runtime claims.

Each `calibrations` item contains `workflow`, `good` capture ID, `broken` capture ID, `restored_good` capture ID, `fault`, `expected_failure`, `observed_failure`, and boolean `restored`. The gate checks three distinct execution results and identity. The reviewer verifies equivalent oracle, intended failure cause, safe fault injection, restore, and subsequent good rerun. Record all three capture IDs in the calibration object.

`review` contains `status` pending, complete, or blocked, `reviewer`, and relative artifact paths in `evidence`. A completed review requires an actual fresh review and a nonempty report. Presence of a file cannot prove independence. The lead checks the supported task receipts and review findings.

`recommendation` is needs-human, do-not-ship, or ship. A ship recommendation needs every inventoried critical workflow selected, all assessed claims PASS, current dependencies, and completed independent review. It still does not prove broader release policy or authorize deployment.

## Validate and interpret

```sh
python3 <skill-root>/scripts/audit.py validate --run <run>
python3 <skill-root>/scripts/audit.py validate --run <run> --require-review --require-runtime
```

The first command accepts structurally valid honest assessments, including partial assessments with blocked claims or pending review. Its result is `RECEIPT_VALID`. The second requires completed independent review and resolved selected runtime coverage, including selected critical workflows and current dependency files. Nonzero means a receipt gate failed. Neither command claims semantic truth.

Hashes detect accidental changes to recorded outputs. A writer with access to both outputs and receipts can forge them. Keep recorder, contract, and acceptance graders outside candidate write access using actual runtime isolation. Append-only naming is a workflow property, not tamper-proof storage. Do not describe this helper as an anti-forgery security boundary.

## Contract/tool 1.2 additions

`init --target-profile <file>` fingerprints the logical absolute path, resolved target and file bytes in `manifest.target_profile`. Validation rejects changed/retargeted profiles. It does not interpret the file as authority or proof of readiness. Omitted profiles remain valid for generic/source-only cases.

Every new calibration record needs `good`, `broken`, and `restored_good`: three distinct captured outcome IDs. The good and restored-good checks must complete with exit 0; the broken check must complete with the expected behavioral failure and no timeout. `restored: true` remains a declaration but cannot replace the restored-good capture. Keep `fault`, `expected_failure` and `observed_failure`, and inspect the actual assertion/output independently. Earlier 1.1 calibration records lacking restored-good evidence need new captures; do not rewrite historical attempts as new proof.

Cleanup status `retained-approved` requires `detail`, `approval`, `approval_reference`, `fixture_owner`, nonempty `fixture_ids`, `disposition`, and `cleanup_instructions`. Approval references identify actual live user decisions or an applicable run strategy the user accepted. They are checked structurally; the reviewer must establish their authenticity. Unapproved retention uses blocked cleanup.

Use `report.completion` with `status` complete/partial/waiting and `coverage_exceptions` (default empty). Each accepted exception has a known required `workflow`, `reason`, `approval` and `approval_reference`. Workflow `required` is optional; selected or critical workflows are always required. Basic validation still accepts explicitly partial reports, including schema-1 reports without a completion record.

`validate --require-completion --require-review` is the comprehensive diagnostic completion gate. It requires independent review, confirmed environment, at least one executed outcome beyond exceptions, and conclusive bounded outcome captures for each required workflow. Product FAIL can close an executed diagnostic check. Required unselected, BLOCKED/INCONCLUSIVE or unresolved cleanup needs an explicit human-accepted exception; moving work to a rollout cannot satisfy this gate. File existence, approval strings and hashes do not prove semantic coverage, actual authorization or truth. The independent reviewer must compare the ledger to the original requested outcome and discovered important domains.

`--require-runtime` separately requires all selected claims PASS, required workflow selection, calibration and dependency freshness. Neither flag starts work, grants authority, repairs products, establishes hostile-writer isolation or certifies every possible repository behavior.
